#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Login programatico no PJE TRF5 via Keycloak SSO.
Gera pje_session.json compativel com scripts existentes.

AVISO IMPORTANTE (2026-02):
==========================
Este script NAO FUNCIONA atualmente porque o Keycloak do PJE TRF5 nao permite
"direct access grants" (OAuth2 Resource Owner Password Credentials Flow).

Erro retornado: "Client not allowed for direct access grants"

ALTERNATIVAS FUNCIONAIS:
1. Chrome MCP (login via browser automatizado) + HAR
2. HAR manual (sempre funciona)

Este script e mantido para referencia e caso a configuracao do Keycloak mude.

Uso original (nao funciona):
    # Via variaveis de ambiente
    export PJE_CPF="12345678900"
    export PJE_SENHA="minha_senha"
    python login_programatico.py --output pje_session.json

    # Via argumentos (menos seguro)
    python login_programatico.py --cpf 12345678900 --senha minha_senha

Metodo tentado:
    1. OAuth2 Password Flow contra Keycloak SSO
    2. Obtencao de JSESSIONID via navegacao simulada
    3. Geracao de pje_session.json compativel
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import urlencode, urlparse, parse_qs

# ===========================
# CONFIGURACAO
# ===========================
# URLs do PJE TRF5
KEYCLOAK_BASE = "https://sso.cloud.pje.jus.br"
KEYCLOAK_REALM = "pje"
PJE_FRONTEND = "https://frontend-prd.trf5.jus.br"
PJE_BACKEND = "https://pje1g.trf5.jus.br"

# Endpoints Keycloak
KEYCLOAK_TOKEN_URL = f"{KEYCLOAK_BASE}/auth/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
KEYCLOAK_AUTH_URL = f"{KEYCLOAK_BASE}/auth/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth"

# Client IDs a tentar (ordem de prioridade)
CLIENT_IDS = ["pje-frontend", "pje-trf5-1g", "frontend-prd.trf5.jus.br"]

# Timeout de requisicoes
REQUEST_TIMEOUT = 30


# ===========================
# EXCECOES CUSTOMIZADAS
# ===========================
class PJEAuthError(Exception):
    """Erro de autenticacao no PJE"""
    pass


class InvalidCredentialsError(PJEAuthError):
    """Credenciais invalidas"""
    pass


class TwoFactorRequiredError(PJEAuthError):
    """Autenticacao requer 2FA"""
    pass


class CaptchaRequiredError(PJEAuthError):
    """Autenticacao requer CAPTCHA"""
    pass


class SessionError(PJEAuthError):
    """Erro ao obter sessao"""
    pass


# ===========================
# FUNCOES AUXILIARES
# ===========================
def sanitize_cpf(cpf: str) -> str:
    """Remove caracteres nao numericos do CPF."""
    return ''.join(c for c in cpf if c.isdigit())


def decode_jwt_payload(token: str) -> dict:
    """Decodifica payload JWT sem verificar assinatura."""
    import base64

    try:
        # JWT tem 3 partes: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return {}

        # Payload e a segunda parte (base64url encoded)
        payload_b64 = parts[1]
        # Adicionar padding se necessario
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding

        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes.decode('utf-8'))
    except Exception:
        return {}


