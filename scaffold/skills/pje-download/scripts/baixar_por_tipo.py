#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Baixa documentos de um processo do PJE filtrados por tipo.

Permite download seletivo de apenas documentos relevantes,
economizando tempo e espaço em processos volumosos.

Uso:
    # Baixar apenas petições iniciais
    python baixar_por_tipo.py --cookies pje_session.json --id-processo 2683123 --tipo 12 --output inicial.pdf

    # Baixar múltiplos tipos
    python baixar_por_tipo.py --cookies pje_session.json --id-processo 2683123 --tipos 12,64,837 --output-dir ./tipos/

Tipos PJE comuns:
    12 = Petição inicial
    13 = Alegações Finais
    20 = Contrarrazões
    23 = Embargos de Declaração
    64 = Decisão
    119 = Despacho
    158 = Petição (outras) - inclui Contestação, Réplica
    837 = Laudo de Perícia
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

# Mapeamento de tipos PJE
TIPOS_PJE = {
    12: 'Petição inicial',
    13: 'Alegações Finais',
    20: 'Contrarrazões',
    23: 'Embargos de Declaração',
    28: 'Impugnação aos Embargos',
    64: 'Decisão',
    119: 'Despacho',
    158: 'Petição (outras)',
    466: 'Manifestação (Outras)',
    715: 'Esclarecimento de Perito',
    837: 'Laudo de Perícia',
}

# Tipos relevantes para download seletivo (prioridade)
TIPOS_RELEVANTES = [12, 64, 837, 23, 13, 158, 20, 119, 28, 715, 466]


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


