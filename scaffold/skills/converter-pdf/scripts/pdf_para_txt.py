#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Converte PDFs de processos judiciais para arquivos de texto.

METODO PADRAO: OCR (Tesseract)
Processos judiciais frequentemente contem documentos escaneados, portanto
OCR e o metodo padrao. Use --digital para extracao rapida sem OCR.

Dependencias:
    pip install pdfplumber pdf2image pytesseract
    + Tesseract OCR instalado no sistema (com idioma portugues)
    + Poppler (para pdf2image no Windows)
"""

import argparse
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional


# =============================================================================
# CONFIGURACAO DE CAMINHOS (adaptado para skill)
# =============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent

# Caminho do Poppler no Windows (baixar de https://github.com/oschwartz10612/poppler-windows/releases)
_default_poppler = Path.home() / "poppler" / "poppler-24.08.0" / "Library" / "bin"
if _default_poppler.exists():
    POPPLER_PATH = str(_default_poppler)
else:
    POPPLER_PATH = os.environ.get("POPPLER_PATH", None)

# Caminho do tessdata (verifica varios locais)
# Prioridade: 1) skill/tessdata, 2) ~/tessdata, 3) padrao do sistema
_tessdata_skill = SCRIPT_DIR / "tessdata"
_tessdata_home = Path.home() / "tessdata"

if _tessdata_skill.exists():
    TESSDATA_DIR = _tessdata_skill
elif _tessdata_home.exists():
    TESSDATA_DIR = _tessdata_home
else:
    TESSDATA_DIR = None  # Usa padrao do sistema


# =============================================================================
# PADROES DE POLUICAO DO PJE (para remocao)
# =============================================================================

PADROES_POLUICAO = [
    # Rodapes de assinatura eletronica do PJe (TRF1 a TRF5)
    r'Assinado eletronicamente por:.*?(?:Num\.|Pág\.).*?(?:\d+|\n)',
    r'Assinado eletronicamente por:[^\n]*\n',

    # URLs do PJe
    r'https?://pje\d?g?\.trf\d\.jus\.br/[^\s\n]*',
    r'https?://[^\s]*ConsultaDocumento[^\s\n]*',

    # Numero do documento PJe
    r'Numero do documento:\s*\d+',
    r'Número do documento:\s*\d+',

    # Rodapes de tribunais superiores
    r'Documento:\s*\d+\s*-\s*Inteiro Teor[^\n]*',
    r'Site certificado[^\n]*',
    r'DJ:\s*\d{2}/\d{2}/\d{4}\s*Página\s*\d+\s*de\s*\d+',

    # Codigo de validacao
    r'Codigo de validacao:\s*[A-Za-z0-9]+',
    r'Código de validação:\s*[A-Za-z0-9]+',

    # Marcadores de pagina do PDF (rodape)
    r'Pag\.\s*\d+\s*de\s*\d+',
    r'Página\s*\d+\s*de\s*\d+',
    r'- Pág\.\s*\d+',

    # Carimbos de certificacao digital
    r'Este documento foi assinado digitalmente[^\n]*',
    r'Documento assinado digitalmente[^\n]*',
    r'Para verificar.*?acesse[^\n]*',

    # Linhas so com numeros de documento/pagina
    r'^Num\.\s*\d+\s*$',

    # Data/hora de geracao do documento
    r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s+Num\.\s*\d+',
]

# Padroes de cabecalhos/rodapes de escritorios (repetitivos)
PADROES_ESCRITORIOS = [
    # Telefones e emails repetidos
    r'(?:Fone|Tel|Telefone)s?:?\s*\(?\d{2}\)?\s*\d{4,5}[-.]\d{4}[^\n]*',
    r'e-?mail:\s*[^\s@]+@[^\s@]+\.[^\s\n]+',

    # Enderecos de escritorios (quando repetem muito)
    r'(?:Av\.|Avenida|Rua|R\.)[^,\n]+,\s*n[°o]?\s*\d+[^\n]*CEP[^\n]*',

    # Filiais repetidas
    r'Filiais?:[^\n]+',
]


def remover_poluicao_pje(texto: str) -> Tuple[str, int]:
    """
    Remove poluicao especifica do PJe (rodapes, URLs, metadados repetitivos).

    Args:
        texto: Texto bruto extraido do PDF

    Returns:
        Tupla (texto_limpo, quantidade_removida)
    """
    tamanho_original = len(texto)

    # Aplicar todos os padroes de poluicao
    for padrao in PADROES_POLUICAO:
        texto = re.sub(padrao, '', texto, flags=re.MULTILINE | re.IGNORECASE)

    # Remover linhas que sao apenas separadores ou espacos
    texto = re.sub(r'^[\s\-_=]{10,}$', '', texto, flags=re.MULTILINE)

    # Remover linhas vazias consecutivas (mais de 2)
    texto = re.sub(r'\n{4,}', '\n\n\n', texto)

    quantidade_removida = tamanho_original - len(texto)
    return texto, quantidade_removida


def remover_cabecalhos_repetitivos(texto: str) -> str:
    """
    Remove cabecalhos/rodapes de escritorios que se repetem em cada pagina.
    So remove se aparecer muitas vezes (indicando repeticao em paginas).

    Args:
        texto: Texto do processo

    Returns:
        Texto sem cabecalhos repetitivos
    """
    linhas = texto.split('\n')

    # Contar frequencia de cada linha (normalizada)
    frequencia = {}
    for linha in linhas:
        linha_norm = linha.strip().lower()
        if len(linha_norm) > 20:  # Ignorar linhas muito curtas
            frequencia[linha_norm] = frequencia.get(linha_norm, 0) + 1

    # Identificar linhas que aparecem muitas vezes (provavelmente cabecalhos)
    num_paginas = texto.count('[PAGINA ')
    limite_repeticao = max(5, num_paginas * 0.3)  # 30% das paginas ou minimo 5

    linhas_repetitivas = {
        linha for linha, count in frequencia.items()
        if count >= limite_repeticao
    }

    # Filtrar linhas repetitivas (exceto marcadores de pagina)
    linhas_filtradas = []
    for linha in linhas:
        linha_norm = linha.strip().lower()
        if linha_norm in linhas_repetitivas and '[pagina' not in linha_norm:
            continue
        linhas_filtradas.append(linha)

    return '\n'.join(linhas_filtradas)


def detectar_paginas_vazias(texto: str) -> str:
    """
    Remove ou marca paginas que tem pouco conteudo util.

    Args:
        texto: Texto com marcadores [PAGINA X]

    Returns:
        Texto com paginas vazias removidas
    """
    # Dividir por paginas
    partes = re.split(r'(={60}\n\[PAGINA \d+\]\n={60})', texto)

    resultado = []
    for i, parte in enumerate(partes):
        # Se for marcador de pagina, manter
        if re.match(r'={60}\n\[PAGINA \d+\]\n={60}', parte):
            resultado.append(parte)
        else:
            # Verificar se a pagina tem conteudo util
            texto_limpo = re.sub(r'\s+', '', parte)
            if len(texto_limpo) > 50:  # Mais de 50 caracteres uteis
                resultado.append(parte)
            # Se pagina muito vazia, pular (nao adicionar)

    return ''.join(resultado)


# =============================================================================
# EXTRACAO DE TEXTO
# =============================================================================

def extrair_texto_pdfplumber(pdf_path: str) -> Tuple[str, int]:
    """
    Extrai texto usando pdfplumber (melhor para PDFs com tabelas).

    Args:
        pdf_path: Caminho para o arquivo PDF

    Returns:
        Tupla (texto_extraido, num_paginas)
    """
    try:
        import pdfplumber

        texto_total = []
        num_paginas = 0

        with pdfplumber.open(pdf_path) as pdf:
            num_paginas = len(pdf.pages)
            for i, page in enumerate(pdf.pages, 1):
                texto = page.extract_text()
                if texto:
                    texto_total.append(f"\n{'='*60}\n[PAGINA {i}]\n{'='*60}\n")
                    texto_total.append(texto)

        return '\n'.join(texto_total), num_paginas

    except ImportError:
        raise ImportError("pdfplumber nao instalado. Instale com: pip install pdfplumber")
    except Exception as e:
        raise Exception(f"Erro pdfplumber: {e}")


def extrair_texto_pypdf2(pdf_path: str) -> Tuple[str, int]:
    """
    Extrai texto usando PyPDF2 (fallback).

    Args:
        pdf_path: Caminho para o arquivo PDF

    Returns:
        Tupla (texto_extraido, num_paginas)
    """
    try:
        from PyPDF2 import PdfReader

        texto_total = []
        reader = PdfReader(pdf_path)
        num_paginas = len(reader.pages)

        for i, page in enumerate(reader.pages, 1):
            texto = page.extract_text()
            if texto:
                texto_total.append(f"\n{'='*60}\n[PAGINA {i}]\n{'='*60}\n")
                texto_total.append(texto)

        return '\n'.join(texto_total), num_paginas

    except ImportError:
        raise ImportError("PyPDF2 nao instalado. Instale com: pip install PyPDF2")
    except Exception as e:
        raise Exception(f"Erro PyPDF2: {e}")


def extrair_texto_ocr(pdf_path: str, verbose: bool = False) -> Tuple[str, int]:
    """
    Extrai texto usando OCR (pytesseract + pdf2image).
    Usado para PDFs escaneados.

    Args:
        pdf_path: Caminho para o arquivo PDF
        verbose: Se True, mostra progresso detalhado (padrao: False)

    Returns:
        Tupla (texto_extraido, num_paginas)
    """
    try:
        from pdf2image import convert_from_path
        import pytesseract

        # Configurar caminho do Tesseract no Windows
        tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Usar tessdata customizado (se existir) com idioma portugues
        if TESSDATA_DIR is not None:
            os.environ['TESSDATA_PREFIX'] = str(TESSDATA_DIR)

        # Configurar caminho do Poppler no Windows
        if POPPLER_PATH and os.path.exists(POPPLER_PATH):
            os.environ['PATH'] = POPPLER_PATH + os.pathsep + os.environ.get('PATH', '')

        # Converter PDF para imagens
        # Usar DPI menor para processar mais rapido (150 e suficiente para texto)
        imagens = convert_from_path(pdf_path, dpi=150)
        num_paginas = len(imagens)

        texto_total = []
        # Calcular marcos de progresso (25%, 50%, 75%)
        marcos = {int(num_paginas * p): f"{int(p*100)}%" for p in [0.25, 0.5, 0.75]}

        for i, imagem in enumerate(imagens, 1):
            # Extrair texto com Tesseract (portugues)
            texto = pytesseract.image_to_string(imagem, lang='por')

            if texto and texto.strip():
                texto_total.append(f"\n{'='*60}\n[PAGINA {i}]\n{'='*60}\n")
                texto_total.append(texto)

            # Progresso apenas nos marcos (25%, 50%, 75%) e somente se verbose
            if verbose and i in marcos:
                print(f"    [OCR] {marcos[i]} concluido...")

        return '\n'.join(texto_total), num_paginas

    except ImportError as e:
        raise ImportError(
            f"Dependencias de OCR nao instaladas: {e}\n"
            "Instale com: pip install pdf2image pytesseract\n"
            "E instale o Tesseract OCR: https://github.com/tesseract-ocr/tesseract"
        )
    except Exception as e:
        raise Exception(f"Erro OCR: {e}")


def verificar_pdf_escaneado(texto: str, num_paginas: int) -> bool:
    """
    Verifica se o PDF provavelmente e escaneado (pouco texto extraido)
    ou possui fontes com encoding corrompido (cid:XXX).

    Args:
        texto: Texto extraido
        num_paginas: Numero de paginas do PDF

    Returns:
        True se provavelmente escaneado ou corrompido
    """
    if num_paginas == 0:
        return True

    # Remover marcadores de pagina para contar texto real
    texto_real = re.sub(r'={60}\n\[PAGINA \d+\]\n={60}', '', texto)
    texto_real = texto_real.strip()

    # Calcular caracteres por pagina
    chars_por_pagina = len(texto_real) / num_paginas if num_paginas > 0 else 0

    # PDFs digitais normalmente tem 1500-3000 chars por pagina
    # PDFs escaneados tem muito menos (ou zero)
    if chars_por_pagina < 200:
        return True

    # Verificar se ha texto corrompido com (cid:XXX) - fontes com encoding quebrado
    cid_count = len(re.findall(r'\(cid:\d+\)', texto_real))
    if cid_count > 50:
        return True

    # Verificar se texto parece corrompido/invertido
    palavras_teste = ['processo', 'autor', 'reu', 'juiz', 'sentenca', 'decisao', 'peticao', 'direito']
    texto_lower = texto_real[:50000].lower()

    palavras_encontradas = sum(1 for p in palavras_teste if p in texto_lower)

    # Se encontrar menos de 2 palavras comuns em 50k chars, provavelmente esta corrompido
    if chars_por_pagina > 200 and palavras_encontradas < 2:
        return True

    return False


# =============================================================================
# LIMPEZA DE TEXTO
# =============================================================================

def limpar_texto(texto: str) -> str:
    """
    Limpa e normaliza o texto extraido (limpeza basica).

    Args:
        texto: Texto bruto

    Returns:
        Texto limpo
    """
    # Remover multiplas linhas em branco
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    # Remover espacos multiplos
    texto = re.sub(r'[ \t]+', ' ', texto)

    # Remover espacos no inicio/fim das linhas
    linhas = [linha.strip() for linha in texto.split('\n')]
    texto = '\n'.join(linhas)

    # Remover caracteres de controle (exceto newline e tab)
    texto = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', texto)

    return texto


def extrair_metadados_texto(texto: str) -> dict:
    """
    Extrai metadados basicos do texto do processo.

    Args:
        texto: Texto do processo

    Returns:
        Dicionario com metadados extraidos
    """
    metadados = {}

    # Numero do processo (padrao CNJ)
    match = re.search(r'\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}', texto)
    if match:
        metadados['numero_cnj'] = match.group()

    # Classe processual
    match = re.search(r'Classe:\s*([^\n]+)', texto, re.IGNORECASE)
    if match:
        metadados['classe'] = match.group(1).strip()

    # Autor/Requerente
    match = re.search(r'(?:Autor|Requerente|Impetrante)(?:\(a\))?:\s*([^\n]+)', texto, re.IGNORECASE)
    if match:
        metadados['autor'] = match.group(1).strip()

    # Reu/Requerido
    match = re.search(r'(?:Reu|Réu|Requerido|Impetrado)(?:\(a\))?:\s*([^\n]+)', texto, re.IGNORECASE)
    if match:
        metadados['reu'] = match.group(1).strip()

    # Assunto
    match = re.search(r'Assunto:\s*([^\n]+)', texto, re.IGNORECASE)
    if match:
        metadados['assunto'] = match.group(1).strip()

    # Orgao julgador
    match = re.search(r'(?:Orgao|Órgão)\s*(?:Julgador)?:\s*([^\n]+)', texto, re.IGNORECASE)
    if match:
        metadados['orgao_julgador'] = match.group(1).strip()

    # Valor da causa
    match = re.search(r'Valor\s*(?:da\s*Causa)?:\s*R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    if match:
        metadados['valor_causa'] = match.group(1).strip()

    return metadados


# =============================================================================
# PROCESSAMENTO PRINCIPAL
# =============================================================================

def processar_pdf(pdf_path: Path, output_dir: Path, usar_ocr: bool = True, verbose: bool = False) -> dict:
    """
    Processa um PDF e salva o texto extraido.

    Args:
        pdf_path: Caminho do PDF
        output_dir: Diretorio de saida
        usar_ocr: Se True, usa OCR (padrao). Se False, usa extracao digital.
        verbose: Se True, mostra progresso detalhado (padrao: False)

    Returns:
        Dicionario com resultado do processamento
    """
    nome_base = pdf_path.stem
    output_path = output_dir / f"{nome_base}.txt"

    resultado = {
        'arquivo_origem': str(pdf_path),
        'arquivo_destino': str(output_path),
        'sucesso': False,
        'metodo': None,
        'paginas': 0,
        'caracteres_bruto': 0,
        'caracteres_limpo': 0,
        'poluicao_removida': 0,
        'usou_ocr': usar_ocr,
        'metadados': {},
        'erro': None
    }

    texto = None
    num_paginas = 0

    if usar_ocr:
        # PADRAO: OCR (melhor para processos judiciais com documentos escaneados)
        try:
            texto, num_paginas = extrair_texto_ocr(str(pdf_path), verbose=verbose)
            resultado['metodo'] = 'OCR (Tesseract)'
        except Exception as e:
            # Fallback silencioso para extracao digital
            try:
                texto, num_paginas = extrair_texto_pdfplumber(str(pdf_path))
                resultado['metodo'] = 'pdfplumber (fallback)'
                resultado['usou_ocr'] = False
            except Exception as e2:
                resultado['erro'] = f"OCR: {e}; pdfplumber: {e2}"
    else:
        # MODO DIGITAL: extracao rapida sem OCR (para PDFs digitais)
        try:
            texto, num_paginas = extrair_texto_pdfplumber(str(pdf_path))
            resultado['metodo'] = 'pdfplumber'
        except Exception as e:
            # Tentar OCR silenciosamente se extracao digital falhar
            try:
                texto, num_paginas = extrair_texto_ocr(str(pdf_path), verbose=verbose)
                resultado['metodo'] = 'OCR (fallback)'
                resultado['usou_ocr'] = True
            except Exception as e2:
                resultado['erro'] = f"pdfplumber: {e}; OCR: {e2}"

    resultado['paginas'] = num_paginas

    if not texto or len(texto.strip()) < 100:
        resultado['erro'] = "PDF sem texto extraivel (documento escaneado sem OCR disponivel)"
        return resultado

    resultado['caracteres_bruto'] = len(texto)

    # Limpeza basica
    texto = limpar_texto(texto)

    # Limpeza agressiva de poluicao do PJe
    texto, poluicao_removida = remover_poluicao_pje(texto)
    resultado['poluicao_removida'] = poluicao_removida

    # Remover cabecalhos repetitivos
    texto = remover_cabecalhos_repetitivos(texto)

    # Remover paginas vazias
    texto = detectar_paginas_vazias(texto)

    # Limpeza final
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    resultado['caracteres_limpo'] = len(texto)

    # Extrair metadados
    resultado['metadados'] = extrair_metadados_texto(texto)

    # Calcular reducao
    if resultado['caracteres_bruto'] > 0:
        reducao = (1 - resultado['caracteres_limpo'] / resultado['caracteres_bruto']) * 100
    else:
        reducao = 0

    # Adicionar cabecalho ao arquivo
    cabecalho = f"""# Texto Extraido de Processo Judicial