# ===========================
# CLASSE PRINCIPAL
# ===========================
class PJEAuthenticator:
    """Gerencia autenticacao programatica no PJE TRF5."""

    def __init__(self, cpf: str, senha: str, verbose: bool = False):
        self.cpf = sanitize_cpf(cpf)
        self.senha = senha
        self.verbose = verbose
        self.session = requests.Session()

        # User-Agent realista
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        })

    def _log(self, msg: str):
        """Log apenas se verbose."""
        if self.verbose:
            print(f"  [DEBUG] {msg}")

    def _try_password_flow(self, client_id: str) -> Optional[dict]:
        """Tenta OAuth2 Password Flow com um client_id especifico."""
        self._log(f"Tentando client_id: {client_id}")

        payload = {
            'grant_type': 'password',
            'client_id': client_id,
            'username': self.cpf,
            'password': self.senha,
            'scope': 'openid'
        }

        try:
            response = self.session.post(
                KEYCLOAK_TOKEN_URL,
                data=payload,
                timeout=REQUEST_TIMEOUT,
                verify=True  # Verificar SSL em producao
            )

            self._log(f"Status: {response.status_code}")

            if response.status_code == 200:
                return response.json()

            # Analisar erro
            try:
                error_data = response.json()
                error_desc = error_data.get('error_description', '')
                error_code = error_data.get('error', '')

                self._log(f"Erro: {error_code} - {error_desc}")

                if error_code == 'invalid_grant':
                    raise InvalidCredentialsError(f"Credenciais invalidas: {error_desc}")

                if 'otp' in error_desc.lower() or '2fa' in error_desc.lower():
                    raise TwoFactorRequiredError("Autenticacao 2FA requerida")

                if 'captcha' in error_desc.lower():
                    raise CaptchaRequiredError("CAPTCHA requerido")

            except json.JSONDecodeError:
                pass

            return None

        except requests.exceptions.Timeout:
            self._log("Timeout na requisicao")
            return None
        except requests.exceptions.RequestException as e:
            self._log(f"Erro de rede: {e}")
            return None

    def _try_authorization_code_flow(self) -> Optional[dict]:
        """
        Tenta Authorization Code Flow simulando navegacao.
        Fallback quando Password Flow nao esta habilitado.
        """
        self._log("Tentando Authorization Code Flow...")

        # Parametros para iniciar o fluxo
        params = {
            'client_id': 'pje-frontend',
            'redirect_uri': f'{PJE_FRONTEND}/callback',
            'response_type': 'code',
            'scope': 'openid',
            'state': 'pje_login'
        }

        try:
            # 1. Iniciar fluxo - obter pagina de login
            auth_url = f"{KEYCLOAK_AUTH_URL}?{urlencode(params)}"
            response = self.session.get(auth_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)

            self._log(f"Auth URL status: {response.status_code}")

            if response.status_code != 200:
                return None

            # 2. Encontrar action URL do formulario
            html = response.text

            # Procurar por action URL no formulario Keycloak
            import re
            action_match = re.search(r'action="([^"]+)"', html)
            if not action_match:
                self._log("Formulario de login nao encontrado")
                return None

            action_url = action_match.group(1).replace('&amp;', '&')
            self._log(f"Action URL: {action_url}")

            # 3. Submeter credenciais
            login_data = {
                'username': self.cpf,
                'password': self.senha
            }

            response = self.session.post(
                action_url,
                data=login_data,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            )

            self._log(f"Login status: {response.status_code}")
            self._log(f"Final URL: {response.url}")

            # 4. Verificar se chegou no callback com codigo
            if 'callback' in response.url and 'code=' in response.url:
                # Extrair codigo do callback
                parsed = urlparse(response.url)
                params = parse_qs(parsed.query)
                code = params.get('code', [None])[0]

                if code:
                    self._log(f"Codigo obtido: {code[:20]}...")

                    # 5. Trocar codigo por tokens
                    token_data = {
                        'grant_type': 'authorization_code',
                        'client_id': 'pje-frontend',
                        'code': code,
                        'redirect_uri': f'{PJE_FRONTEND}/callback'
                    }

                    token_response = self.session.post(
                        KEYCLOAK_TOKEN_URL,
                        data=token_data,
                        timeout=REQUEST_TIMEOUT
                    )

                    if token_response.status_code == 200:
                        return token_response.json()

            # Verificar se login falhou
            if 'Invalid username or password' in response.text:
                raise InvalidCredentialsError("Credenciais invalidas")

            if 'captcha' in response.text.lower():
                raise CaptchaRequiredError("CAPTCHA requerido")

            return None

        except (InvalidCredentialsError, CaptchaRequiredError, TwoFactorRequiredError):
            raise
        except Exception as e:
            self._log(f"Erro no authorization code flow: {e}")
            return None

    def authenticate(self) -> dict:
        """
        Executa autenticacao e retorna tokens.

        Returns:
            dict com access_token, id_token, refresh_token

        Raises:
            PJEAuthError em caso de falha
        """
        print("[ETAPA 1] Autenticando no Keycloak SSO...")

        # Tentar Password Flow com diferentes client_ids
        for client_id in CLIENT_IDS:
            try:
                tokens = self._try_password_flow(client_id)
                if tokens:
                    self._log(f"Sucesso com client_id: {client_id}")
                    return tokens
            except (InvalidCredentialsError, TwoFactorRequiredError, CaptchaRequiredError):
                # Erros que nao vale a pena tentar outro client_id
                raise

        # Fallback: Authorization Code Flow
        self._log("Password Flow falhou, tentando Authorization Code Flow...")
        tokens = self._try_authorization_code_flow()
        if tokens:
            return tokens

        raise PJEAuthError("Nenhum metodo de autenticacao funcionou. Use HAR como fallback.")

    def get_session_cookies(self, tokens: dict) -> dict:
        """
        Navega no PJE para obter cookies de sessao (JSESSIONID, etc).

        Args:
            tokens: dict com access_token e id_token

        Returns:
            dict com cookies capturados
        """
        print("[ETAPA 2] Obtendo cookies de sessao...")

        id_token = tokens.get('id_token', '')
        access_token = tokens.get('access_token', '')

        # Extrair info do token
        token_payload = decode_jwt_payload(id_token)
        self._log(f"Token payload keys: {list(token_payload.keys())}")

        # Configurar cookies Keycloak
        keycloak_cookies = {
            'KEYCLOAK_IDENTITY': id_token,
            'KEYCLOAK_SESSION': tokens.get('session_state', '')
        }

        for name, value in keycloak_cookies.items():
            if value:
                self.session.cookies.set(name, value)

        # Navegar para obter JSESSIONID
        endpoints_to_try = [
            f"{PJE_BACKEND}/pje/ng2/dev.seam",
            f"{PJE_BACKEND}/pje/seam/resource/rest/pje-legacy/painelUsuario",
            f"{PJE_FRONTEND}",
        ]

        for endpoint in endpoints_to_try:
            self._log(f"Tentando endpoint: {endpoint}")

            try:
                response = self.session.get(
                    endpoint,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                    verify=True
                )

                self._log(f"Status: {response.status_code}")

                # Verificar se obteve JSESSIONID
                if 'JSESSIONID' in self.session.cookies:
                    self._log("JSESSIONID obtido!")
                    break

            except Exception as e:
                self._log(f"Erro: {e}")
                continue

        # Coletar todos os cookies
        cookies = {}
        for cookie in self.session.cookies:
            cookies[cookie.name] = cookie.value
            self._log(f"Cookie: {cookie.name}")

        # Adicionar cookies Keycloak se nao estiverem
        for name, value in keycloak_cookies.items():
            if name not in cookies and value:
                cookies[name] = value

        return cookies, token_payload

    def build_session_file(self, cookies: dict, token_payload: dict) -> dict:
        """
        Constroi estrutura do pje_session.json compativel.
        """
        print("[ETAPA 3] Gerando pje_session.json...")

        # Gerar string de cookies
        cookie_string = '; '.join(f"{k}={v}" for k, v in cookies.items())

        # Extrair localizacao do token
        localizacao = token_payload.get('jtr', token_payload.get('preferred_username', ''))

        session_data = {
            "cookies": cookies,
            "headers_api": {
                "X-pje-legacy-app": "pje-trf5-1g",
                "X-pje-cookies": cookie_string,
                "X-pje-usuario-localizacao": str(localizacao) if localizacao else ""
            },
            "cookie_download": cookie_string,
            "extraido_em": datetime.now().isoformat(),
            "metodo": "programatico"
        }

        return session_data


