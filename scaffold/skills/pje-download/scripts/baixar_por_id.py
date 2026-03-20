#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baixa documentos individuais do PJE por ID.

Usa a mesma abordagem do baixar_por_tipo.py - POST com formulário JSF
especificando o intervalo de IDs (idDe=idAte para documento único).

Uso:
    # Baixar lista de IDs de um arquivo JSON
    python baixar_por_id.py --cookies pje_session.json --id-processo 2683123 --ids-file selecao.json --output-dir ./docs/

    # Baixar IDs específicos
    python baixar_por_id.py --cookies pje_session.json --id-processo 2683123 --ids 100813527,127729955,124323840 --output-dir ./docs/

Saída:
    PDFs individuais nomeados por ID e descrição.
"""

import json
import argparse
import requests
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("[ERRO] BeautifulSoup não instalado. Execute: pip install beautifulsoup4")
    sys.exit(1)


# Configurações
BASE_URL = "https://pje1g.trf5.jus.br"
TIMEOUT = 180  # 3 minutos para downloads grandes


def carregar_cookies(cookies_path: str) -> dict:
    """Carrega cookies do arquivo JSON."""
    with open(cookies_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def criar_sessao(dados_auth: dict) -> requests.Session:
    """Cria sessão requests com cookies."""
    session = requests.Session()

    cookie_str = dados_auth.get('cookie_download', '')
    if not cookie_str:
        cookie_str = dados_auth.get('headers', {}).get('Cookie', '')
    if not cookie_str:
        cookie_str = dados_auth.get('headers', {}).get('X-pje-cookies', '')
    if not cookie_str:
        cookies_dict = dados_auth.get('cookies', {})
        if cookies_dict:
            cookie_str = '; '.join(f'{k}={v}' for k, v in cookies_dict.items())

    if not cookie_str:
        print("[ERRO] Nenhum cookie encontrado")
        sys.exit(1)

    session.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Origin': BASE_URL,
        'Connection': 'keep-alive',
        'Cookie': cookie_str,
    })

    return session


def obter_codigo_acesso(session: requests.Session, id_processo: int, dados_auth: dict) -> str:
    """Obtém código de acesso para o processo."""
    url = f"{BASE_URL}/pje/seam/resource/rest/pje-legacy/painelUsuario/gerarChaveAcessoProcesso/{id_processo}"

    try:
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://frontend-prd.trf5.jus.br',
            'Referer': 'https://frontend-prd.trf5.jus.br/'
        }

        auth_headers = dados_auth.get('headers_api', dados_auth.get('headers', {}))
        for key in ['X-pje-legacy-app', 'X-pje-cookies', 'X-pje-usuario-localizacao']:
            if key in auth_headers:
                headers[key] = auth_headers[key]

        response = session.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            try:
                dados = response.json()
                if isinstance(dados, str):
                    return dados
                return dados.get('ca', '')
            except:
                return response.text.strip('"')
    except Exception:
        pass

    return ''


def extrair_view_state(html: str) -> str:
    """Extrai ViewState do formulário JSF."""
    soup = BeautifulSoup(html, 'html.parser')

    vs_input = soup.find('input', {'name': 'javax.faces.ViewState'})
    if vs_input:
        return vs_input.get('value', '')

    match = re.search(r'javax\.faces\.ViewState["\'][^>]*value=["\']([^"\']+)', html)
    if match:
        return match.group(1)

    return ''


def sanitizar_nome(texto: str, max_len: int = 50) -> str:
    """Sanitiza texto para uso em nome de arquivo."""
    texto = re.sub(r'[<>:"/\\|?*]', '', texto)
    texto = re.sub(r'[\s\-\.]+', '_', texto)
    texto = re.sub(r'_+', '_', texto)
    return texto[:max_len].strip('_')


def baixar_documento_por_id(session: requests.Session, id_processo: int,
                            id_documento: str, codigo_acesso: str,
                            id_tarefa: int, output_path: Path,
                            view_state: str = None, url_autos: str = None) -> dict:
    """
    Baixa um documento individual usando filtro de intervalo de IDs.

    Retorna: {'sucesso': bool, 'motivo': str, 'tamanho_kb': float, 'arquivo': str, 'view_state': str}
    """
    resultado = {'sucesso': False, 'motivo': '', 'tamanho_kb': 0, 'arquivo': '', 'view_state': view_state}

    url_base = f"{BASE_URL}/pje/Processo/ConsultaProcesso/Detalhe/listAutosDigitais.seam"

    # Construir URL se não fornecida
    if not url_autos:
        params = {'idProcesso': id_processo}
        if codigo_acesso:
            params['ca'] = codigo_acesso
        if id_tarefa:
            params['idTaskInstance'] = id_tarefa
        url_autos = f"{url_base}?{urlencode(params)}"

    try:
        # Obter ViewState se não fornecido
        if not view_state:
            response = session.get(url_autos, timeout=60)
            response.raise_for_status()

            view_state = extrair_view_state(response.text)
            if not view_state:
                resultado['motivo'] = 'viewstate_nao_encontrado'
                return resultado

        resultado['view_state'] = view_state

        # POST com filtro de intervalo de IDs (idDe=idAte para documento único)
        data = {
            'navbar:inativacaoLembreteMsgsOpenedState': '',
            'navbar:cbTipoDocumento': '0',
            'navbar:idDe': id_documento,
            'navbar:idAte': id_documento,
            'navbar:dtInicioInputDate': '',
            'navbar:dtInicioInputCurrentDate': datetime.now().strftime('%m/%Y'),
            'navbar:dtFimInputDate': '',
            'navbar:dtFimInputCurrentDate': datetime.now().strftime('%m/%Y'),
            'navbar:cbCronologia': 'ASC',
            'navbar:downloadProcesso': 'Download',
            'navbar': 'navbar',
            'autoScroll': '',
            'javax.faces.ViewState': view_state
        }

        session.headers['Referer'] = url_autos
        response = session.post(url_base, data=data, timeout=TIMEOUT, stream=True)

        content_type = response.headers.get('Content-Type', '')

        # Verificar se é PDF
        if 'application/pdf' in content_type or response.content[:4] == b'%PDF':
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            size_kb = output_path.stat().st_size / 1024

            if size_kb < 1:
                output_path.unlink()
                resultado['motivo'] = 'arquivo_muito_pequeno'
                return resultado

            resultado['sucesso'] = True
            resultado['tamanho_kb'] = size_kb
            resultado['arquivo'] = str(output_path)
            return resultado

        # Se não é PDF, pode ser HTML de erro
        elif 'text/html' in content_type:
            html = response.text

            new_view_state = extrair_view_state(html)
            if new_view_state:
                resultado['view_state'] = new_view_state

            if 'login' in html.lower() and 'senha' in html.lower():
                resultado['motivo'] = 'sessao_expirada'
            elif 'permissão' in html.lower() or 'permission' in html.lower():
                resultado['motivo'] = 'sem_permissao'
            elif 'não encontrado' in html.lower() or 'not found' in html.lower():
                resultado['motivo'] = 'documento_nao_encontrado'
            elif 'não há documentos' in html.lower() or 'nenhum documento' in html.lower():
                resultado['motivo'] = 'id_nao_existe'
            else:
                resultado['motivo'] = 'resposta_html_inesperada'

            return resultado

        else:
            resultado['motivo'] = f'content_type_inesperado'
            return resultado

    except requests.exceptions.Timeout:
        resultado['motivo'] = 'timeout'
        return resultado
    except Exception as e:
        resultado['motivo'] = f'erro: {str(e)[:30]}'
        return resultado


def main():
    parser = argparse.ArgumentParser(
        description='Baixa documentos individuais do PJE por ID'
    )
    parser.add_argument(
        '--cookies', '-c',
        required=True,
        help='Arquivo JSON com cookies de autenticação'
    )
    parser.add_argument(
        '--id-processo', '-p',
        type=int,
        required=True,
        help='ID interno do processo no PJE'
    )
    parser.add_argument(
        '--id-tarefa', '-t',
        type=int,
        default=None,
        help='ID da tarefa (opcional)'
    )
    parser.add_argument(
        '--ids-file', '-f',
        default=None,
        help='Arquivo JSON com lista de documentos selecionados'
    )
    parser.add_argument(
        '--ids', '-i',
        default=None,
        help='Lista de IDs separados por vírgula'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default='./documentos',
        help='Diretório de saída (padrão: ./documentos)'
    )
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=1.5,
        help='Delay entre downloads em segundos (padrão: 1.5)'
    )
    parser.add_argument(
        '--limite', '-l',
        type=int,
        default=None,
        help='Limite de documentos a baixar (para testes)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostra output detalhado (padrao: output minimo)'
    )

    args = parser.parse_args()

    # Determinar lista de documentos a baixar
    documentos = []

    if args.ids_file:
        with open(args.ids_file, 'r', encoding='utf-8') as f:
            selecao = json.load(f)

        if 'documentos_selecionados' in selecao:
            documentos = selecao['documentos_selecionados']
        elif 'documentos' in selecao:
            documentos = selecao['documentos']
        else:
            documentos = selecao

    elif args.ids:
        ids_lista = [id.strip() for id in args.ids.split(',')]
        documentos = [{'id': id, 'descricao': ''} for id in ids_lista]

    else:
        print("[ERRO] Especifique --ids-file ou --ids")
        return 1

    if not documentos:
        print("[ERRO] Nenhum documento para baixar")
        return 1

    if args.limite:
        documentos = documentos[:args.limite]

    verbose = args.verbose
    dados_auth = carregar_cookies(args.cookies)
    session = criar_sessao(dados_auth)

    # Obter código de acesso (silencioso)
    codigo_acesso = obter_codigo_acesso(session, args.id_processo, dados_auth)

    # Preparar diretório de saída
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Cabecalho compacto
    print(f"[INICIO] {len(documentos)} docs -> {output_dir}")

    resultados = []
    sucesso = 0
    falha = 0
    total_kb = 0
    view_state = None

    # Construir URL base
    url_base = f"{BASE_URL}/pje/Processo/ConsultaProcesso/Detalhe/listAutosDigitais.seam"
    params = {'idProcesso': args.id_processo}
    if codigo_acesso:
        params['ca'] = codigo_acesso
    if args.id_tarefa:
        params['idTaskInstance'] = args.id_tarefa
    url_autos = f"{url_base}?{urlencode(params)}"

    for i, doc in enumerate(documentos, 1):
        doc_id = doc.get('id', doc) if isinstance(doc, dict) else str(doc)
        descricao = doc.get('descricao', '') if isinstance(doc, dict) else ''
        tipo = doc.get('tipo', '') if isinstance(doc, dict) else ''

        # Criar nome do arquivo
        nome_base = sanitizar_nome(descricao) if descricao else ''
        tipo_base = sanitizar_nome(tipo) if tipo else ''

        if nome_base:
            nome_arquivo = f"{doc_id}_{tipo_base}_{nome_base}.pdf"
        elif tipo_base:
            nome_arquivo = f"{doc_id}_{tipo_base}.pdf"
        else:
            nome_arquivo = f"{doc_id}.pdf"

        output_path = output_dir / nome_arquivo

        resultado = baixar_documento_por_id(
            session, args.id_processo, doc_id, codigo_acesso,
            args.id_tarefa, output_path, view_state, url_autos
        )

        # Atualizar ViewState para próximo download
        if resultado.get('view_state'):
            view_state = resultado['view_state']

        if resultado['sucesso']:
            sucesso += 1
            total_kb += resultado['tamanho_kb']
            # Output compacto: uma linha por documento
            print(f"[OK] {doc_id}: {resultado['tamanho_kb']:.0f}KB")
        else:
            falha += 1
            print(f"[ERRO] {doc_id}: {resultado['motivo']}")

        resultados.append({
            'id': doc_id,
            'tipo': tipo,
            'descricao': descricao,
            'sucesso': resultado['sucesso'],
            'motivo': resultado['motivo'],
            'tamanho_kb': resultado['tamanho_kb'],
            'arquivo': resultado['arquivo']
        })

        # Delay entre downloads
        if i < len(documentos):
            time.sleep(args.delay)

    # Resumo compacto
    print(f"[FIM] {sucesso}/{len(documentos)} OK, {total_kb/1024:.2f}MB total")

    # Salvar log (detalhes ficam aqui)
    log_path = output_dir / '_download_por_id_log.json'
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump({
            'data': datetime.now().isoformat(),
            'id_processo': args.id_processo,
            'documentos_solicitados': len(documentos),
            'sucesso': sucesso,
            'falha': falha,
            'total_kb': total_kb,
            'resultados': resultados
        }, f, indent=2, ensure_ascii=False)

    return 0 if falha == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
