#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrai índice COMPLETO de documentos de um processo do PJE.

Acessa a página listDocConsultProcess.seam que contém todos os documentos
em uma única tabela, com ID, Tipo, Descrição, Data e Tamanho.

Este índice é a base para a análise semântica feita pelo agent seletor-documentos.

Uso:
    python extrair_indice_completo.py --cookies pje_session.json --id-processo 2683123 --output indice.json

Saída:
    JSON com lista completa de documentos para análise pelo LLM.
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
TIMEOUT = 120


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


def acessar_autos_digitais(session: requests.Session, id_processo: int,
                           codigo_acesso: str, id_tarefa: int = None) -> str:
    """Acessa página de autos digitais para obter CID válido."""
    url_base = f"{BASE_URL}/pje/Processo/ConsultaProcesso/Detalhe/listAutosDigitais.seam"

    params = {'idProcesso': id_processo}
    if codigo_acesso:
        params['ca'] = codigo_acesso
    if id_tarefa:
        params['idTaskInstance'] = id_tarefa

    url = f"{url_base}?{urlencode(params)}"

    print(f"  [INFO] Acessando autos digitais...")
    response = session.get(url, timeout=TIMEOUT)

    # Extrair CID da URL ou do HTML
    cid_match = re.search(r'cid=(\d+)', response.url)
    if cid_match:
        return cid_match.group(1)

    # Tentar extrair do HTML
    cid_match = re.search(r'cid=(\d+)', response.text)
    if cid_match:
        return cid_match.group(1)

    return ''


def extrair_indice_completo(session: requests.Session, cid: str) -> dict:
    """
    Extrai índice completo da página listDocConsultProcess.

    Esta página contém TODOS os documentos em uma tabela única.
    """
    url = f"{BASE_URL}/pje/Processo/ConsultaProcesso/Detalhe/listDocConsultProcess.seam?cid={cid}"

    print(f"  [INFO] Acessando lista de documentos (cid={cid})...")
    response = session.get(url, timeout=TIMEOUT)
    response.raise_for_status()

    html = response.text

    # Verificar sessão
    if 'login' in html.lower() and 'senha' in html.lower():
        print("[ERRO] Sessão expirada - necessário reautenticar")
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # Extrair número do processo do título
    titulo = soup.find('title')
    numero_match = re.search(r'(\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4})',
                             titulo.text if titulo else '')
    numero_processo = numero_match.group(1) if numero_match else ''

    # Encontrar tabela de documentos
    tabela = soup.find('table')
    if not tabela:
        print("[ERRO] Tabela de documentos não encontrada")
        return None

    documentos = []
    linhas = tabela.find_all('tr')[1:]  # Pular cabeçalho

    for linha in linhas:
        colunas = linha.find_all('td')
        if len(colunas) >= 5:
            doc = {
                'id': colunas[0].get_text(strip=True),
                'tipo': colunas[1].get_text(strip=True),
                'descricao': colunas[2].get_text(strip=True),
                'juntado_por': colunas[3].get_text(strip=True) if len(colunas) > 3 else '',
                'data': colunas[4].get_text(strip=True) if len(colunas) > 4 else '',
                'tamanho': colunas[6].get_text(strip=True) if len(colunas) > 6 else ''
            }

            # Limpar e normalizar dados
            doc['id'] = re.sub(r'\D', '', doc['id'])  # Apenas dígitos
            if doc['id']:
                documentos.append(doc)

    # Extrair total de resultados
    total_match = re.search(r'(\d+)\s*resultados?\s*encontrados?', html, re.IGNORECASE)
    total = int(total_match.group(1)) if total_match else len(documentos)

    resultado = {
        'numero_processo': numero_processo,
        'total_documentos': total,
        'documentos_extraidos': len(documentos),
        'data_extracao': datetime.now().isoformat(),
        'fonte': 'listDocConsultProcess.seam',
        'documentos': documentos
    }

    return resultado


def main():
    parser = argparse.ArgumentParser(
        description='Extrai índice COMPLETO de documentos do PJE'
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
        default='indice_completo.json',
        help='Arquivo de saída (padrão: indice_completo.json)'
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

    # Primeiro acessa autos digitais para obter CID válido
    cid = acessar_autos_digitais(session, args.id_processo, codigo_acesso, args.id_tarefa)

    if not cid:
        print("[ERRO] Não foi possível obter CID da sessão")
        return 1

    print(f"[OK] CID obtido: {cid}")

    # Extrair índice completo
    resultado = extrair_indice_completo(session, cid)

    if resultado is None:
        print("[ERRO] Falha ao extrair índice")
        return 1

    # Salvar resultado
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print()
    print("=" * 60)
    print("[RESULTADO] Índice COMPLETO extraído")
    print(f"  Processo: {resultado['numero_processo']}")
    print(f"  Total de documentos: {resultado['total_documentos']}")
    print(f"  Documentos extraídos: {resultado['documentos_extraidos']}")
    print()

    # Mostrar amostra dos primeiros documentos
    print("  Primeiros 5 documentos:")
    for doc in resultado['documentos'][:5]:
        print(f"    - {doc['id']}: {doc['tipo'][:30]} | {doc['descricao'][:40]}...")

    print()
    print(f"  Arquivo salvo: {output_path}")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