def validate_session(session_data: dict) -> Tuple[bool, list]:
    """Valida se sessao esta completa."""
    warnings = []

    cookies = session_data.get('cookies', {})

    if 'JSESSIONID' not in cookies:
        warnings.append("JSESSIONID ausente - download pode nao funcionar")

    if 'KEYCLOAK_IDENTITY' not in cookies:
        warnings.append("KEYCLOAK_IDENTITY ausente - autenticacao pode falhar")

    valid = 'JSESSIONID' in cookies or 'KEYCLOAK_IDENTITY' in cookies

    return valid, warnings


def main():
    parser = argparse.ArgumentParser(
        description='Login programatico no PJE TRF5',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    # Via variaveis de ambiente (recomendado)
    export PJE_CPF="12345678900"
    export PJE_SENHA="minha_senha"
    python login_programatico.py

    # Via argumentos
    python login_programatico.py --cpf 12345678900 --senha minha_senha
        """
    )

    parser.add_argument(
        '--cpf',
        default=os.getenv('PJE_CPF'),
        help='CPF do usuario (ou variavel PJE_CPF)'
    )
    parser.add_argument(
        '--senha',
        default=os.getenv('PJE_SENHA'),
        help='Senha do usuario (ou variavel PJE_SENHA)'
    )
    parser.add_argument(
        '--output', '-o',
        default='pje_session.json',
        help='Arquivo de saida (padrao: pje_session.json)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Output detalhado para debug'
    )

    args = parser.parse_args()

    # Validar credenciais
    if not args.cpf:
        print("[ERRO] CPF nao fornecido. Use --cpf ou variavel PJE_CPF")
        return 1

    if not args.senha:
        print("[ERRO] Senha nao fornecida. Use --senha ou variavel PJE_SENHA")
        return 1

    print(f"[INICIO] Login programatico no PJE TRF5")
    print(f"  CPF: {args.cpf[:3]}***{args.cpf[-2:]}")

    try:
        # Autenticar
        auth = PJEAuthenticator(args.cpf, args.senha, verbose=args.verbose)
        tokens = auth.authenticate()

        # Obter cookies de sessao
        cookies, token_payload = auth.get_session_cookies(tokens)

        # Construir arquivo de sessao
        session_data = auth.build_session_file(cookies, token_payload)

        # Validar
        valid, warnings = validate_session(session_data)

        for warning in warnings:
            print(f"[AVISO] {warning}")

        # Salvar
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        # Resumo
        print()
        print(f"[OK] Cookies capturados: {len(cookies)}")
        for name in sorted(cookies.keys()):
            print(f"  - {name}")

        print()
        if valid:
            print(f"[FIM] Sessao salva em: {output_path}")
            return 0
        else:
            print(f"[AVISO] Sessao salva mas pode estar incompleta: {output_path}")
            return 0  # Ainda salva para tentar usar

    except InvalidCredentialsError as e:
        print(f"[ERRO] {e}")
        print("[DICA] Verifique se CPF e senha estao corretos")
        return 1

    except TwoFactorRequiredError as e:
        print(f"[ERRO] {e}")
        print("[FALLBACK] Use Chrome MCP ou HAR manual")
        return 2

    except CaptchaRequiredError as e:
        print(f"[ERRO] {e}")
        print("[FALLBACK] Use Chrome MCP ou HAR manual")
        return 3

    except PJEAuthError as e:
        print(f"[ERRO] {e}")
        print("[FALLBACK] Use Chrome MCP ou HAR manual")
        return 4

    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 99


if __name__ == '__main__':
    sys.exit(main())
