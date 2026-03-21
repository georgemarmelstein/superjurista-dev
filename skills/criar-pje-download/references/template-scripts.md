---
titulo: Templates de Scripts para PJE Download
---

# Templates de Scripts para PJE Download

Este documento contem templates parametrizaveis para criar scripts de download do PJE.

## Variaveis de Configuracao

Todos os scripts devem usar estas variaveis no topo:

```python
# =============================================================================
# CONFIGURACAO DO TRIBUNAL
# =============================================================================

# URL base do PJE (descoberta via HAR)
BASE_URL = "https://pje1g.TRIBUNAL.jus.br"

# URL do frontend (se diferente)
FRONTEND_URL = "https://frontend-prd.TRIBUNAL.jus.br"

# Header identificador da aplicacao
PJE_APP_NAME = "pje-TRIBUNAL-1g"

# Cookies especificos do tribunal (alem dos universais)
COOKIES_TRIBUNAL = ["TRIBUNALxxxxxxxx"]

# Nomes das tarefas/filas
TAREFAS = {
    "sentenca": "Elaboracao de Sentenca - Minutar",
    "decisao": "Elaboracao de decisao - Minutar"
}
```

---

## Template: extrair_cookies_har.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrai cookies de sessao do PJE a partir de arquivo HAR.
Adaptado para: [TRIBUNAL]
"""

import json
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Cookies universais do PJE
COOKIES_UNIVERSAIS = [
    'JSESSIONID',
    'KEYCLOAK_IDENTITY',
    'KEYCLOAK_SESSION',
    'dtCookie'
]

# Cookies especificos do tribunal (identificados no HAR)
COOKIES_TRIBUNAL = [
    # TODO: Adicionar cookies especificos descobertos no HAR
    # Exemplo: 'trf5017e3f72'
]

COOKIES_ESSENCIAIS = COOKIES_UNIVERSAIS + COOKIES_TRIBUNAL


def extrair_cookies_har(har_files: list) -> dict:
    """Extrai cookies de um ou mais arquivos HAR."""
    cookies = {}
    headers = {}

    for har_file in har_files:
        with open(har_file, 'r', encoding='utf-8') as f:
            har = json.load(f)

        for entry in har['log']['entries']:
            # Extrair cookies
            for cookie in entry['request'].get('cookies', []):
                name = cookie['name']
                if name not in cookies:
                    cookies[name] = cookie['value']

            # Extrair headers especificos
            for header in entry['request'].get('headers', []):
                name = header['name']
                if name.startswith('X-pje') or name == 'Authorization':
                    if name not in headers:
                        headers[name] = header['value']

    return {'cookies': cookies, 'headers': headers}


def validar_cookies(dados: dict) -> bool:
    """Verifica se cookies essenciais estao presentes."""
    cookies = dados.get('cookies', {})

    # Verificar JSESSIONID (obrigatorio)
    if 'JSESSIONID' not in cookies:
        print("[ERRO] JSESSIONID nao encontrado!")
        return False

    # Verificar Keycloak (se aplicavel)
    # Alguns tribunais nao usam Keycloak
    # if 'KEYCLOAK_IDENTITY' not in cookies:
    #     print("[AVISO] KEYCLOAK_IDENTITY nao encontrado")

    return True


def main():
    parser = argparse.ArgumentParser(
        description='Extrai cookies do PJE de arquivo HAR'
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

    # Verificar arquivos
    for har_file in args.har:
        if not Path(har_file).exists():
            print(f"[ERRO] Arquivo nao encontrado: {har_file}")
            sys.exit(1)

    print(f"[INICIO] Processando {len(args.har)} arquivo(s) HAR...")

    # Extrair
    dados = extrair_cookies_har(args.har)

    # Validar
    if not validar_cookies(dados):
        print("[ERRO] Cookies essenciais ausentes!")
        sys.exit(1)

    # Adicionar metadados
    dados['extraido_em'] = datetime.now().isoformat()
    dados['metodo'] = 'har'
    dados['arquivos_fonte'] = args.har

    # Salvar
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)

    print(f"[OK] Cookies salvos em: {args.output}")

    # Resumo
    print(f"\n[INFO] Cookies encontrados: {len(dados['cookies'])}")
    for name in dados['cookies']:
        print(f"  - {name}")


if __name__ == '__main__':
    main()
```

---

## Template: listar_processos.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lista processos conclusos do PJE.
Adaptado para: [TRIBUNAL]
"""

