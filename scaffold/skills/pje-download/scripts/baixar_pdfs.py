#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baixa PDFs dos autos digitais dos processos do PJE TRF5.

Uso:
    python baixar_pdfs.py --cookies cookies.json --processos processos.json --output ./output
"""

import json
import argparse
import requests
import time
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
TIMEOUT = 120  # segundos para download de PDF
MAX_SIZE_MB = 1024  # 1GB


def carregar_cookies(cookies_path: str) -> dict:
    """Carrega cookies do arquivo JSON."""
    with open(cookies_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def carregar_processos(processos_path: str) -> list:
    """Carrega lista de processos do arquivo JSON."""
    with open(processos_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)
        return dados.get('processos', dados if isinstance(dados, list) else [])


def criar_sessao(dados_auth: dict) -> requests.Session:
    """
    Cria sessão requests com cookies para download.

    IMPORTANTE: Usa cookie string completo para sessão JSF.
    """
    session = requests.Session()

    # Obter string de cookies completa
    cookie_str = ''

    # 1. Tentar cookie_download (formato extrair_cookies.py)
    cookie_str = dados_auth.get('cookie_download', '')

    # 2. Tentar Cookie header diretamente
    if not cookie_str:
        cookie_str = dados_auth.get('headers', {}).get('Cookie', '')

    # 3. Tentar X-pje-cookies
    if not cookie_str:
        cookie_str = dados_auth.get('headers', {}).get('X-pje-cookies', '')
        if not cookie_str:
            cookie_str = dados_auth.get('headers_api', {}).get('X-pje-cookies', '')

    # 4. Construir a partir do dict
    if not cookie_str:
        cookies_dict = dados_auth.get('cookies', {})
        if cookies_dict:
            cookie_str = '; '.join(f'{k}={v}' for k, v in cookies_dict.items())

    if not cookie_str:
        print("[ERRO] Nenhum cookie encontrado no arquivo")
        print("[DICA] Use extrair_cookies.py com --har-baixar para extrair cookies de download")
        sys.exit(1)

    # Guardar para uso posterior
    session._cookie_string = cookie_str

    # Headers que imitam o browser Firefox
    session.headers.update({
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Origin': 'https://pje1g.trf5.jus.br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Cookie': cookie_str,
    })

    # NOTA: NÃO enviar Authorization - a API do PJE usa apenas cookies!
    # Authorization header causa 401

    return session


def obter_codigo_acesso(session: requests.Session, id_processo: int, dados_auth: dict = None) -> str:
    """Obtém o código de acesso (ca) para um processo via API."""
    url = f"{BASE_URL}/pje/seam/resource/rest/pje-legacy/painelUsuario/gerarChaveAcessoProcesso/{id_processo}"

    try:
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'Origin': 'https://frontend-prd.trf5.jus.br',
            'Referer': 'https://frontend-prd.trf5.jus.br/'
        }

        if dados_auth:
            auth_headers = dados_auth.get('headers_api', dados_auth.get('headers', {}))
            # IMPORTANTE: NÃO enviar Authorization - causa 401!
            for key in ['X-pje-legacy-app', 'X-pje-cookies', 'X-pje-usuario-localizacao']:
                if key in auth_headers:
                    headers[key] = auth_headers[key]

        response = session.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            resp_text = response.text.strip()

            if resp_text.startswith('<!DOCTYPE') or resp_text.startswith('<html'):
                return ''

            try:
                dados = response.json()
                if isinstance(dados, str):
                    return dados
                elif isinstance(dados, dict):
                    return dados.get('ca', dados.get('chaveAcesso', ''))
            except:
                return resp_text.strip('"')

    except Exception:
        pass

    return ''


def extrair_view_state(html: str) -> str:
    """Extrai o ViewState do formulário JSF."""
    soup = BeautifulSoup(html, 'html.parser')

    vs_input = soup.find('input', {'name': 'javax.faces.ViewState'})
    if vs_input:
        return vs_input.get('value', '')

    match = re.search(r'javax\.faces\.ViewState["\'][^>]*value=["\']([^"\']+)', html)
    if match:
        return match.group(1)

    return ''


def baixar_pdf_processo(session: requests.Session, processo: dict, output_dir: Path,
                        ordem: str = 'ASC', dados_auth: dict = None) -> dict:
    """
    Baixa PDF completo dos autos digitais de um processo.

    Retorna: {'sucesso': bool, 'motivo': str, 'tamanho_mb': float, 'arquivo': str}
    """
    numero_cnj = processo.get('numero_cnj', 'desconhecido')
    numero_safe = re.sub(r'[^\d.-]', '', numero_cnj)
    id_processo = processo.get('id_processo')
    id_tarefa = processo.get('id_tarefa')

    resultado = {'sucesso': False, 'motivo': '', 'tamanho_mb': 0, 'arquivo': ''}

    # Criar pasta do processo
    pasta_processo = output_dir / numero_safe
    pasta_processo.mkdir(parents=True, exist_ok=True)

    # Obter código de acesso (silencioso)
    codigo_acesso = processo.get('codigo_acesso')
    if not codigo_acesso and id_processo:
        codigo_acesso = obter_codigo_acesso(session, id_processo, dados_auth)

    try:
        url_base = f"{BASE_URL}/pje/Processo/ConsultaProcesso/Detalhe/listAutosDigitais.seam"

        params = {'idProcesso': id_processo}
        if codigo_acesso:
            params['ca'] = codigo_acesso
        if id_tarefa:
            params['idTaskInstance'] = id_tarefa

        param_str = urlencode(params)
        url_autos = f"{url_base}?{param_str}"

        session.headers['Referer'] = 'https://pje1g.trf5.jus.br/pje/Painel/painel_usuario/Usuario.seam'

        response = session.get(url_autos, timeout=60)
        response.raise_for_status()

        view_state = extrair_view_state(response.text)
        if not view_state:
            resp_lower = response.text.lower()
            if 'login' in resp_lower:
                resultado['motivo'] = 'cookies_expirados'
            elif 'sessão expirada' in resp_lower or 'sessao expirada' in resp_lower:
                resultado['motivo'] = 'sessao_expirada'
            else:
                resultado['motivo'] = 'viewstate_nao_encontrado'
            return resultado

        # POST para download
        data = {
            'navbar:inativacaoLembreteMsgsOpenedState': '',
            'navbar:cbTipoDocumento': '0',
            'navbar:idDe': '',
            'navbar:idAte': '',
            'navbar:dtInicioInputDate': '',
            'navbar:dtInicioInputCurrentDate': datetime.now().strftime('%m/%Y'),
            'navbar:dtFimInputDate': '',
            'navbar:dtFimInputCurrentDate': datetime.now().strftime('%m/%Y'),
            'navbar:cbCronologia': ordem,
            'navbar:downloadProcesso': 'Download',
            'navbar': 'navbar',
            'autoScroll': '',
            'javax.faces.ViewState': view_state
        }

        session.headers['Referer'] = url_autos
        response = session.post(url_base, data=data, timeout=TIMEOUT, stream=True)

        content_type = response.headers.get('Content-Type', '')

        if 'application/pdf' in content_type or response.content[:4] == b'%PDF':
            output_path = pasta_processo / f"{numero_safe}.pdf"

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            size_mb = output_path.stat().st_size / (1024 * 1024)

            # Verificar tamanho máximo
            if size_mb > MAX_SIZE_MB:
                output_path.unlink()
                resultado['motivo'] = f'muito_grande_{size_mb:.0f}MB'
                resultado['tamanho_mb'] = size_mb
                return resultado

            resultado['sucesso'] = True
            resultado['tamanho_mb'] = size_mb
            resultado['arquivo'] = str(output_path)
            return resultado

        else:
            if 'text/html' in content_type:
                resp_lower = response.text.lower()
                if 'sessão expirada' in resp_lower or 'sessao expirada' in resp_lower:
                    resultado['motivo'] = 'sessao_expirada'
                elif 'login' in resp_lower:
                    resultado['motivo'] = 'requer_login'
                elif 'acesso negado' in resp_lower or 'não autorizado' in resp_lower:
                    resultado['motivo'] = 'acesso_negado'
                else:
                    resultado['motivo'] = 'resposta_html_inesperada'
            return resultado

    except requests.exceptions.Timeout:
        resultado['motivo'] = 'timeout'
        return resultado
    except requests.exceptions.RequestException as e:
        resultado['motivo'] = f'erro: {str(e)[:30]}'
        return resultado


def main():
    parser = argparse.ArgumentParser(
        description='Baixa PDFs dos autos digitais do PJE'
    )
    parser.add_argument(
        '--cookies', '-c',
        required=True,
        help='Arquivo JSON com cookies de autenticação'
    )
    parser.add_argument(
        '--processos', '-p',
        required=True,
        help='Arquivo JSON com lista de processos'
    )
    parser.add_argument(
        '--output', '-o',
        default='./output',
        help='Diretório de saída (padrão: ./output)'
    )
    parser.add_argument(
        '--ordem',
        choices=['crescente', 'decrescente'],
        default='crescente',
        help='Ordem dos documentos no PDF (padrão: crescente)'
    )
    parser.add_argument(
        '--limite', '-l',
        type=int,
        default=0,
        help='Limitar quantidade de downloads (0 = todos)'
    )
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=2.0,
        help='Delay entre downloads em segundos (padrão: 2.0)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostra output detalhado (padrao: output minimo)'
    )

    args = parser.parse_args()

    ordem_api = 'ASC' if args.ordem == 'crescente' else 'DESC'
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    verbose = args.verbose

    dados_auth = carregar_cookies(args.cookies)
    processos = carregar_processos(args.processos)

    if args.limite > 0:
        processos = processos[:args.limite]

    # Cabecalho compacto
    print(f"[INICIO] {len(processos)} processos -> {output_dir}")

    session = criar_sessao(dados_auth)

    sucesso = 0
    falha = 0
    dispensados = 0
    total_mb = 0
    resultados = []

    for i, processo in enumerate(processos, 1):
        numero = processo.get('numero_cnj', 'N/A')

        resultado = baixar_pdf_processo(session, processo, output_dir, ordem_api, dados_auth)

        if resultado['sucesso']:
            sucesso += 1
            total_mb += resultado['tamanho_mb']
            # Output compacto: uma linha por arquivo
            print(f"[OK] {numero}: {resultado['tamanho_mb']:.1f}MB")
        elif 'muito_grande' in resultado.get('motivo', ''):
            dispensados += 1
            if verbose:
                print(f"[SKIP] {numero}: {resultado['motivo']}")
        else:
            falha += 1
            print(f"[ERRO] {numero}: {resultado['motivo']}")

        resultados.append({
            'numero': numero,
            'status': 'sucesso' if resultado['sucesso'] else resultado['motivo'],
            'tamanho_mb': resultado.get('tamanho_mb', 0),
            'arquivo': resultado.get('arquivo', '')
        })

        if i < len(processos):
            time.sleep(args.delay)

    # Resumo compacto
    print(f"[FIM] {sucesso}/{len(processos)} OK, {total_mb:.1f}MB total")
    if dispensados > 0:
        print(f"      {dispensados} dispensados (muito grandes)")

    # Salvar log (detalhes ficam aqui)
    log_path = output_dir / '_download_log.json'
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump({
            'data': datetime.now().isoformat(),
            'sucesso': sucesso,
            'falha': falha,
            'dispensados': dispensados,
            'resultados': resultados
        }, f, indent=2, ensure_ascii=False)

    return 0 if falha == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
