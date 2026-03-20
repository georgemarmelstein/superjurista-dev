# -*- coding: utf-8 -*-
"""
MCP Server: TCU Jurisprudencia

Acesso a jurisprudencia do Tribunal de Contas da Uniao (TCU).
Inclui: Acordaos, Jurisprudencia Selecionada, Normas, Sumulas.

Sintaxe de busca (operadores em MINUSCULO):
- e       : Ambos termos obrigatorios. Ex: licitacao e fraude
- ou      : Qualquer termo. Ex: pregao ou concorrencia
- nao     : Exclui termo. Ex: contrato nao emergencial
- adj     : Adjacentes na ordem. Ex: tomada adj contas
- prox    : Proximos (qualquer ordem). Ex: dano prox erario
- mesmo   : No mesmo paragrafo. Ex: multa mesmo gestor
- $       : Wildcard sufixo. Ex: aposentad$ -> aposentadoria, aposentado
- "..."   : Frase exata. Ex: "tomada de contas especial"
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
import httpx
import re
import urllib.parse

# Criar servidor MCP
mcp = FastMCP("tcu-jurisprudencia")

# ============================================================
# CONFIGURACAO
# ============================================================

BASE_URL = "https://pesquisa.apps.tcu.gov.br/rest/publico"

# Bases disponiveis no TCU
BASES_DISPONIVEIS = {
    "acordao-completo": {
        "nome": "Acordaos Completos",
        "descricao": "Todos os acordaos do TCU com inteiro teor",
        "ordenacao_padrao": "DTRELEVANCIA desc, NUMACORDAOINT desc"
    },
    "jurisprudencia-selecionada": {
        "nome": "Jurisprudencia Selecionada",
        "descricao": "Ementas e sumulas selecionadas pela Secretaria de Jurisprudencia, organizadas por tema",
        "ordenacao_padrao": "score desc, COLEGIADO asc, ANOACORDAO desc, NUMACORDAO desc"
    },
    "norma": {
        "nome": "Normas",
        "descricao": "Normativos internos do TCU (Portarias, Resolucoes, Instrucoes)",
        "ordenacao_padrao": "score desc"
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "origem": "angular",
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


def _formatar_data(data_str: str) -> str:
    """Converte data para formato brasileiro DD/MM/YYYY."""
    if not data_str:
        return ""
    try:
        if "T" in data_str:
            dt = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            return dt.strftime("%d/%m/%Y")
        # Formato YYYYMMDD
        if len(data_str) == 8 and data_str.isdigit():
            return f"{data_str[6:8]}/{data_str[4:6]}/{data_str[0:4]}"
        return data_str
    except Exception:
        return data_str


def _extrair_resultados_acordao(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrai resultados de acordaos."""
    resultados = []
    documentos = data.get("documentos", [])

    for doc in documentos:
        # Campos reais da API do TCU
        colegiado = doc.get("COLEGIADO", "")
        resultado = {
            "tipo": "Acordao",
            "numero": f"Acordao {doc.get('NUMACORDAO', '')}/{doc.get('ANOACORDAO', '')} - {colegiado}",
            "orgao": colegiado,
            "relator": doc.get("RELATOR", ""),
            "data": doc.get("DATASESSAO", ""),
            "ementa": _limpar_html(doc.get("SUMARIO", "") or doc.get("FRAGMENTO1", "")),
            "url": doc.get("URLARQUIVOPDF", "") or doc.get("URLARQUIVO", ""),
            "processo": doc.get("PROC", ""),
            "situacao": doc.get("SITUACAO", ""),
        }
        resultados.append(resultado)

    return resultados


