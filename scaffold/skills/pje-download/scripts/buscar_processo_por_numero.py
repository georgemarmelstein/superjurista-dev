#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Busca ID interno do processo no PJE a partir do número CNJ.

Uso:
    python buscar_processo_por_numero.py --cookies pje_session.json --numero 0822811-25.2019.4.05.8100
"""

import json
import argparse
import requests
import sys
from urllib.parse import quote

# Configurações
BASE_URL = "https://pje1g.trf5.jus.br"


def carregar_cookies(cookies_path: str) -> dict:
    """Carrega cookies do arquivo JSON."""
    with open(cookies_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def criar_sessao(dados_auth: dict) -> requests.Session:
    """Cria sessão requests com cookies."""
    session = requests.Session()

    cookie_str = dados_auth.get('cookie_download', '')
    if not cookie_str:
        cookies_dict = dados_auth.get('cookies', {})
        if cookies_dict:
            cookie_str = '; '.join(f'{k}={v}' for k, v in cookies_dict.items())

    session.headers.update({
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Origin': 'https://pje1g.trf5.jus.br',
        'Referer': 'https://pje1g.trf5.jus.br/pje/ng2/dev.seam',
        'X-pje-legacy-app': 'pje-trf5-1g',
        'Content-Type': 'application/json',
        'Cookie': cookie_str
    })

    return session


def buscar_por_numero_api(session: requests.Session, numero_cnj: str) -> dict:
    """Busca processo pela API de consulta pública."""
    # Tentar consulta pela API REST
    url = f"{BASE_URL}/pje/seam/resource/rest/pje-legacy/api/processoPublico/consultarProcessoPorNumero/{quote(numero_cnj)}"

    try:
        print(f"[DEBUG] Consultando API: {url}")
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = session.get(url, timeout=30, verify=False)

        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"[DEBUG] API pública falhou: {e}")

    return None


def buscar_na_fila_tarefa(session: requests.Session, numero_cnj: str, tarefa: str) -> dict:
    """Busca processo na fila de tarefas pelo número."""
    tarefa_encoded = quote(tarefa, safe='')
    url = f"{BASE_URL}/pje/seam/resource/rest/pje-legacy/painelUsuario/recuperarProcessosTarefaPendenteComCriterios/{tarefa_encoded}/false"

    payload = {
        "numeroProcesso": numero_cnj,
        "page": 0,
        "maxResults": 10
    }

    try:
        print(f"[DEBUG] Buscando na fila: {tarefa}")
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = session.post(url, json=payload, timeout=60, verify=False)

        if response.status_code == 200:
            dados = response.json()
            if isinstance(dados, dict) and 'entities' in dados:
                processos = dados['entities']
                if processos:
                    return processos[0]  # Retorna o primeiro encontrado
    except Exception as e:
        print(f"[DEBUG] Busca na fila falhou: {e}")

    return None


def buscar_todas_filas(session: requests.Session, numero_cnj: str) -> dict:
    """Busca processo em todas as filas de tarefas."""
    tarefas = [
        "Elaboração de sentença - Minutar",
        "Elaboração de decisão - Minutar",
        "Julgamento - Aguardando"
    ]

    for tarefa in tarefas:
        resultado = buscar_na_fila_tarefa(session, numero_cnj, tarefa)
        if resultado:
            return resultado

    return None


def main():
    parser = argparse.ArgumentParser(
        description='Busca ID do processo no PJE por número CNJ'
    )
    parser.add_argument(
        '--cookies', '-c',
        required=True,
        help='Arquivo JSON com cookies de autenticação'
    )
    parser.add_argument(
        '--numero', '-n',
        required=True,
        help='Número CNJ do processo (ex: 0822811-25.2019.4.05.8100)'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Arquivo de saída JSON (opcional)'
    )

    args = parser.parse_args()

    print(f"[INFO] Carregando cookies de {args.cookies}...")
    dados_auth = carregar_cookies(args.cookies)

    session = criar_sessao(dados_auth)

    print(f"[INFO] Buscando processo: {args.numero}")

    # Tentar API pública primeiro
    resultado = buscar_por_numero_api(session, args.numero)

    # Se não encontrar, tentar nas filas
    if not resultado:
        print("[INFO] Tentando busca nas filas de tarefas...")
        resultado = buscar_todas_filas(session, args.numero)

    if resultado:
        id_processo = resultado.get('idProcesso') or resultado.get('id')
        numero = resultado.get('numeroProcesso') or resultado.get('numero')

        print()
        print("=" * 60)
        print("[OK] Processo encontrado!")
        print(f"  Número CNJ: {numero}")
        print(f"  ID interno: {id_processo}")

        if 'idTaskInstance' in resultado:
            print(f"  ID tarefa: {resultado.get('idTaskInstance')}")
        if 'classeJudicial' in resultado:
            print(f"  Classe: {resultado.get('classeJudicial')}")
        if 'poloAtivo' in resultado:
            polo = resultado.get('poloAtivo', '')[:60]
            print(f"  Polo ativo: {polo}...")

        print("=" * 60)

        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(resultado, f, indent=2, ensure_ascii=False)
            print(f"[INFO] Dados salvos em: {args.output}")

        # Imprimir apenas o ID para captura em script
        print(f"\nID_PROCESSO={id_processo}")
        return 0
    else:
        print()
        print("[ERRO] Processo não encontrado")
        print("[DICA] Verifique se o número está correto e se você tem acesso ao processo")
        return 1


if __name__ == '__main__':
    sys.exit(main())
