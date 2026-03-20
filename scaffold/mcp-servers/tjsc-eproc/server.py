# -*- coding: utf-8 -*-
"""
MCP Server: TJSC eProc - Jurisprudencia

Acesso a jurisprudencia do Tribunal de Justica de Santa Catarina (TJSC)
via sistema eProc. Endpoint publico, sem autenticacao.

Sintaxe de busca (case-insensitive, acentos ignorados):
  - AND: implicito (espaco entre termos). Ex: pensao morte
  - OR: ou. Ex: bpc ou loas
  - NOT: nao (com ou sem acento). Ex: servidor nao militar
  - Frase exata: "...". Ex: "pensao por morte"
  - Wildcard sufixo: *. Ex: aposentad*
  - Wildcard prefixo: *. Ex: *doenca
  - Proximidade: prox. Ex: contrato prox administrativo

Ref: Tutorial de Pesquisa da Jurisprudencia TJSC (atualizado 06/10/2025)
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
import httpx
import re

# Criar servidor MCP
mcp = FastMCP("tjsc_eproc_mcp")

# ============================================================
# CONFIGURACAO
# ============================================================

BASE_URL = "https://eproc1g.tjsc.jus.br/eproc/externo_controlador.php"
SEARCH_URL = f"{BASE_URL}?acao=jurisprudencia@jurisprudencia/listar_resultados"
PAGINATE_URL = f"{BASE_URL}?acao=jurisprudencia@jurisprudencia/ajax_paginar_resultado"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://eproc1g.tjsc.jus.br",
    "Referer": f"{BASE_URL}?acao=jurisprudencia@jurisprudencia/pesquisar",
}

AJAX_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded",
    "X-Requested-With": "XMLHttpRequest",
}

ORIGENS = {
    "tjsc": "1",
    "turmas_recursais": "3",
    "turmas_uniformizacao": "4",
    "conselho_magistratura": "5",
}

TIPOS_DOCUMENTO = {
    "acordaos": "1",
    "decisoes_monocraticas": "2",
    "despachos_vice": "3",
}

ORDENACAO = {
    "mais_recentes": "1",
    "mais_antigos": "2",
}

CAMPOS_BUSCA = {
    "inteiro_teor": "I",
    "ementa": "E",
    "caput_ementa": "CE",
}


# ============================================================
# FUNCOES AUXILIARES
# ============================================================

def _limpar_html(texto: str) -> str:
    """Remove tags HTML e normaliza espacos."""
    if not texto:
        return ""
    texto = re.sub(r'<[^>]+>', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()


def _truncar_texto(texto: str, max_chars: int = 6000) -> str:
    """Trunca texto preservando fim de frase."""
    if not texto or len(texto) <= max_chars:
        return texto
    texto_truncado = texto[:max_chars]
    ultimo_ponto = texto_truncado.rfind('.')
    if ultimo_ponto > max_chars * 0.8:
        texto_truncado = texto_truncado[:ultimo_ponto + 1]
    return texto_truncado + " [...]"


def _escape_xml(texto: str) -> str:
    """Escapa caracteres especiais para XML."""
    if not texto:
        return ""
    texto = str(texto)
    texto = texto.replace("&", "&amp;")
    texto = texto.replace("<", "&lt;")
    texto = texto.replace(">", "&gt;")
    texto = texto.replace('"', "&quot;")
    return texto


def _extrair_resultados(html: str) -> List[Dict[str, Any]]:
    """Extrai resultados do HTML retornado pelo eProc."""
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".resultadoItem")
    resultados = []

    for item in items:
        record: Dict[str, Any] = {}

        # Tipo documento
        tipo_el = item.select_one(".resValueTipoJurisprudencia")
        if tipo_el:
            record["tipo"] = tipo_el.get_text(strip=True)

        # Processo numero e classe
        proc_label = item.find(class_="resLabel", string=re.compile("PROCESSO"))
        if proc_label:
            proc_val = proc_label.find_next_sibling(class_="resValue")
            if proc_val:
                link = proc_val.select_one("a")
                if link:
                    record["numero"] = link.get_text(strip=True)
                classe_span = proc_val.select_one("span")
                if classe_span:
                    classe_text = classe_span.get_text(strip=True)
                    # Remove prefix like "AI - " and clean
                    classe_text = re.sub(r'^\s*\w+\s*-\s*', '', classe_text).strip()
                    if classe_text:
                        record["classe"] = classe_text

        # Label-value pairs
        labels = item.select(".resLabel")
        for label in labels:
            key = label.get_text(strip=True)
            value_el = label.find_next_sibling(class_="resValue")
            if not value_el:
                continue
            value = value_el.get_text(strip=True)

            if key == "PROCESSO":
                continue  # Already handled
            elif key == "UF":
                record["uf"] = value
            elif key == "ÓRGÃO JULGADOR":
                record["orgao"] = value
            elif key == "DATA DO JULGAMENTO":
                record["data_julgamento"] = value
            elif key == "DATA DA PUBLICAÇÃO":
                record["data_publicacao"] = value
            elif key == "RELATOR":
                record["relator"] = value
            elif key in ("DECISÃO", "EMENTA", "ACÓRDÃO"):
                record["conteudo_tipo"] = key.title()
                record["ementa"] = value

        resultados.append(record)

    return resultados


def _extrair_total(html: str) -> int:
    """Extrai total de resultados do HTML."""
    match = re.search(r'name="hdnTotalResultado"\s+value="(\d+)"', html)
    if match:
        return int(match.group(1))
    match = re.search(r'(\d+)\s*documentos?\s*encontrados', html)
    return int(match.group(1)) if match else 0


def _formatar_xml(resultados: List[Dict[str, Any]], total: int) -> str:
    """Formata resultados em XML estruturado."""
    if not resultados:
        return "<jurisprudencia_tjsc>\n<mensagem>Nenhum resultado encontrado.</mensagem>\n</jurisprudencia_tjsc>"

    linhas = [f'<jurisprudencia_tjsc total="{total}" exibidos="{len(resultados)}">']

    for i, r in enumerate(resultados, 1):
        linhas.append(f'  <item indice="{i}">')

        if r.get("tipo"):
            linhas.append(f'    <tipo>{_escape_xml(r["tipo"])}</tipo>')
        if r.get("numero"):
            linhas.append(f'    <numero>{_escape_xml(r["numero"])}</numero>')
        if r.get("classe"):
            linhas.append(f'    <classe>{_escape_xml(r["classe"])}</classe>')
        if r.get("orgao"):
            linhas.append(f'    <orgao>{_escape_xml(r["orgao"])}</orgao>')
        if r.get("relator"):
            linhas.append(f'    <relator>{_escape_xml(r["relator"])}</relator>')
        if r.get("data_julgamento"):
            linhas.append(f'    <data_julgamento>{_escape_xml(r["data_julgamento"])}</data_julgamento>')
        if r.get("data_publicacao"):
            linhas.append(f'    <data_publicacao>{_escape_xml(r["data_publicacao"])}</data_publicacao>')

        ementa = _limpar_html(r.get("ementa", ""))
        ementa = _truncar_texto(ementa)
        if ementa:
            linhas.append("    <conteudo>")
            linhas.append(f"      {_escape_xml(ementa)}")
            linhas.append("    </conteudo>")

        linhas.append("  </item>")

    linhas.append("</jurisprudencia_tjsc>")
    return "\n".join(linhas)


def _handle_error(e: Exception) -> str:
    """Formatacao consistente de erros."""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 404:
            return "Erro: Recurso nao encontrado."
        elif status == 403:
            return "Erro: Acesso negado."
        elif status == 429:
            return "Erro: Limite de requisicoes excedido. Aguarde."
        elif status >= 500:
            return f"Erro: Servidor indisponivel (HTTP {status})"
        return f"Erro: Falha na requisicao (HTTP {status})"
    elif isinstance(e, httpx.TimeoutException):
        return "Erro: Timeout na requisicao. Tente novamente."
    elif isinstance(e, httpx.ConnectError):
        return "Erro: Nao foi possivel conectar ao TJSC."
    return f"Erro: {type(e).__name__}: {str(e)}"


async def _fazer_busca(
    busca: str,
    max_resultados: int = 30,
    origem: Optional[str] = None,
    tipo_documento: Optional[str] = None,
    campo: str = "I",
    ordenacao: str = "1",
    data_decisao_inicio: Optional[str] = None,
    data_decisao_fim: Optional[str] = None,
    data_publicacao_inicio: Optional[str] = None,
    data_publicacao_fim: Optional[str] = None,
    processo: Optional[str] = None,
    classe_processual: Optional[str] = None,
    orgao_julgador: Optional[str] = None,
    relator: Optional[str] = None,
    jurisprudencia_selecionada: bool = False,
    agrupar_resultados: bool = False,
) -> tuple[List[Dict[str, Any]], int]:
    """Executa busca e retorna (resultados, total)."""

    # Determine page size (max 100 per request)
    page_size = min(max_resultados, 100)

    form_data: Dict[str, Any] = {
        "txtPesquisa": busca,
        "selOrdenacao": ordenacao,
        "selTamanhoPagina": str(page_size),
        "rdoCampo": campo,
    }

    if origem and origem in ORIGENS:
        form_data["selOrigem[]"] = ORIGENS[origem]
    if tipo_documento and tipo_documento in TIPOS_DOCUMENTO:
        form_data["selTipoDocumento[]"] = TIPOS_DOCUMENTO[tipo_documento]
    if data_decisao_inicio:
        form_data["dtDecisaoInicio"] = data_decisao_inicio
    if data_decisao_fim:
        form_data["dtDecisaoFim"] = data_decisao_fim
    if data_publicacao_inicio:
        form_data["dtDisponibilizacaoInicio"] = data_publicacao_inicio
    if data_publicacao_fim:
        form_data["dtDisponibilizacaoFim"] = data_publicacao_fim
    if processo:
        form_data["txtProcesso"] = processo
    if classe_processual:
        form_data["selClasseProcessual"] = classe_processual
    if orgao_julgador:
        form_data["selOrgaoJulgador"] = orgao_julgador
    if relator:
        form_data["selRelator"] = relator
    if jurisprudencia_selecionada:
        form_data["chkJurisprudenciaSelecionada"] = "1"
    if agrupar_resultados:
        form_data["chkAgruparResultados"] = "1"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # First page (full page load)
        resp = await client.post(SEARCH_URL, headers=HEADERS, data=form_data)
        resp.encoding = "iso-8859-1"
        resp.raise_for_status()

        html = resp.text
        total = _extrair_total(html)
        resultados = _extrair_resultados(html)

        # If we need more results, paginate
        pages_needed = (max_resultados + page_size - 1) // page_size
        cookies = dict(resp.cookies)

        for page in range(2, pages_needed + 1):
            if len(resultados) >= max_resultados:
                break

            pag_data = {
                "hdnPaginaAtual": str(page),
                "selTamanhoPagina": str(page_size),
            }
            pag_resp = await client.post(
                PAGINATE_URL,
                headers=AJAX_HEADERS,
                data=pag_data,
                cookies=cookies,
            )
            pag_resp.encoding = "iso-8859-1"
            if pag_resp.status_code == 200:
                page_results = _extrair_resultados(pag_resp.text)
                resultados.extend(page_results)
            else:
                break

    return resultados[:max_resultados], total


# ============================================================
# PYDANTIC MODELS
# ============================================================

class BuscaInput(BaseModel):
    """Input para busca de jurisprudencia no TJSC."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    busca: str = Field(
        ...,
        description=(
            "Query com sintaxe do TJSC eProc (case-insensitive, acentos ignorados). "
            "Operadores: AND (implicito/espaco), ou (OR), nao/não (NOT), "
            '"..." (frase exata), * (wildcard), prox (proximidade). '
            "Exemplos: "
            '"pensão por morte", aposentad* ou reforma*, servidor nao militar'
        ),
        min_length=2,
        max_length=500
    )
    max_resultados: int = Field(
        default=30,
        description="Maximo de resultados (1-100)",
        ge=1,
        le=100
    )
    origem: Optional[str] = Field(
        default=None,
        description="Filtro por origem: tjsc, turmas_recursais, turmas_uniformizacao, conselho_magistratura"
    )
    tipo_documento: Optional[str] = Field(
        default=None,
        description="Filtro por tipo: acordaos, decisoes_monocraticas, despachos_vice"
    )
    campo: Optional[str] = Field(
        default="I",
        description="Campo de busca: I=Inteiro Teor (padrao), E=Ementa, CE=Caput da Ementa"
    )
    ordenacao: Optional[str] = Field(
        default="1",
        description="Ordenacao: 1=mais recentes (padrao), 2=mais antigos"
    )
    data_inicio: Optional[str] = Field(
        default=None,
        description="Data decisao/julgamento inicio (DD/MM/AAAA)"
    )
    data_fim: Optional[str] = Field(
        default=None,
        description="Data decisao/julgamento fim (DD/MM/AAAA)"
    )
    data_publicacao_inicio: Optional[str] = Field(
        default=None,
        description="Data disponibilizacao/publicacao inicio (DD/MM/AAAA)"
    )
    data_publicacao_fim: Optional[str] = Field(
        default=None,
        description="Data disponibilizacao/publicacao fim (DD/MM/AAAA)"
    )
    processo: Optional[str] = Field(
        default=None,
        description="Numero do processo (formato CNJ ou apenas digitos)"
    )
    classe_processual: Optional[str] = Field(
        default=None,
        description="Classe processual para restringir a busca"
    )
    orgao_julgador: Optional[str] = Field(
        default=None,
        description="Orgao julgador para restringir a busca"
    )
    relator: Optional[str] = Field(
        default=None,
        description="Nome do Relator/Relatora para filtrar"
    )
    jurisprudencia_selecionada: bool = Field(
        default=False,
        description="Filtrar apenas precedentes relevantes (jurisprudencia selecionada pelo TJSC)"
    )
    agrupar_resultados: bool = Field(
        default=False,
        description="Agrupar resultados semelhantes (mesma relatoria, classe e ementa), exibindo o mais atual"
    )

    @field_validator('busca')
    @classmethod
    def validar_busca(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Termo de busca nao pode ser vazio")
        return v.strip()


class RelatorioInput(BaseModel):
    """Input para geracao de relatorio do TJSC."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    busca: str = Field(
        ...,
        description="Query com sintaxe do TJSC eProc (mesma de buscar_tjsc).",
        min_length=2,
        max_length=500
    )
    max_resultados: int = Field(
        default=10,
        description="Maximo de resultados para o relatorio (1-50)",
        ge=1,
        le=50
    )
    tipo_documento: Optional[str] = Field(
        default=None,
        description="Filtro por tipo: acordaos, decisoes_monocraticas, despachos_vice"
    )

    @field_validator('busca')
    @classmethod
    def validar_busca(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Termo de busca nao pode ser vazio")
        return v.strip()


# ============================================================
# TOOLS
# ============================================================

@mcp.tool(
    name="buscar_tjsc",
    annotations={
        "title": "Buscar Jurisprudencia no TJSC",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def buscar_tjsc(params: BuscaInput) -> str:
    """
    Busca jurisprudencia no Tribunal de Justica de Santa Catarina (TJSC)
    via sistema eProc (1o Grau).

    SINTAXE DE BUSCA (case-insensitive, acentos ignorados):
    | Operador    | Sintaxe      | Exemplo                          |
    |-------------|--------------|----------------------------------|
    | AND         | (espaco)     | pensao morte                     |
    | OR          | ou           | bpc ou loas                      |
    | NOT         | nao / não    | servidor nao militar             |
    | Frase exata | "..."        | "pensao por morte"               |
    | Wildcard    | *            | aposentad* (sufixo) ou *doenca   |
    | Proximidade | prox         | contrato prox administrativo     |

    FILTROS DISPONIVEIS:
    - origem: tjsc, turmas_recursais, turmas_uniformizacao, conselho_magistratura
    - tipo_documento: acordaos, decisoes_monocraticas, despachos_vice
    - campo: I (inteiro teor), E (ementa), CE (caput da ementa)
    - ordenacao: 1 (mais recentes), 2 (mais antigos)
    - data_inicio/data_fim: DD/MM/AAAA (data decisao/julgamento)
    - data_publicacao_inicio/data_publicacao_fim: DD/MM/AAAA
    - processo: numero do processo (CNJ ou digitos)
    - classe_processual, orgao_julgador, relator: filtros especificos
    - jurisprudencia_selecionada: true para precedentes relevantes
    - agrupar_resultados: true para agrupar semelhantes

    Args:
        params: Parametros de busca validados.

    Returns:
        str: XML estruturado com resultados.
    """
    try:
        resultados, total = await _fazer_busca(
            busca=params.busca,
            max_resultados=params.max_resultados,
            origem=params.origem,
            tipo_documento=params.tipo_documento,
            campo=params.campo or "I",
            ordenacao=params.ordenacao or "1",
            data_decisao_inicio=params.data_inicio,
            data_decisao_fim=params.data_fim,
            data_publicacao_inicio=params.data_publicacao_inicio,
            data_publicacao_fim=params.data_publicacao_fim,
            processo=params.processo,
            classe_processual=params.classe_processual,
            orgao_julgador=params.orgao_julgador,
            relator=params.relator,
            jurisprudencia_selecionada=params.jurisprudencia_selecionada,
            agrupar_resultados=params.agrupar_resultados,
        )

        xml = _formatar_xml(resultados, total)
        meta = f'<!-- Busca: "{params.busca}" | Total: {total} | Exibidos: {len(resultados)} -->\n'
        return meta + xml

    except Exception as e:
        return f"<erro>{_handle_error(e)}</erro>"


@mcp.tool(
    name="gerar_relatorio_tjsc",
    annotations={
        "title": "Gerar Relatorio de Jurisprudencia do TJSC",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gerar_relatorio_tjsc(params: RelatorioInput) -> str:
    """
    Busca jurisprudencia no TJSC e gera relatorio formatado em Markdown.

    USE ESTA TOOL quando precisar de um relatorio para apresentar.
    Para analise programatica, prefira buscar_tjsc que retorna XML.

    A sintaxe e a MESMA de buscar_tjsc.

    Args:
        params: Parametros de busca validados.

    Returns:
        str: Relatorio em Markdown.
    """
    try:
        resultados, total = await _fazer_busca(
            busca=params.busca,
            max_resultados=params.max_resultados,
            tipo_documento=params.tipo_documento,
        )

        data_hora = datetime.now().strftime("%d/%m/%Y as %H:%M")

        linhas = [
            "# Relatorio de Jurisprudencia - TJSC (eProc)",
            "",
            f"**Busca realizada:** `{params.busca}`",
            f"**Data/Hora:** {data_hora}",
            f"**Documentos encontrados:** {total}",
            f"**Documentos exibidos:** {len(resultados)}",
            "",
            "---",
            ""
        ]

        if not resultados:
            linhas.append("*Nenhum documento encontrado.*")
            return "\n".join(linhas)

        for i, r in enumerate(resultados, 1):
            numero = r.get("numero", "N/I")
            tipo = r.get("tipo", "")
            classe = r.get("classe", "")
            relator = r.get("relator", "N/I")
            orgao = r.get("orgao", "")
            data_julg = r.get("data_julgamento", "")
            data_pub = r.get("data_publicacao", "")

            titulo = numero
            if classe:
                titulo += f" ({classe})"

            linhas.extend([
                f"## {i}. {titulo}",
                "",
            ])

            if tipo:
                linhas.append(f"**Tipo:** {tipo}")
            linhas.append(f"**Relator:** {relator}")
            if orgao:
                linhas.append(f"**Orgao Julgador:** {orgao}")
            if data_julg:
                linhas.append(f"**Data Julgamento:** {data_julg}")
            if data_pub:
                linhas.append(f"**Data Publicacao:** {data_pub}")
            linhas.append("")

            ementa = _limpar_html(r.get("ementa", ""))
            if ementa:
                ementa = _truncar_texto(ementa, 3000)
                linhas.extend([
                    f"### {r.get('conteudo_tipo', 'Conteudo')}",
                    "",
                    f"> {ementa}",
                    ""
                ])

            linhas.extend(["---", ""])

        linhas.extend([
            "",
            f"*Relatorio gerado via MCP TJSC eProc em {data_hora}*"
        ])

        return "\n".join(linhas)

    except Exception as e:
        return f"**Erro:** {_handle_error(e)}"


@mcp.tool(
    name="listar_filtros_tjsc",
    annotations={
        "title": "Listar Filtros Disponiveis no TJSC",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def listar_filtros_tjsc() -> str:
    """
    Lista todos os filtros, parametros e operadores disponiveis
    para busca de jurisprudencia no TJSC eProc.

    Returns:
        str: XML estruturado com filtros e operadores.
    """
    linhas = ['<filtros_tjsc>']

    # Operadores
    linhas.append('  <operadores nota="Case-insensitive. Acentos ignorados na busca.">')
    linhas.append('    <operador sintaxe="(espaco)">AND implicito. Ex: pensao morte</operador>')
    linhas.append('    <operador sintaxe="ou">OR. Ex: bpc ou loas</operador>')
    linhas.append('    <operador sintaxe="nao">NOT (com ou sem acento). Ex: servidor nao militar</operador>')
    linhas.append('    <operador sintaxe="&quot;...&quot;">Frase exata. Ex: "pensao por morte"</operador>')
    linhas.append('    <operador sintaxe="*">Wildcard sufixo/prefixo. Ex: aposentad* ou *doenca</operador>')
    linhas.append('    <operador sintaxe="prox">Proximidade (qualquer ordem). Ex: contrato prox administrativo</operador>')
    linhas.append('  </operadores>')

    # Origens
    linhas.append('  <origem>')
    for key, val in ORIGENS.items():
        linhas.append(f'    <opcao codigo="{key}" valor="{val}">{key}</opcao>')
    linhas.append('  </origem>')

    # Tipos documento
    linhas.append('  <tipo_documento>')
    for key, val in TIPOS_DOCUMENTO.items():
        linhas.append(f'    <opcao codigo="{key}" valor="{val}">{key}</opcao>')
    linhas.append('  </tipo_documento>')

    # Campo busca
    linhas.append('  <campo_busca>')
    linhas.append('    <opcao codigo="I">Inteiro Teor (padrao)</opcao>')
    linhas.append('    <opcao codigo="E">Ementa</opcao>')
    linhas.append('    <opcao codigo="CE">Caput da Ementa</opcao>')
    linhas.append('  </campo_busca>')

    # Ordenacao
    linhas.append('  <ordenacao>')
    linhas.append('    <opcao codigo="1">Mais recentes (padrao)</opcao>')
    linhas.append('    <opcao codigo="2">Mais antigos</opcao>')
    linhas.append('  </ordenacao>')

    # Datas
    linhas.append('  <datas formato="DD/MM/AAAA">')
    linhas.append('    <campo nome="data_inicio">Data decisao/julgamento inicio</campo>')
    linhas.append('    <campo nome="data_fim">Data decisao/julgamento fim</campo>')
    linhas.append('    <campo nome="data_publicacao_inicio">Data disponibilizacao/publicacao inicio</campo>')
    linhas.append('    <campo nome="data_publicacao_fim">Data disponibilizacao/publicacao fim</campo>')
    linhas.append('  </datas>')

    # Campos especificos
    linhas.append('  <campos_especificos>')
    linhas.append('    <campo nome="processo">Numero do processo (CNJ ou digitos)</campo>')
    linhas.append('    <campo nome="classe_processual">Classe processual</campo>')
    linhas.append('    <campo nome="orgao_julgador">Orgao julgador (colegiado)</campo>')
    linhas.append('    <campo nome="relator">Nome do Relator/Relatora</campo>')
    linhas.append('  </campos_especificos>')

    # Opcoes booleanas
    linhas.append('  <opcoes_booleanas>')
    linhas.append('    <opcao nome="jurisprudencia_selecionada">Apenas precedentes relevantes selecionados pelo TJSC</opcao>')
    linhas.append('    <opcao nome="agrupar_resultados">Agrupar resultados semelhantes (mesma relatoria/classe/ementa)</opcao>')
    linhas.append('  </opcoes_booleanas>')

    linhas.append('</filtros_tjsc>')

    return "\n".join(linhas)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    mcp.run()