# Arquivo origem: {pdf_path.name}
# Data extracao: {datetime.now().isoformat()}
# Metodo: {resultado['metodo']}
# Paginas: {resultado['paginas']}
# Caracteres (bruto): {resultado['caracteres_bruto']}
# Caracteres (limpo): {resultado['caracteres_limpo']}
# Reducao: {reducao:.1f}%

"""

    # Salvar
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(cabecalho)
        f.write(texto)

    resultado['sucesso'] = True
    return resultado


def main():
    parser = argparse.ArgumentParser(
        description='Converte PDFs de processos judiciais para texto. PADRAO: OCR (Tesseract)'
    )
    parser.add_argument(
        '--input',
        required=True,
        help='Diretorio com PDFs ou arquivo PDF individual'
    )
    parser.add_argument(
        '--output',
        default='./textos',
        help='Diretorio de saida para arquivos TXT (padrao: ./textos)'
    )
    parser.add_argument(
        '--limite',
        type=int,
        default=0,
        help='Limitar quantidade de arquivos (0 = todos)'
    )
    parser.add_argument(
        '--digital',
        action='store_true',
        help='Usar extracao digital (pdfplumber) em vez de OCR. Mais rapido, mas falha em escaneados.'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostra progresso detalhado (padrao: output minimo)'
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    usar_ocr = not args.digital
    verbose = args.verbose

    # Listar PDFs
    if input_path.is_file():
        pdfs = [input_path]
    else:
        pdfs = sorted(input_path.glob('*.pdf'))

    if args.limite > 0:
        pdfs = pdfs[:args.limite]

    if not pdfs:
        print("[AVISO] Nenhum PDF encontrado")
        return

    # Cabecalho compacto
    metodo = 'digital' if not usar_ocr else 'OCR'
    print(f"[INICIO] {len(pdfs)} PDFs -> {output_dir} ({metodo})")

    sucesso = 0
    falha = 0
    total_bruto = 0
    total_limpo = 0
    resultados = []

    for i, pdf in enumerate(pdfs, 1):
        resultado = processar_pdf(pdf, output_dir, usar_ocr, verbose=verbose)
        resultados.append(resultado)

        if resultado['sucesso']:
            sucesso += 1
            total_bruto += resultado['caracteres_bruto']
            total_limpo += resultado['caracteres_limpo']

            reducao = 0
            if resultado['caracteres_bruto'] > 0:
                reducao = (1 - resultado['caracteres_limpo'] / resultado['caracteres_bruto']) * 100

            # Output compacto: uma linha por arquivo
            print(f"[OK] {pdf.name}: {resultado['paginas']}p, {resultado['caracteres_limpo']//1000}k chars, -{reducao:.0f}%")
        else:
            falha += 1
            print(f"[ERRO] {pdf.name}: {resultado['erro'][:50]}")

    # Resumo compacto
    if total_bruto > 0:
        reducao_total = (1 - total_limpo / total_bruto) * 100
        print(f"[FIM] {sucesso}/{len(pdfs)} OK, {total_limpo//1000}k chars total, -{reducao_total:.0f}%")
    else:
        print(f"[FIM] {sucesso}/{len(pdfs)} OK")

    # Salvar log (detalhes ficam aqui, nao no output)
    import json
    log_path = output_dir / 'conversao_log.json'
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump({
            'data': datetime.now().isoformat(),
            'sucesso': sucesso,
            'falha': falha,
            'caracteres_bruto': total_bruto,
            'caracteres_limpo': total_limpo,
            'resultados': resultados
        }, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    main()