import json
import argparse
import requests
import sys
from urllib.parse import quote

# =============================================================================
# CONFIGURACAO DO TRIBUNAL (EDITAR AQUI)
# =============================================================================

BASE_URL = "https://pje1g.TRIBUNAL.jus.br"
PJE_APP_NAME = "pje-TRIBUNAL-1g"

TAREFAS = {
    "sentenca": "Elaboracao de Sentenca - Minutar",
    "decisao": "Elaboracao de decisao - Minutar"
}

# =============================================================================


def carregar_sessao(arquivo: str) -> dict:
    """Carrega dados de sessao do arquivo JSON."""
    with open(arquivo, 'r', encoding='utf-8') as f:
        return json.load(f)


def criar_sessao_requests(dados: dict) -> requests.Session:
    """Cria sessao requests com cookies e headers."""
    session = requests.Session()

    # Adicionar cookies
    for name, value in dados.get('cookies', {}).items():
        session.cookies.set(name, value)

    # Headers padrao
    session.headers.update({
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Origin': BASE_URL,
        'Referer': f'{BASE_URL}/pje/ng2/dev.seam',
        'X-pje-legacy-app': PJE_APP_NAME,
    })

    # Headers extras do HAR
    for name, value in dados.get('headers', {}).items():
        if name.startswith('X-pje'):
            session.headers[name] = value

    return session


def listar_processos(session: requests.Session, tarefa: str, limite: int = 0) -> list:
    """Lista processos de uma tarefa."""
    tarefa_encoded = quote(tarefa)
    url = f"{BASE_URL}/pje/seam/resource/rest/pje-legacy/painelUsuario/recuperarProcessosTarefaPendenteComCriterios/{tarefa_encoded}/false"

    response = session.get(url, timeout=60)

    if response.status_code != 200:
        print(f"[ERRO] API retornou status {response.status_code}")
        return []

    try:
        dados = response.json()
    except json.JSONDecodeError:
        print("[ERRO] Resposta nao e JSON (sessao expirada?)")
        return []

    processos = dados if isinstance(dados, list) else dados.get('processos', [])

    if limite > 0:
        processos = processos[:limite]

    return processos


def main():
    parser = argparse.ArgumentParser(description='Lista processos do PJE')
    parser.add_argument('--cookies', required=True, help='Arquivo de sessao')
    parser.add_argument('--modo', choices=['sentenca', 'decisao'], default='sentenca')
    parser.add_argument('--limite', type=int, default=0, help='Limite de processos')
    parser.add_argument('--output', default='processos.json', help='Arquivo de saida')

    args = parser.parse_args()

    print(f"[INICIO] Modo: {args.modo.upper()}")

    # Carregar sessao
    dados = carregar_sessao(args.cookies)
    session = criar_sessao_requests(dados)

    # Buscar processos
    tarefa = TAREFAS[args.modo]
    print(f"[INFO] Buscando tarefa: {tarefa}")

    processos = listar_processos(session, tarefa, args.limite)

    if not processos:
        print("[AVISO] Nenhum processo encontrado")
        sys.exit(0)

    print(f"[OK] {len(processos)} processos encontrados")

    # Salvar
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({'processos': processos}, f, indent=2, ensure_ascii=False)

    print(f"[FIM] Salvo em: {args.output}")


if __name__ == '__main__':
    main()
