# -*- coding: utf-8 -*-
"""
MCP Server: [NOME_TRIBUNAL] - Jurisprudencia

Acesso a jurisprudencia do [NOME_TRIBUNAL_COMPLETO].
Gerado automaticamente pela skill criar-mcp-precedente.

Sintaxe de busca:
[TABELA_BOOLEANOS]
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup
import httpx
import re

# Criar servidor MCP
mcp = FastMCP("[nome_tribunal]_mcp")

# ============================================================
# CONFIGURACAO
# ============================================================

API_URL = "[URL_ENDPOINT]"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "[ACCEPT_HEADER]",
    "Accept-Language": "pt-BR,pt;q=0.9",
    # [HEADERS_ADICIONAIS]
}

# Filtros disponiveis (descobertos na analise)
FILTROS_DISPONIVEIS = {
    # "orgao_julgador": ["1a Turma", "2a Turma", ...],
    # "tipo_documento": ["Acordao", "Decisao", ...],
}


# ============================================================
# CLASSES DE SESSAO (se necessario)
# ============================================================

# [SE requires_session = True]
# class TribunalSession:
#     """Gerencia sessao com o portal."""
#
#     def __init__(self):
#         self.client = httpx.AsyncClient()
#         self.session_token = None
#
#     async def obter_sessao(self):
#         """Obtem token/cookie de sessao."""
#         # Implementar conforme necessidade do tribunal
#         pass
#
#     async def buscar(self, params: dict) -> dict:
#         """Faz busca autenticada."""
#         if not self.session_token:
#             await self.obter_sessao()
#         # Implementar busca
#         pass


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


def _formatar_data(data_str: str) -> str:
    """Converte data para formato brasileiro DD/MM/YYYY."""
    if not data_str:
        return ""
    # Adaptar conforme formato do tribunal
    try:
        if "T" in data_str:  # ISO format
            dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y")
        return data_str
    except Exception:
        return data_str


def _extrair_resultados(response_data: Any) -> List[Dict[str, Any]]:
    """
    Extrai resultados da resposta do tribunal.

    ADAPTAR conforme response_format:
    - JSON: response_data ja e dict
    - HTML: usar BeautifulSoup
    - XML: usar re ou ElementTree
    """
    resultados = []

    # [IMPLEMENTAR EXTRACAO CONFORME FORMATO]
    # Exemplo para JSON:
    # for item in response_data.get("registros", []):
    #     resultados.append({
    #         "numero": item.get("processo", ""),
    #         "tipo": item.get("tipo", ""),
    #         "orgao": item.get("orgaoJulgador", ""),
    #         "relator": item.get("relator", ""),
    #         "data": item.get("dataJulgamento", ""),
    #         "ementa": item.get("ementa", ""),
    #         "url": item.get("link", ""),
    #     })

    return resultados


def _formatar_xml(resultados: List[Dict[str, Any]], tag_raiz: str) -> str:
    """Formata resultados em XML estruturado."""
    if not resultados:
        return f"<{tag_raiz}>\n<mensagem>Nenhum resultado encontrado.</mensagem>\n</{tag_raiz}>"

    linhas = [f'<{tag_raiz} total="{len(resultados)}">']

    for i, r in enumerate(resultados, 1):
        linhas.append(f'  <item indice="{i}">')

        if r.get("tipo"):
            linhas.append(f'    <tipo>{_escape_xml(r["tipo"])}</tipo>')
        if r.get("numero"):
            linhas.append(f'    <numero>{_escape_xml(r["numero"])}</numero>')
        if r.get("orgao"):
            linhas.append(f'    <orgao>{_escape_xml(r["orgao"])}</orgao>')
        if r.get("relator"):
            linhas.append(f'    <relator>{_escape_xml(r["relator"])}</relator>')
        if r.get("data"):
            linhas.append(f'    <data>{_escape_xml(_formatar_data(r["data"]))}</data>')

        ementa = _limpar_html(r.get("ementa", ""))
        ementa = _truncar_texto(ementa)
        linhas.append('    <conteudo>')
        linhas.append(f'      {_escape_xml(ementa)}')
        linhas.append('    </conteudo>')

        if r.get("url"):
            linhas.append(f'    <fonte>{_escape_xml(r["url"])}</fonte>')

        linhas.append('  </item>')

    linhas.append(f"</{tag_raiz}>")
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
        return "Erro: Nao foi possivel conectar ao tribunal."
    return f"Erro: {type(e).__name__}: {str(e)}"


async def _fazer_busca(busca: str, max_resultados: int) -> tuple:
    """Executa a busca no portal e retorna (resultados, total).

    IMPLEMENTAR A BUSCA UMA UNICA VEZ AQUI — buscar_* e gerar_relatorio_*
    apenas chamam esta funcao (padrao dos MCPs reais: TCU, TJSC, HUDOC).
    """
    page_size = min(max_resultados, 100)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # [IMPLEMENTAR REQUISICAO CONFORME ENDPOINT DESCOBERTO NA FASE 1]
        # Exemplo para POST JSON:
        # response = await client.post(
        #     API_URL,
        #     json={"query": busca, "tamanho": page_size},
        #     headers=HEADERS,
        # )
        # [SE O PORTAL SERVIR CHARSET LEGADO — comum em eProc e sistemas antigos:]
        # response.encoding = "iso-8859-1"
        # response.raise_for_status()
        # data = response.json()  # ou response.text para HTML

        data = {}  # Placeholder - implementar

        resultados = _extrair_resultados(data)
        total = len(resultados)  # [OU extrair o total real da resposta]

        # [SE HOUVER PAGINACAO E max_resultados > page_size:]
        # cookies = dict(response.cookies)  # reaproveitar sessao da 1a pagina
        # pages_needed = (max_resultados + page_size - 1) // page_size
        # for page in range(2, pages_needed + 1):
        #     if len(resultados) >= max_resultados:
        #         break
        #     pag_resp = await client.post(PAGINATE_URL, data={...}, cookies=cookies)
        #     resultados.extend(_extrair_resultados(pag_resp.text))

    return resultados[:max_resultados], total


# ============================================================
# PYDANTIC MODELS
# ============================================================

class BuscaInput(BaseModel):
    """Input para busca de jurisprudencia."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    busca: str = Field(
        ...,
        description="Query com sintaxe do tribunal. Ver docstring para operadores.",
        min_length=2,
        max_length=500
    )
    max_resultados: int = Field(
        default=30,
        description="Maximo de resultados (1-100)",
        ge=1,
        le=100
    )
    # [ADICIONAR FILTROS CONFORME DESCOBERTO]
    # orgao_julgador: Optional[str] = Field(default=None, description="Filtro por orgao")

    @field_validator('busca')
    @classmethod
    def validar_busca(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Termo de busca nao pode ser vazio")
        return v.strip()


class RelatorioInput(BaseModel):
    """Input para geracao de relatorio."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    busca: str = Field(
        ...,
        description="Query com sintaxe do tribunal.",
        min_length=2,
        max_length=500
    )
    max_resultados: int = Field(
        default=10,
        description="Maximo de resultados para o relatorio",
        ge=1,
        le=50
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
    name="buscar_[tribunal]",
    annotations={
        "title": "Buscar Jurisprudencia no [NOME_TRIBUNAL]",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def buscar_[tribunal](params: BuscaInput) -> str:
    """
    Busca jurisprudencia no [NOME_TRIBUNAL_COMPLETO].

    SINTAXE DE BUSCA:
    [TABELA_BOOLEANOS]

    EXEMPLOS DE QUERIES:
    [EXEMPLOS_QUERIES]

    Args:
        params (BuscaInput): Parametros validados contendo:
            - busca (str): Query com sintaxe do tribunal
            - max_resultados (int): Maximo de resultados (1-100)

    Returns:
        str: XML estruturado com resultados contendo:
            - tipo: Tipo do documento (Acordao, Decisao, etc)
            - numero: Numero do processo
            - orgao: Orgao julgador
            - relator: Nome do relator
            - data: Data do julgamento
            - conteudo: Ementa/resumo
            - fonte: Link para documento
    """
    try:
        resultados, total = await _fazer_busca(params.busca, params.max_resultados)
        xml = _formatar_xml(resultados, "jurisprudencia_[tribunal]")

        # Adicionar metadados
        meta = f'<!-- Busca: "{params.busca}" | Retornados: {len(resultados)} | Total no portal: {total} -->\n'
        return meta + xml

    except Exception as e:
        return f'<erro>{_handle_error(e)}</erro>'


@mcp.tool(
    name="gerar_relatorio_[tribunal]",
    annotations={
        "title": "Gerar Relatorio de Jurisprudencia do [NOME_TRIBUNAL]",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gerar_relatorio_[tribunal](params: RelatorioInput) -> str:
    """
    Busca jurisprudencia e gera relatorio formatado em Markdown.

    USE ESTA TOOL quando precisar de um relatorio para apresentar.
    Para analise programatica, prefira buscar_[tribunal] que retorna XML.

    A sintaxe e a MESMA de buscar_[tribunal].

    Args:
        params (RelatorioInput): Parametros validados contendo:
            - busca (str): Query com sintaxe do tribunal
            - max_resultados (int): Maximo de resultados (1-50)

    Returns:
        str: Relatorio em Markdown com ementas e metadados
    """
    try:
        resultados, _total = await _fazer_busca(params.busca, params.max_resultados)
        data_hora = datetime.now().strftime("%d/%m/%Y as %H:%M")

        linhas = [
            "# Relatorio de Jurisprudencia - [NOME_TRIBUNAL]",
            "",
            f"**Busca realizada:** `{params.busca}`",
            f"**Data/Hora:** {data_hora}",
            f"**Documentos encontrados:** {len(resultados)}",
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
            relator = r.get("relator", "N/I")
            orgao = r.get("orgao", "")
            data = _formatar_data(r.get("data", ""))

            linhas.extend([
                f"## {i}. {numero}",
                "",
            ])

            if tipo:
                linhas.append(f"**Tipo:** {tipo}")
            linhas.append(f"**Relator:** {relator}")
            if orgao:
                linhas.append(f"**Orgao Julgador:** {orgao}")
            linhas.append(f"**Data:** {data}")
            linhas.append("")

            ementa = _limpar_html(r.get("ementa", ""))
            if ementa:
                ementa = _truncar_texto(ementa, 3000)
                linhas.extend([
                    "### Ementa",
                    "",
                    f"> {ementa}",
                    ""
                ])

            url = r.get("url", "")
            if url:
                linhas.append(f"[Ver documento completo]({url})")
                linhas.append("")

            linhas.extend(["---", ""])

        linhas.extend([
            "",
            f"*Relatorio gerado via MCP [NOME_TRIBUNAL] em {data_hora}*"
        ])

        return "\n".join(linhas)

    except Exception as e:
        return f"**Erro:** {_handle_error(e)}"


@mcp.tool(
    name="listar_filtros_[tribunal]",
    annotations={
        "title": "Listar Filtros Disponiveis no [NOME_TRIBUNAL]",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def listar_filtros_[tribunal]() -> str:
    """
    Lista todos os filtros e parametros disponiveis para busca.

    Returns:
        str: XML estruturado com filtros e operadores
    """
    linhas = ['<filtros_[tribunal]>']

    # Operadores de busca
    linhas.append('  <operadores>')
    linhas.append('    <!-- [OPERADORES_DESCOBERTOS] -->')
    # linhas.append('    <operador codigo="E">Ambos termos. Ex: pensao E morte</operador>')
    # linhas.append('    <operador codigo="OU">Qualquer termo. Ex: bpc OU loas</operador>')
    linhas.append('  </operadores>')

    # Filtros disponiveis
    for filtro, valores in FILTROS_DISPONIVEIS.items():
        linhas.append(f'  <{filtro}>')
        for valor in valores:
            linhas.append(f'    <opcao>{valor}</opcao>')
        linhas.append(f'  </{filtro}>')

    linhas.append('</filtros_[tribunal]>')

    return "\n".join(linhas)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    mcp.run()
