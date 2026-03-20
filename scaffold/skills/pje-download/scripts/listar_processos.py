#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lista processos conclusos para elaboração de minuta no PJE TRF5.
Suporta dois modos: sentença e decisão.
Suporta filtros avançados: etiquetas, prioridade, partes, etc.

Uso:
    python listar_processos.py --cookies cookies.json --modo sentenca --limite 10
    python listar_processos.py --cookies cookies.json --modo decisao --tags URGENTE --prioridade
    python listar_processos.py --cookies cookies.json --modo sentenca --polo-passivo INSS
"""

import json
import argparse
import requests
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


# Configurações
BASE_URL = "https://pje1g.trf5.jus.br"

# Tarefas por modo
TAREFAS = {
    'sentenca': "Elaboração de sentença - Minutar",
    'decisao': "Elaboração de decisão - Minutar"
}


def carregar_cookies(cookies_path: str) -> dict:
    """Carrega cookies do arquivo JSON."""
    with open(cookies_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def criar_sessao(dados_auth: dict) -> requests.Session:
    """
    Cria sessão requests com cookies e headers de autenticação.
    """
    session = requests.Session()

    # Obter string de cookies para enviar no header Cookie
    cookie_string = dados_auth.get('cookie_download', '')
    if not cookie_string:
        # Construir a partir do dict de cookies
        cookies = dados_auth.get('cookies', {})
        cookie_string = '; '.join(f'{k}={v}' for k, v in cookies.items())

    # Headers padrão - IMPORTANTE: Origin e Referer devem ser do mesmo domínio da API
    session.headers.update({
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'pt-BR,pt;q=0.8,en-US;q=0.5,en;q=0.3',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:145.0) Gecko/20100101 Firefox/145.0',
        'Origin': 'https://pje1g.trf5.jus.br',
        'Referer': 'https://pje1g.trf5.jus.br/pje/ng2/dev.seam',
        'X-pje-legacy-app': 'pje-trf5-1g',
        'Content-Type': 'application/json',
        'Cookie': cookie_string  # Enviar cookies diretamente no header
    })

    # Headers de autenticação para API REST
    # IMPORTANTE: NÃO enviar Authorization - a API usa apenas cookies!
    headers_auth = dados_auth.get('headers_api', dados_auth.get('headers', {}))
    for nome, valor in headers_auth.items():
        # Pular Authorization - causa 401 se enviado
        if nome == 'Authorization':
            continue
        session.headers[nome] = valor

    return session


def listar_processos_conclusos(session: requests.Session, tarefa: str, filtros: dict = None) -> list:
    """
    Lista processos conclusos para a tarefa especificada.

    Args:
        session: Sessão requests autenticada
        tarefa: Nome da tarefa (ex: "Elaboração de sentença - Minutar")
        filtros: Dicionário opcional de filtros (tags, prioridade, etc.)

    Returns:
        Lista de processos encontrados
    """
    if filtros is None:
        filtros = {}

    tarefa_encoded = quote(tarefa, safe='')
    url = f"{BASE_URL}/pje/seam/resource/rest/pje-legacy/painelUsuario/recuperarProcessosTarefaPendenteComCriterios/{tarefa_encoded}/false"

    payload = {
        "numeroProcesso": "",
        "classe": filtros.get('classe'),
        "tags": filtros.get('tags', []),
        "tagsString": None,
        "poloAtivo": filtros.get('polo_ativo'),
        "poloPassivo": filtros.get('polo_passivo'),
        "orgao": None,
        "ordem": None,
        "page": 0,
        "maxResults": 300,
        "idTaskInstance": None,
        "apelidoSessao": None,
        "idTipoSessao": None,
        "dataSessao": None,
        "somenteFavoritas": None,
        "objeto": None,
        "semEtiqueta": filtros.get('sem_etiqueta'),
        "assunto": filtros.get('assunto'),
        "dataAutuacao": None,
        "nomeParte": filtros.get('nome_parte'),
        "nomeFiltro": None,
        "numeroDocumento": None,
        "competencia": "",
        "relator": None,
        "orgaoJulgador": None,
        "somenteLembrete": None,
        "somenteSigiloso": filtros.get('sigiloso'),
        "somenteLiminar": filtros.get('liminar'),
        "eleicao": None,
        "estado": None,
        "municipio": None,
        "prioridadeProcesso": filtros.get('prioridade'),
        "cpfCnpj": filtros.get('cpf_cnpj'),
        "porEtiqueta": None,
        "conferidos": filtros.get('conferidos'),
        "orgaoJulgadorColegiado": None,
        "naoLidos": filtros.get('nao_lidos'),
        "tipoProcessoDocumento": None,
        "somenteComTodasTags": filtros.get('todas_tags')
    }

    try:
        # Desabilitar verificação SSL e warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = session.post(url, json=payload, timeout=60, verify=False)

        if response.status_code == 401:
            return []

        if response.status_code == 403:
            return []

        response.raise_for_status()
        dados = response.json()

        if isinstance(dados, dict):
            if 'entities' in dados:
                processos = dados['entities']
            elif 'processos' in dados:
                processos = dados['processos']
            else:
                processos = []
        else:
            processos = dados

        return processos

    except requests.exceptions.RequestException as e:
        return []


def extrair_metadados_processo(processo: dict) -> dict:
    """Extrai metadados relevantes de um processo."""
    data_chegada = processo.get('dataChegada')
    if data_chegada and isinstance(data_chegada, (int, float)):
        data_chegada = datetime.fromtimestamp(data_chegada / 1000).isoformat()

    return {
        'id_processo': processo.get('idProcesso'),
        'id_tarefa': processo.get('idTaskInstance'),
        'id_tarefa_proximo': processo.get('idTaskInstanceProximo'),
        'numero_cnj': processo.get('numeroProcesso') or processo.get('numero'),
        'classe': processo.get('classeJudicial') or processo.get('classe'),
        'assunto': processo.get('assunto') or processo.get('assuntoPrincipal'),
        'polo_ativo': processo.get('poloAtivo'),
        'polo_passivo': processo.get('poloPassivo'),
        'orgao_julgador': processo.get('orgaoJulgador'),
        'id_orgao_julgador': processo.get('idOrgaoJulgador'),
        'data_conclusao': data_chegada,
        'valor_causa': processo.get('valorCausa'),
        'prioridade': processo.get('prioridade', False),
        'sigiloso': processo.get('sigiloso', False),
        'conferido': processo.get('conferido', False),
        'nome_tarefa': processo.get('nomeTarefa'),
        'etiquetas': processo.get('etiquetas', []),
        'codigo_acesso': processo.get('ca'),
        'dados_brutos': processo
    }


def ordenar_processos(processos: list, ordem: str = 'crescente') -> list:
    """Ordena processos por data de conclusão."""
    def get_data(p):
        data = p.get('data_conclusao') or p.get('dados_brutos', {}).get('dataInicio', '')
        return data or ''

    reverse = ordem.lower() == 'decrescente'
    return sorted(processos, key=get_data, reverse=reverse)


def main():
    parser = argparse.ArgumentParser(
        description='Lista processos conclusos no PJE'
    )
    parser.add_argument(
        '--cookies', '-c',
        required=True,
        help='Arquivo JSON com cookies de autenticação'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Arquivo de saída (padrão: processos_<modo>.json)'
    )
    parser.add_argument(
        '--modo', '-m',
        choices=['sentenca', 'decisao'],
        default='sentenca',
        help='Modo: sentenca ou decisao (padrão: sentenca)'
    )
    parser.add_argument(
        '--ordem',
        choices=['crescente', 'decrescente'],
        default='crescente',
        help='Ordem por data de conclusão (padrão: crescente)'
    )
    parser.add_argument(
        '--limite', '-l',
        type=int,
        default=0,
        help='Limitar quantidade de processos (0 = todos)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostra output detalhado (padrao: output minimo)'
    )

    # Filtros de etiquetas
    parser.add_argument(
        '--tags', '-t',
        nargs='+',
        help='Filtrar por etiquetas (ex: --tags URGENTE LIMINAR)'
    )
    parser.add_argument(
        '--sem-etiqueta',
        action='store_true',
        help='Apenas processos sem etiqueta'
    )
    parser.add_argument(
        '--todas-tags',
        action='store_true',
        help='Exigir TODAS as tags (nao apenas uma)'
    )

    # Filtros de status
    parser.add_argument(
        '--prioridade',
        action='store_true',
        help='Apenas processos prioritarios (idosos, doentes graves, etc)'
    )
    parser.add_argument(
        '--sigiloso',
        action='store_true',
        help='Apenas processos sigilosos'
    )
    parser.add_argument(
        '--liminar',
        action='store_true',
        help='Apenas processos com liminar'
    )
    parser.add_argument(
        '--nao-conferidos',
        action='store_true',
        help='Apenas processos nao conferidos (novos)'
    )
    parser.add_argument(
        '--nao-lidos',
        action='store_true',
        help='Apenas processos nao lidos'
    )

    # Filtros de partes
    parser.add_argument(
        '--polo-ativo',
        help='Filtrar por nome do autor'
    )
    parser.add_argument(
        '--polo-passivo',
        help='Filtrar por nome do reu (ex: --polo-passivo INSS)'
    )
    parser.add_argument(
        '--nome-parte',
        help='Filtrar por nome em qualquer polo'
    )
    parser.add_argument(
        '--cpf-cnpj',
        help='Filtrar por CPF/CNPJ da parte'
    )

    # Filtros de classe/assunto
    parser.add_argument(
        '--classe',
        type=int,
        help='Filtrar por ID da classe judicial'
    )
    parser.add_argument(
        '--assunto',
        help='Filtrar por texto no assunto (ex: --assunto aposentadoria)'
    )

    args = parser.parse_args()

    tarefa = TAREFAS[args.modo]
    output_path = Path(args.output) if args.output else Path(f"processos_{args.modo}.json")
    verbose = args.verbose

    # Construir dicionario de filtros
    filtros = {}

    # Etiquetas
    if args.tags:
        filtros['tags'] = args.tags
    if args.sem_etiqueta:
        filtros['sem_etiqueta'] = True
    if args.todas_tags:
        filtros['todas_tags'] = True

    # Status
    if args.prioridade:
        filtros['prioridade'] = True
    if args.sigiloso:
        filtros['sigiloso'] = True
    if args.liminar:
        filtros['liminar'] = True
    if args.nao_conferidos:
        filtros['conferidos'] = False
    if args.nao_lidos:
        filtros['nao_lidos'] = True

    # Partes
    if args.polo_ativo:
        filtros['polo_ativo'] = args.polo_ativo
    if args.polo_passivo:
        filtros['polo_passivo'] = args.polo_passivo
    if args.nome_parte:
        filtros['nome_parte'] = args.nome_parte
    if args.cpf_cnpj:
        filtros['cpf_cnpj'] = args.cpf_cnpj

    # Classe/Assunto
    if args.classe:
        filtros['classe'] = args.classe
    if args.assunto:
        filtros['assunto'] = args.assunto

    # Cabecalho compacto
    filtros_ativos = [k for k in filtros.keys() if k != 'tags'] + (args.tags or [])
    filtros_str = f" [filtros: {', '.join(filtros_ativos)}]" if filtros_ativos else ""
    print(f"[INICIO] Listando processos ({args.modo}){filtros_str} -> {output_path}")

    dados_auth = carregar_cookies(args.cookies)
    session = criar_sessao(dados_auth)
    processos_raw = listar_processos_conclusos(session, tarefa, filtros)

    if not processos_raw:
        print("[ERRO] Nenhum processo encontrado")
        return 1

    # Extrair metadados
    processos = [extrair_metadados_processo(p) for p in processos_raw]

    # Ordenar
    processos = ordenar_processos(processos, args.ordem)

    # Limitar
    if args.limite > 0:
        processos = processos[:args.limite]

    # Preparar saída
    resultado = {
        'total': len(processos),
        'modo': args.modo,
        'tarefa': tarefa,
        'ordem': args.ordem,
        'filtros_aplicados': filtros if filtros else None,
        'extraido_em': datetime.now().isoformat(),
        'processos': processos
    }

    # Salvar
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)

    # Output compacto
    print(f"[OK] {len(processos)} processos salvos em: {output_path}")

    # Resumo detalhado apenas se verbose
    if verbose:
        print("\n--- Resumo dos processos ---")
        for i, p in enumerate(processos[:10], 1):
            print(f"{i}. {p['numero_cnj']} - {p['classe']}")
        if len(processos) > 10:
            print(f"... e mais {len(processos) - 10} processos")

    return 0


if __name__ == '__main__':
    sys.exit(main())