def baixar_por_tipo(session: requests.Session, id_processo: int,
                    tipo_documento: int, codigo_acesso: str = None,
                    id_tarefa: int = None, output_path: Path = None) -> dict:
    """
    Baixa PDF filtrado por tipo de documento.

    Retorna: {'sucesso': bool, 'motivo': str, 'tamanho_mb': float, 'arquivo': str}
    """
    resultado = {'sucesso': False, 'motivo': '', 'tamanho_mb': 0, 'arquivo': ''}

    url_base = f"{BASE_URL}/pje/Processo/ConsultaProcesso/Detalhe/listAutosDigitais.seam"

    params = {'idProcesso': id_processo}
    if codigo_acesso:
        params['ca'] = codigo_acesso
    if id_tarefa:
        params['idTaskInstance'] = id_tarefa

    url_autos = f"{url_base}?{urlencode(params)}"

    try:
        # Acessar página para obter ViewState
        response = session.get(url_autos, timeout=60)
        response.raise_for_status()

        view_state = extrair_view_state(response.text)
        if not view_state:
            resultado['motivo'] = 'viewstate_nao_encontrado'
            return resultado

        # POST com filtro de tipo
        data = {
            'navbar:inativacaoLembreteMsgsOpenedState': '',
            'navbar:cbTipoDocumento': str(tipo_documento),
            'navbar:idDe': '',
            'navbar:idAte': '',
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

        if 'application/pdf' in content_type or response.content[:4] == b'%PDF':
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            size_mb = output_path.stat().st_size / (1024 * 1024)

            if size_mb < 0.001:
                output_path.unlink()
                resultado['motivo'] = 'nenhum_documento_do_tipo'
                return resultado

            resultado['sucesso'] = True
            resultado['tamanho_mb'] = size_mb
            resultado['arquivo'] = str(output_path)
            return resultado

        else:
            if 'text/html' in content_type:
                if 'nenhum documento' in response.text.lower():
                    resultado['motivo'] = 'nenhum_documento_do_tipo'
                elif 'sessão expirada' in response.text.lower():
                    resultado['motivo'] = 'sessao_expirada'
                else:
                    resultado['motivo'] = 'resposta_html_inesperada'
            else:
                resultado['motivo'] = 'content_type_inesperado'

            return resultado

    except requests.exceptions.Timeout:
        resultado['motivo'] = 'timeout'
        return resultado
    except Exception as e:
        resultado['motivo'] = f'erro: {str(e)[:30]}'
        return resultado


def main():
    parser = argparse.ArgumentParser(
        description='Baixa documentos do PJE filtrados por tipo'
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
        '--tipo',
        type=int,
        default=None,
        help='Código do tipo de documento (ex: 12 para Petição inicial)'
    )
    parser.add_argument(
        '--tipos',
        type=str,
        default=None,
        help='Lista de tipos separados por vírgula (ex: 12,64,837)'
    )
    parser.add_argument(
        '--relevantes',
        action='store_true',
        help='Baixar todos os tipos relevantes automaticamente'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Arquivo de saída (para tipo único)'
    )
    parser.add_argument(
        '--output-dir',
        default='./tipos',
        help='Diretório de saída (para múltiplos tipos)'
    )
    parser.add_argument(
        '--delay', '-d',
        type=float,
        default=3.0,
        help='Delay entre downloads em segundos (padrão: 3.0)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostra output detalhado (padrao: output minimo)'
    )

    args = parser.parse_args()

    # Determinar lista de tipos
    tipos_baixar = []

    if args.relevantes:
        tipos_baixar = TIPOS_RELEVANTES.copy()
    elif args.tipos:
        tipos_baixar = [int(t.strip()) for t in args.tipos.split(',')]
    elif args.tipo:
        tipos_baixar = [args.tipo]
    else:
        print("[ERRO] Especifique --tipo, --tipos ou --relevantes")
        return 1

    verbose = args.verbose
    dados_auth = carregar_cookies(args.cookies)
    session = criar_sessao(dados_auth)

    # Obter código de acesso (silencioso)
    codigo_acesso = obter_codigo_acesso(session, args.id_processo, dados_auth)

    # Preparar diretório de saída
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Cabecalho compacto
    print(f"[INICIO] {len(tipos_baixar)} tipos -> {output_dir}")

    resultados = []
    sucesso = 0
    falha = 0
    vazio = 0
    total_mb = 0

    for i, tipo in enumerate(tipos_baixar, 1):
        tipo_nome = TIPOS_PJE.get(tipo, f'tipo_{tipo}')
        tipo_slug = re.sub(r'[^\w\-]', '_', tipo_nome.lower())

        if args.output and len(tipos_baixar) == 1:
            output_path = Path(args.output)
        else:
            output_path = output_dir / f"{tipo_slug}_{tipo}.pdf"

        resultado = baixar_por_tipo(
            session, args.id_processo, tipo,
            codigo_acesso, args.id_tarefa, output_path
        )

        if resultado['sucesso']:
            sucesso += 1
            total_mb += resultado['tamanho_mb']
            # Output compacto: uma linha por tipo
            print(f"[OK] {tipo_nome}: {resultado['tamanho_mb']:.2f}MB")
        elif resultado['motivo'] == 'nenhum_documento_do_tipo':
            vazio += 1
            if verbose:
                print(f"[VAZIO] {tipo_nome}")
        else:
            falha += 1
            print(f"[ERRO] {tipo_nome}: {resultado['motivo']}")

        resultados.append({
            'tipo': tipo,
            'nome': tipo_nome,
            **resultado
        })

        if i < len(tipos_baixar):
            time.sleep(args.delay)

    # Resumo compacto
    print(f"[FIM] {sucesso}/{len(tipos_baixar)} OK, {total_mb:.2f}MB total")
    if vazio > 0:
        print(f"      {vazio} tipos sem documentos")

    # Salvar log (detalhes ficam aqui)
    log_path = output_dir / '_download_tipos_log.json'
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump({
            'data': datetime.now().isoformat(),
            'id_processo': args.id_processo,
            'tipos_solicitados': tipos_baixar,
            'sucesso': sucesso,
            'vazio': vazio,
            'falha': falha,
            'total_mb': total_mb,
            'resultados': resultados
        }, f, indent=2, ensure_ascii=False)

    return 0 if falha == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
