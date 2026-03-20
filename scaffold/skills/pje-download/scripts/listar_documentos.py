#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lista documentos de um processo do PJE com seus tipos e metadados.

Extrai o índice de documentos da página de autos digitais para permitir
análise e planejamento de download seletivo.

Uso:
    python listar_documentos.py --cookies pje_session.json --id-processo 2683123 --output indice.json

Saída:
    JSON com lista de documentos, tipos e estatísticas.
"""

import json
import argparse
import requests
import re
import sys
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
TIMEOUT = 60

# Mapeamento de tipos relevantes vs irrelevantes
TIPOS_RELEVANTES = {
    'NUCLEAR': [
        'Petição inicial', 'Decisão', 'Laudo de Perícia',
        'Embargos de Declaração', 'Alegações Finais', 'Sentença', 'Acórdão'
    ],
    'IMPORTANTE': [
        'Petição (outras)', 'Contrarrazões', 'Despacho',
        'Impugnação aos Embargos', 'Esclarecimento de Perito',
        'Manifestação (Outras)', 'Contestação', 'Réplica', 'Reconvenção',
        'Agravo', 'Apelação', 'Recurso'
    ]
}

TIPOS_IRRELEVANTES = [
    'Certidão', 'Certidão (Outras)', 'Certidão de Intimação',
    'Certidão de Juntada', 'Certidão de Retificação',
    'Certidão de Interposição de Recurso', 'Comunicação',
    'Expediente', 'Intimação', 'Ato Ordinatório',
    'Substabelecimento', 'Documento Comprobatório',
    'Documento de Comprovação', 'Petição de Habilitação',
    'Procuração', 'Guia de Custas'
]


def carregar_cookies(cookies_path: str) -> dict:
    """Carrega cookies do arquivo JSON."""
    with open(cookies_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def criar_sessao(dados_auth: dict) -> requests.Session:
    """Cria sessão requests com cookies."""
    session = requests.Session()

    # Obter string de cookies
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
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
    except Exception as e:
        print(f"[AVISO] Falha ao obter código de acesso: {e}")

    return ''


def extrair_documentos_timeline(html: str) -> list:
    """Extrai lista de documentos da timeline da página."""
    soup = BeautifulSoup(html, 'html.parser')
    documentos = []

    # Encontrar elementos de documento na timeline
    # Formato típico: "129401156 - Contrarrazões (Contrarrazões de Embargos de Declaração)"

    # Padrão 1: Links com ID numérico
    for link in soup.find_all('a'):
        text = link.get_text(strip=True)
        match = re.match(r'^(\d{6,})\s*-\s*(.+)$', text)
        if match:
            doc_id = match.group(1)
            tipo_completo = match.group(2)

            # Extrair tipo base (antes do parêntese)
            tipo_base = re.sub(r'\s*\([^)]*\)\s*$', '', tipo_completo).strip()

            documentos.append({
                'id': doc_id,
                'tipo': tipo_base,
                'tipo_completo': tipo_completo,
                'data': None  # Será preenchido se disponível
            })

    # Padrão 2: Spans com classe específica
    for span in soup.find_all('span', class_=re.compile(r'documento|doc')):
        text = span.get_text(strip=True)
        match = re.match(r'^(\d{6,})\s*-\s*(.+)$', text)
        if match:
            doc_id = match.group(1)
            tipo_completo = match.group(2)
            tipo_base = re.sub(r'\s*\([^)]*\)\s*$', '', tipo_completo).strip()

            # Evitar duplicados
            if not any(d['id'] == doc_id for d in documentos):
                documentos.append({
                    'id': doc_id,
                    'tipo': tipo_base,
                    'tipo_completo': tipo_completo,
                    'data': None
                })

    return documentos


def extrair_tipos_disponiveis(html: str) -> dict:
    """Extrai tipos de documento disponíveis no combobox de filtro."""
    soup = BeautifulSoup(html, 'html.parser')
    tipos = {}

    # Encontrar select de tipo de documento
    select = soup.find('select', id=re.compile(r'cbTipoDocumento|tipoDocumento'))
    if select:
        for option in select.find_all('option'):
            value = option.get('value', '')
            text = option.get_text(strip=True)
            if value and value != '0' and text != 'Selecione':
                tipos[text] = value

    return tipos


def classificar_tipo(tipo: str) -> str:
    """Classifica um tipo de documento como NUCLEAR, IMPORTANTE ou IRRELEVANTE."""
    tipo_lower = tipo.lower()

    for t in TIPOS_RELEVANTES['NUCLEAR']:
        if t.lower() in tipo_lower or tipo_lower in t.lower():
            return 'NUCLEAR'

    for t in TIPOS_RELEVANTES['IMPORTANTE']:
        if t.lower() in tipo_lower or tipo_lower in t.lower():
            return 'IMPORTANTE'

    for t in TIPOS_IRRELEVANTES:
        if t.lower() in tipo_lower or tipo_lower in t.lower():
            return 'IRRELEVANTE'

    return 'NAO_CLASSIFICADO'


def listar_documentos(session: requests.Session, id_processo: int,
                      codigo_acesso: str = None, id_tarefa: int = None) -> dict:
    """Lista documentos de um processo."""

    url_base = f"{BASE_URL}/pje/Processo/ConsultaProcesso/Detalhe/listAutosDigitais.seam"

    params = {'idProcesso': id_processo}
    if codigo_acesso:
        params['ca'] = codigo_acesso
    if id_tarefa:
        params['idTaskInstance'] = id_tarefa

    url = f"{url_base}?{urlencode(params)}"

    print(f"[INFO] Acessando página de autos digitais...")
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()

    html = response.text

    # Verificar se página carregou corretamente
    if 'login' in html.lower() and 'senha' in html.lower():
        print("[ERRO] Sessão expirada - necessário reautenticar")
        return None

    # Extrair número do processo
    numero_match = re.search(r'(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})', html)
    numero_processo = numero_match.group(1) if numero_match else f"id_{id_processo}"

    # Extrair total de documentos (ex: "859 de 860")
    total_match = re.search(r'(\d+)\s+de\s+(\d+)', html)
    total_documentos = int(total_match.group(2)) if total_match else 0

    # Extrair documentos da timeline
    documentos = extrair_documentos_timeline(html)

    # Extrair tipos disponíveis no filtro
    tipos_disponiveis = extrair_tipos_disponiveis(html)

    # Classificar documentos
    estatisticas = {
        'NUCLEAR': 0,
        'IMPORTANTE': 0,
        'IRRELEVANTE': 0,
        'NAO_CLASSIFICADO': 0
    }

    tipos_contagem = {}

    for doc in documentos:
        classificacao = classificar_tipo(doc['tipo'])
        doc['classificacao'] = classificacao
        estatisticas[classificacao] += 1

        tipo = doc['tipo']
        if tipo not in tipos_contagem:
            tipos_contagem[tipo] = {'quantidade': 0, 'classificacao': classificacao}
        tipos_contagem[tipo]['quantidade'] += 1

    resultado = {
        'numero_processo': numero_processo,
        'id_processo': id_processo,
        'total_documentos': total_documentos,
        'documentos_extraidos': len(documentos),
        'data_extracao': datetime.now().isoformat(),
        'estatisticas': estatisticas,
        'tipos_contagem': tipos_contagem,
        'tipos_pje_disponiveis': tipos_disponiveis,
        'documentos': documentos[:100] if len(documentos) > 100 else documentos,
        'nota': 'Lista limitada aos 100 primeiros documentos visíveis na timeline'
    }

    return resultado


def main():
    parser = argparse.ArgumentParser(
        description='Lista documentos de um processo do PJE'
    )
    parser.add_argument(
        '--cookies', '-c',
        required=True,
        help='Arquivo JSON com cookies de autenticação'
    )
    parser.add_argument(
        '--id-processo', '-i',
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
        '--output', '-o',
        default='indice_documentos.json',
        help='Arquivo de saída (padrão: indice_documentos.json)'
    )

    args = parser.parse_args()

    print(f"[INFO] Carregando cookies de {args.cookies}...")
    dados_auth = carregar_cookies(args.cookies)

    session = criar_sessao(dados_auth)

    print(f"[INFO] Obtendo código de acesso para processo {args.id_processo}...")
    codigo_acesso = obter_codigo_acesso(session, args.id_processo, dados_auth)

    if codigo_acesso:
        print(f"[OK] Código de acesso obtido")
    else:
        print(f"[AVISO] Sem código de acesso - tentando acesso direto")

    resultado = listar_documentos(session, args.id_processo, codigo_acesso, args.id_tarefa)

    if resultado is None:
        print("[ERRO] Falha ao listar documentos")
        return 1

    # Salvar resultado
    output_path = Path(args.output)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    print("[RESULTADO] Índice de documentos extraído")
    print(f"  Processo: {resultado['numero_processo']}")
    print(f"  Total de documentos: {resultado['total_documentos']}")
    print(f"  Documentos extraídos: {resultado['documentos_extraidos']}")
    print()
    print("  Classificação:")
    for cat, qtd in resultado['estatisticas'].items():
        pct = (qtd / resultado['documentos_extraidos'] * 100) if resultado['documentos_extraidos'] > 0 else 0
        print(f"    {cat}: {qtd} ({pct:.1f}%)")
    print()
    print(f"  Arquivo salvo: {output_path}")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
