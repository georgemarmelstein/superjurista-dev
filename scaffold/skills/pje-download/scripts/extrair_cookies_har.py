#!/usr/bin/env python3
"""
Extrai cookies e headers de arquivos HAR para autenticacao no PJE.

Uso:
    python extrair_cookies_har.py --har arquivo.har --output pje_session.json
    python extrair_cookies_har.py --har lista.har download.har --output pje_session.json

Fallback quando Chrome MCP nao funciona.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
import sys


def extrair_cookies_de_har(har_files: list[str]) -> dict:
    """
    Extrai cookies e headers relevantes de um ou mais arquivos HAR.

    IMPORTANTE: O PJE usa o header X-pje-cookies para enviar cookies nas
    requisicoes da API. Este header contem todos os cookies necessarios
    para download de PDFs.

    Args:
        har_files: Lista de caminhos para arquivos HAR

    Returns:
        Dicionario com cookies, headers e metadados
    """
    cookies = {}
    headers_api = {}
    x_pje_cookies_str = None  # String completa de cookies do PJE

    # Cookies essenciais do PJE
    cookies_essenciais = {
        'JSESSIONID',
        'KEYCLOAK_IDENTITY',
        'KEYCLOAK_SESSION',
        'trf5017e3f72',
        'trf501d4471f',
        'trf50130116e',
        'PJE-TRF5-1G-StickySessionRule',
        'ROUTER_ID',
        'dtCookie'
    }

    # Headers essenciais para API REST
    headers_essenciais = {
        'authorization',
        'x-pje-cookies',
        'x-pje-usuario-localizacao',
        'x-pje-legacy-app'
    }

    for har_path in har_files:
        path = Path(har_path).expanduser()

        if not path.exists():
            print(f"[AVISO] Arquivo nao encontrado: {har_path}", file=sys.stderr)
            continue

        print(f"[INFO] Processando: {path.name}")

        try:
            with open(path, 'r', encoding='utf-8') as f:
                har = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[ERRO] HAR invalido: {e}", file=sys.stderr)
            continue

        entries = har.get('log', {}).get('entries', [])

        for entry in entries:
            request = entry.get('request', {})

            # Extrair cookies dos requests (formato padrao)
            for cookie in request.get('cookies', []):
                name = cookie.get('name', '')
                value = cookie.get('value', '')

                if name and value:
                    # Priorizar cookies essenciais
                    if name in cookies_essenciais or name not in cookies:
                        cookies[name] = value

            # Extrair headers dos requests
            for header in request.get('headers', []):
                name = header.get('name', '').lower()
                value = header.get('value', '')

                # IMPORTANTE: Extrair cookies do header X-pje-cookies
                # O Chrome muitas vezes nao inclui cookies no array cookies[],
                # mas o PJE envia todos os cookies neste header customizado
                if name == 'x-pje-cookies' and value and not x_pje_cookies_str:
                    x_pje_cookies_str = value
                    # Parsear cookies do header
                    for part in value.split('; '):
                        if '=' in part:
                            cookie_name, cookie_value = part.split('=', 1)
                            if cookie_name not in cookies:
                                cookies[cookie_name] = cookie_value

                # Extrair header Cookie padrao tambem
                if name == 'cookie' and value and not x_pje_cookies_str:
                    for part in value.split('; '):
                        if '=' in part:
                            cookie_name, cookie_value = part.split('=', 1)
                            if cookie_name not in cookies:
                                cookies[cookie_name] = cookie_value

                if name in headers_essenciais and value:
                    # Normalizar nome do header
                    normalized_name = name.title().replace('-', '-')
                    if name == 'authorization':
                        normalized_name = 'Authorization'
                    elif name.startswith('x-pje'):
                        normalized_name = 'X-pje-' + name[6:].replace('-', '-')

                    headers_api[normalized_name] = value

            # Extrair cookies da resposta tambem
            response = entry.get('response', {})
            for cookie in response.get('cookies', []):
                name = cookie.get('name', '')
                value = cookie.get('value', '')

                if name and value and name in cookies_essenciais:
                    cookies[name] = value

    # Se temos X-pje-cookies, usar como cookie_download
    if x_pje_cookies_str:
        headers_api['X-pje-cookies'] = x_pje_cookies_str

    return cookies, headers_api, x_pje_cookies_str


def validar_sessao(cookies: dict, headers: dict) -> tuple[bool, list[str]]:
    """
    Valida se os dados extraidos sao suficientes.

    Returns:
        (valido, lista_de_avisos)
    """
    avisos = []

    # Verificar cookies minimos
    if 'JSESSIONID' not in cookies:
        avisos.append("JSESSIONID ausente - sessao JSF pode nao funcionar")

    if 'KEYCLOAK_IDENTITY' not in cookies and 'KEYCLOAK_SESSION' not in cookies:
        avisos.append("Cookies Keycloak ausentes - autenticacao pode falhar")

    # Verificar headers API
    if not headers.get('Authorization') and not headers.get('X-pje-cookies'):
        avisos.append("Headers de API ausentes - listagem pode nao funcionar")

    valido = 'JSESSIONID' in cookies or bool(headers)

    return valido, avisos


def gerar_cookie_string(cookies: dict) -> str:
    """Gera string de cookie para header Cookie."""
    return '; '.join(f"{k}={v}" for k, v in cookies.items())


def main():
    parser = argparse.ArgumentParser(
        description='Extrai cookies de arquivos HAR para autenticacao no PJE'
    )
    parser.add_argument(
        '--har',
        nargs='+',
        required=True,
        help='Arquivo(s) HAR para processar'
    )
    parser.add_argument(
        '--output',
        default='pje_session.json',
        help='Arquivo de saida (default: pje_session.json)'
    )

    args = parser.parse_args()

    print(f"[INFO] Processando {len(args.har)} arquivo(s) HAR...")

    cookies, headers, x_pje_cookies = extrair_cookies_de_har(args.har)

    if not cookies and not headers:
        print("[ERRO] Nenhum cookie ou header encontrado nos arquivos HAR", file=sys.stderr)
        print("[DICA] Certifique-se de que o HAR foi capturado com sessao ativa", file=sys.stderr)
        print("[DICA] O HAR deve conter requisicoes para pje1g.trf5.jus.br", file=sys.stderr)
        sys.exit(1)

    # Validar
    valido, avisos = validar_sessao(cookies, headers)

    for aviso in avisos:
        print(f"[AVISO] {aviso}")

    # Usar X-pje-cookies se disponivel, senao gerar string de cookies
    cookie_download = x_pje_cookies if x_pje_cookies else gerar_cookie_string(cookies)

    # Montar estrutura de saida compativel com os scripts existentes
    resultado = {
        "cookies": cookies,
        "headers_api": headers,
        "cookie_download": cookie_download,
        "base_url": "https://pje1g.trf5.jus.br",
        "extraido_em": datetime.now().isoformat(),
        "metodo": "har"
    }

    # Salvar
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    print()
    print(f"[INFO] Cookies encontrados: {len(cookies)}")
    for name in sorted(cookies.keys()):
        print(f"  - {name}")

    print()
    print(f"[INFO] Headers encontrados: {len(headers)}")
    for name in sorted(headers.keys()):
        print(f"  - {name}")

    print()
    if valido:
        print(f"[OK] Sessao salva em: {output_path}")
    else:
        print(f"[AVISO] Sessao salva mas pode estar incompleta: {output_path}")

    return 0 if valido else 1


if __name__ == '__main__':
    sys.exit(main())