```

---

## Template: baixar_pdfs.py

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baixa PDFs dos autos digitais do PJE.
Adaptado para: [TRIBUNAL]
"""

import json
import argparse
import requests
import time
import re
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# =============================================================================
# CONFIGURACAO DO TRIBUNAL (EDITAR AQUI)
# =============================================================================

BASE_URL = "https://pje1g.TRIBUNAL.jus.br"
FRONTEND_URL = "https://frontend-prd.TRIBUNAL.jus.br"

# =============================================================================

TIMEOUT = 120  # segundos


def carregar_sessao(arquivo: str) -> dict:
    with open(arquivo, 'r', encoding='utf-8') as f:
        return json.load(f)


def criar_sessao_requests(dados: dict) -> requests.Session:
    session = requests.Session()

    for name, value in dados.get('cookies', {}).items():
        session.cookies.set(name, value)

    session.headers.update({
        'Accept': 'text/html,application/pdf',
        'Origin': BASE_URL,
    })

    return session


def obter_chave_acesso(session: requests.Session, id_processo: str) -> str:
    """Obtem chave de acesso para um processo."""
    url = f"{BASE_URL}/pje/seam/resource/rest/pje-legacy/painelUsuario/gerarChaveAcessoProcesso/{id_processo}"

    # Headers especificos para esta requisicao
    headers = {
        'Accept': 'application/json',
        'Origin': FRONTEND_URL,
        'Referer': f'{FRONTEND_URL}/'
    }

    response = session.get(url, headers=headers, timeout=30)

    if response.status_code != 200:
        return None

    try:
        dados = response.json()
        return dados.get('chaveTemporaria') or dados.get('ca')
    except:
        return None


def baixar_autos(session: requests.Session, chave_acesso: str, output_path: Path) -> bool:
    """Baixa PDF dos autos usando a chave de acesso."""
    url = f"{BASE_URL}/pje/Processo/ConsultaProcesso/Detalhe/listAutosDigitais.seam"
    params = {'ca': chave_acesso}

    # Primeira requisicao: obter ViewState
    response = session.get(url, params=params, timeout=TIMEOUT)

    if response.status_code != 200:
        print(f"[ERRO] Falha ao acessar autos: {response.status_code}")
        return False

    # Parsear HTML para ViewState
    soup = BeautifulSoup(response.text, 'html.parser')
    viewstate = soup.find('input', {'name': 'javax.faces.ViewState'})

    if not viewstate:
        print("[ERRO] ViewState nao encontrado (sessao expirada?)")
        return False

    # Segunda requisicao: download do PDF
    form_data = {
        'javax.faces.ViewState': viewstate['value'],
        # TODO: Ajustar campos do form conforme tribunal
    }

    response = session.post(url, data=form_data, timeout=TIMEOUT)

    if 'application/pdf' not in response.headers.get('Content-Type', ''):
        print("[ERRO] Resposta nao e PDF")
        return False

    # Salvar PDF
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        f.write(response.content)

    print(f"[OK] Salvo: {output_path}")
    return True


def main():
    parser = argparse.ArgumentParser(description='Baixa PDFs do PJE')
    parser.add_argument('--cookies', required=True, help='Arquivo de sessao')
    parser.add_argument('--processos', required=True, help='Arquivo JSON com lista')
    parser.add_argument('--output', default='./downloads', help='Diretorio de saida')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay entre downloads')
    parser.add_argument('--limite', type=int, default=0, help='Limite de processos')

    args = parser.parse_args()

    # Carregar dados
    dados_sessao = carregar_sessao(args.cookies)
    session = criar_sessao_requests(dados_sessao)

    with open(args.processos, 'r', encoding='utf-8') as f:
        dados_processos = json.load(f)

    processos = dados_processos.get('processos', dados_processos)
    if args.limite > 0:
        processos = processos[:args.limite]

    print(f"[INICIO] {len(processos)} processos -> {args.output}")

    output_dir = Path(args.output)
    sucesso = 0
    falha = 0

    for i, proc in enumerate(processos):
        id_processo = proc.get('id') or proc.get('idProcesso')
        numero = proc.get('numero') or proc.get('numeroProcesso')

        print(f"\n[{i+1}/{len(processos)}] {numero}")

        # Obter chave
        chave = obter_chave_acesso(session, id_processo)
        if not chave:
            print("[ERRO] Falha ao obter chave de acesso")
            falha += 1
            continue

        # Baixar PDF
        pdf_path = output_dir / numero / f"{numero}.pdf"
        if baixar_autos(session, chave, pdf_path):
            sucesso += 1
        else:
            falha += 1

        # Delay
        if i < len(processos) - 1:
            time.sleep(args.delay)

    print(f"\n[FIM] {sucesso} OK, {falha} ERRO")


if __name__ == '__main__':
    main()
```

---

## Checklist de Adaptacao

Ao criar scripts para um novo tribunal:

- [ ] Substituir `BASE_URL` pelo dominio correto
- [ ] Substituir `FRONTEND_URL` se aplicavel
- [ ] Substituir `PJE_APP_NAME` pelo header X-pje-legacy-app
- [ ] Adicionar cookies especificos do tribunal em `COOKIES_TRIBUNAL`
- [ ] Verificar nomes das tarefas/filas
- [ ] Testar com HAR recente
- [ ] Documentar diferencas encontradas