def _extrair_resultados_jurisprudencia(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrai resultados de jurisprudencia selecionada."""
    resultados = []
    documentos = data.get("documentos", [])

    for doc in documentos:
        # Campos reais da API do TCU
        num_sumula = doc.get("NUMSUMULA", "")
        num_acordao = doc.get("NUMACORDAO", "")
        ano = doc.get("ANOACORDAO", "")
        colegiado = doc.get("COLEGIADO", "")

        if num_sumula:
            numero = f"Sumula TCU {num_sumula}"
        elif num_acordao:
            numero = f"Acordao {num_acordao}/{ano} - {colegiado}"
        else:
            numero = doc.get("KEY", "")

        resultado = {
            "tipo": "Jurisprudencia Selecionada",
            "numero": numero,
            "orgao": colegiado,
            "relator": doc.get("AUTORTESE", ""),
            "data": doc.get("DATASESSAOFORMATADA", ""),
            "ementa": _limpar_html(doc.get("ENUNCIADO", "")),
            "url": "",  # Jurisprudencia selecionada nao tem link direto
            "area": _limpar_html(doc.get("AREA", "")),
            "tema": _limpar_html(doc.get("TEMA", "")),
            "subtema": _limpar_html(doc.get("SUBTEMA", "")),
            "paradigmatico": doc.get("PARADIGMATICO", ""),
        }
        resultados.append(resultado)

    return resultados


def _extrair_resultados_norma(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extrai resultados de normas."""
    resultados = []
    documentos = data.get("documentos", [])

    for doc in documentos:
        # Campos reais da API do TCU
        tipo_norma = doc.get("TIPONORMA", "") or doc.get("TIPO", "Norma")
        origem = doc.get("ORIGEM", [])
        if isinstance(origem, list):
            origem = ", ".join(origem) if origem else "TCU"

        resultado = {
            "tipo": tipo_norma,
            "numero": doc.get("TITULO", "") or f"{tipo_norma} {doc.get('NUMNORMA', '')}/{doc.get('ANONORMA', '')}",
            "orgao": origem,
            "situacao": doc.get("SITUACAO", ""),
            "data": doc.get("DATANORMA", ""),
            "ementa": _limpar_html(doc.get("ASSUNTO", "") or doc.get("FRAGMENTO1", "")),
            "url": doc.get("LINKBTCU", ""),
            "tema": doc.get("TEMA", ""),
        }
        resultados.append(resultado)

    return resultados


def _extrair_resultados(data: Dict[str, Any], base: str) -> List[Dict[str, Any]]:
    """Extrai resultados conforme a base consultada."""
    if base == "acordao-completo":
        return _extrair_resultados_acordao(data)
    elif base == "jurisprudencia-selecionada":
        return _extrair_resultados_jurisprudencia(data)
    elif base == "norma":
        return _extrair_resultados_norma(data)
    else:
        return _extrair_resultados_acordao(data)


def _formatar_xml(resultados: List[Dict[str, Any]], tag_raiz: str, total_encontrado: int) -> str:
    """Formata resultados em XML estruturado."""
    if not resultados:
        return f"<{tag_raiz} total=\"0\">\n<mensagem>Nenhum resultado encontrado.</mensagem>\n</{tag_raiz}>"

    linhas = [f'<{tag_raiz} total="{total_encontrado}" exibidos="{len(resultados)}">']

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
            linhas.append(f'    <data>{_escape_xml(r["data"])}</data>')
        if r.get("situacao"):
            linhas.append(f'    <situacao>{_escape_xml(r["situacao"])}</situacao>')
        if r.get("processo"):
            linhas.append(f'    <processo>{_escape_xml(r["processo"])}</processo>')
        if r.get("classe"):
            linhas.append(f'    <classe>{_escape_xml(r["classe"])}</classe>')
        if r.get("area"):
            linhas.append(f'    <area>{_escape_xml(r["area"])}</area>')
        if r.get("tema"):
            linhas.append(f'    <tema>{_escape_xml(r["tema"])}</tema>')

        ementa = _truncar_texto(r.get("ementa", ""))
        if ementa:
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
        if status == 422:
            return "Erro: Argumentos de pesquisa invalidos. Verifique a sintaxe."
        elif status == 404:
            return "Erro: Recurso nao encontrado."
        elif status == 403:
            return "Erro: Acesso negado."
        elif status == 429:
            return "Erro: Limite de requisicoes excedido. Aguarde."
        elif status >= 500:
            return f"Erro: Servidor TCU indisponivel (HTTP {status})"
        return f"Erro: Falha na requisicao (HTTP {status})"
    elif isinstance(e, httpx.TimeoutException):
        return "Erro: Timeout na requisicao. Tente novamente."
    elif isinstance(e, httpx.ConnectError):
        return "Erro: Nao foi possivel conectar ao TCU."
    return f"Erro: {type(e).__name__}: {str(e)}"


# ============================================================
# PYDANTIC MODELS
# ============================================================

class BuscaTCUInput(BaseModel):
    """Input para busca de jurisprudencia no TCU."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    busca: str = Field(
        ...,
        description="Query com sintaxe do TCU. Operadores em minusculo: e, ou, nao, adj, prox, mesmo, $",
        min_length=2,
        max_length=500
    )
    base: Literal["acordao-completo", "jurisprudencia-selecionada", "norma"] = Field(
        default="acordao-completo",
        description="Base de dados: acordao-completo, jurisprudencia-selecionada, norma"
    )
    max_resultados: int = Field(
        default=30,
        description="Maximo de resultados (1-100)",
        ge=1,
        le=100
    )
    sinonimos: bool = Field(
        default=True,
        description="Expandir busca com sinonimos"
    )

    @field_validator('busca')
    @classmethod
    def validar_busca(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Termo de busca nao pode ser vazio")
        return v.strip()


class RelatorioTCUInput(BaseModel):
    """Input para geracao de relatorio do TCU."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    busca: str = Field(
        ...,
        description="Query com sintaxe do TCU.",
        min_length=2,
        max_length=500
    )
    base: Literal["acordao-completo", "jurisprudencia-selecionada", "norma"] = Field(
        default="acordao-completo",
        description="Base de dados a consultar"
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
    name="buscar_tcu",
    annotations={
        "title": "Buscar Jurisprudencia no TCU",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def buscar_tcu(params: BuscaTCUInput) -> str:
    """
    Busca jurisprudencia no Tribunal de Contas da Uniao (TCU).

    O TCU e o orgao de controle externo que fiscaliza a aplicacao de recursos federais.
    Sua jurisprudencia e referencia para licitacoes, contratos administrativos,
    responsabilizacao de gestores e tomada de contas especial.

    SINTAXE DE BUSCA (operadores em MINUSCULO):
    +----------+--------------------------------+----------------------------------+
    | Operador | Descricao                      | Exemplo                          |
    +----------+--------------------------------+----------------------------------+
    | e        | Ambos termos obrigatorios      | licitacao e fraude               |
    | ou       | Qualquer um dos termos         | pregao ou concorrencia           |
    | nao      | Exclui o segundo termo         | contrato nao emergencial         |
    | adj      | Adjacentes NA ordem            | tomada adj contas                |
    | prox     | Proximos QUALQUER ordem        | dano prox erario                 |
    | mesmo    | No mesmo PARAGRAFO             | multa mesmo gestor               |
    | $        | Wildcard (qualquer sufixo)     | aposentad$ -> aposentadoria      |
    | "..."    | Frase exata                    | "tomada de contas especial"      |
    +----------+--------------------------------+----------------------------------+

    BASES DISPONIVEIS:
    - acordao-completo: Todos os acordaos com inteiro teor (DEFAULT)
    - jurisprudencia-selecionada: Ementas organizadas por tema
    - sumula: Sumulas do TCU
    - norma: Normativos internos (Portarias, Resolucoes)

    EXEMPLOS DE QUERIES:
    - licitacao e fraude e "pregao eletronico"
    - "tomada de contas especial" e (dano ou prejuizo) e erario
    - servidor e acumulacao nao cargo
    - aposentad$ prox invalidez
    - contrato adj administrativo e inexigibilidade

    TEMAS COMUNS NO TCU:
    - Licitacoes e contratos
    - Tomada de contas especial
    - Responsabilizacao de gestores
    - Convenios e transferencias
    - Pessoal e aposentadoria
    - Obras publicas

    Args:
        params (BuscaTCUInput): Parametros validados contendo:
            - busca (str): Query com sintaxe do TCU (operadores minusculos)
            - base (str): Base de dados (acordao-completo, jurisprudencia-selecionada, sumula, norma)
            - max_resultados (int): Maximo de resultados (1-100)
            - sinonimos (bool): Expandir com sinonimos

    Returns:
        str: XML estruturado com resultados contendo:
            - tipo: Acordao, Jurisprudencia Selecionada, Sumula, Norma
            - numero: Identificacao do documento
            - orgao: Colegiado (Plenario, 1a Camara, 2a Camara)
            - relator: Nome do relator
            - data: Data do julgamento
            - conteudo: Ementa/enunciado
            - fonte: Link para inteiro teor
    """
    try:
        base_info = BASES_DISPONIVEIS.get(params.base, BASES_DISPONIVEIS["acordao-completo"])

        # Construir URL
        url = f"{BASE_URL}/base/{params.base}/documentosResumidos"

        query_params = {
            "termo": params.busca,
            "ordenacao": base_info["ordenacao_padrao"],
            "quantidade": params.max_resultados,
            "inicio": 0,
        }

        if params.base in ["jurisprudencia-selecionada"]:
            query_params["sinonimos"] = str(params.sinonimos).lower()

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=query_params,
                headers=HEADERS,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        total_encontrado = data.get("quantidadeEncontrada", 0)
        resultados = _extrair_resultados(data, params.base)[:params.max_resultados]

        xml = _formatar_xml(resultados, "jurisprudencia_tcu", total_encontrado)

        # Adicionar metadados
        meta = f'<!-- Busca: "{params.busca}" | Base: {params.base} | Total: {total_encontrado} -->\n'
        return meta + xml

    except Exception as e:
        return f'<erro>{_handle_error(e)}</erro>'


@mcp.tool(
    name="gerar_relatorio_tcu",
    annotations={
        "title": "Gerar Relatorio de Jurisprudencia do TCU",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gerar_relatorio_tcu(params: RelatorioTCUInput) -> str:
    """
    Busca jurisprudencia no TCU e gera relatorio formatado em Markdown.

    USE ESTA TOOL quando precisar de um relatorio para apresentar.
    Para analise programatica, prefira buscar_tcu que retorna XML.

    A sintaxe e a MESMA de buscar_tcu:
    - Operadores em minusculo: e, ou, nao, adj, prox, mesmo, $
    - Frase exata entre aspas: "tomada de contas"

    Args:
        params (RelatorioTCUInput): Parametros validados contendo:
            - busca (str): Query com sintaxe do TCU
            - base (str): Base de dados a consultar
            - max_resultados (int): Maximo de resultados (1-50)

    Returns:
        str: Relatorio em Markdown com ementas e metadados
    """
    try:
        base_info = BASES_DISPONIVEIS.get(params.base, BASES_DISPONIVEIS["acordao-completo"])

        url = f"{BASE_URL}/base/{params.base}/documentosResumidos"

        query_params = {
            "termo": params.busca,
            "ordenacao": base_info["ordenacao_padrao"],
            "quantidade": params.max_resultados,
            "inicio": 0,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=query_params,
                headers=HEADERS,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

        total_encontrado = data.get("quantidadeEncontrada", 0)
        resultados = _extrair_resultados(data, params.base)[:params.max_resultados]
        data_hora = datetime.now().strftime("%d/%m/%Y as %H:%M")

        linhas = [
            "# Relatorio de Jurisprudencia - TCU",
            "",
            f"**Busca realizada:** `{params.busca}`",
            f"**Base consultada:** {base_info['nome']}",
            f"**Data/Hora:** {data_hora}",
            f"**Total encontrado:** {total_encontrado}",
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
            relator = r.get("relator", "N/I")
            orgao = r.get("orgao", "")
            data = r.get("data", "")
            situacao = r.get("situacao", "")

            linhas.extend([
                f"## {i}. {numero}",
                "",
            ])

            if tipo:
                linhas.append(f"**Tipo:** {tipo}")
            if relator and relator != "N/I":
                linhas.append(f"**Relator:** {relator}")
            if orgao:
                linhas.append(f"**Orgao Julgador:** {orgao}")
            if data:
                linhas.append(f"**Data:** {data}")
            if situacao:
                linhas.append(f"**Situacao:** {situacao}")
            if r.get("area"):
                linhas.append(f"**Area:** {r['area']}")
            if r.get("tema"):
                linhas.append(f"**Tema:** {r['tema']}")
            linhas.append("")

            ementa = r.get("ementa", "")
            if ementa:
                ementa = _truncar_texto(ementa, 3000)
                linhas.extend([
                    "### Ementa/Enunciado",
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
            f"*Relatorio gerado via MCP TCU-Jurisprudencia em {data_hora}*"
        ])

        return "\n".join(linhas)

    except Exception as e:
        return f"**Erro:** {_handle_error(e)}"


@mcp.tool(
    name="listar_bases_tcu",
    annotations={
        "title": "Listar Bases Disponiveis no TCU",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def listar_bases_tcu() -> str:
    """
    Lista todas as bases de dados e operadores disponiveis para busca no TCU.

    Returns:
        str: XML estruturado com bases e operadores
    """
    linhas = ['<filtros_tcu>']

    # Bases disponiveis
    linhas.append('  <bases>')
    for codigo, info in BASES_DISPONIVEIS.items():
        linhas.append(f'    <base codigo="{codigo}">')
        linhas.append(f'      <nome>{info["nome"]}</nome>')
        linhas.append(f'      <descricao>{info["descricao"]}</descricao>')
        linhas.append(f'    </base>')
    linhas.append('  </bases>')

    # Operadores de busca
    linhas.append('  <operadores>')
    linhas.append('    <operador codigo="e">Ambos termos obrigatorios. Ex: licitacao e fraude</operador>')
    linhas.append('    <operador codigo="ou">Qualquer termo. Ex: pregao ou concorrencia</operador>')
    linhas.append('    <operador codigo="nao">Exclui termo. Ex: contrato nao emergencial</operador>')
    linhas.append('    <operador codigo="adj">Adjacentes na ordem. Ex: tomada adj contas</operador>')
    linhas.append('    <operador codigo="prox">Proximos qualquer ordem. Ex: dano prox erario</operador>')
    linhas.append('    <operador codigo="mesmo">No mesmo paragrafo. Ex: multa mesmo gestor</operador>')
    linhas.append('    <operador codigo="$">Wildcard sufixo. Ex: aposentad$ (aposentadoria, aposentado)</operador>')
    linhas.append('    <operador codigo="aspas">Frase exata. Ex: "tomada de contas especial"</operador>')
    linhas.append('  </operadores>')

    # Colegiados
    linhas.append('  <colegiados>')
    linhas.append('    <colegiado>Plenario</colegiado>')
    linhas.append('    <colegiado>1a Camara</colegiado>')
    linhas.append('    <colegiado>2a Camara</colegiado>')
    linhas.append('  </colegiados>')

    linhas.append('</filtros_tcu>')

    return "\n".join(linhas)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    mcp.run()
