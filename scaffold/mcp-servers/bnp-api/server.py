# -*- coding: utf-8 -*-
"""
MCP Server: BNP/CNJ - Banco Nacional de Precedentes

Acesso a precedentes qualificados do Banco Nacional de Precedentes (BNP)
do Conselho Nacional de Justica (CNJ), incluindo sumulas, temas de
repercussao geral, recursos repetitivos, IRDRs e demais precedentes
vinculantes de todos os tribunais brasileiros.

Plataforma: Pangea/BNP (https://bnp.pdpj.jus.br)
Backend: Flask + OpenSearch (gunicorn)
Frontend: Angular 16

Sintaxe de busca (OpenSearch/Lucene):
  +termo        palavra obrigatoria
  -termo        excluir palavra
  "frase exata" busca por frase exata
  termo1 termo2 busca por qualquer um dos termos (OR implicito)

Exemplos:
  "pensao por morte"           frase exata
  +aposentadoria +especial     ambas obrigatorias
  previdenciario -militar      com exclusao
  "dano moral" +consumidor     combinando frase exata e obrigatoria
"""

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
import httpx
import re

# Criar servidor MCP
mcp = FastMCP("bnp_api")

# ============================================================
# CONFIGURACAO
# ============================================================

API_URL = "https://pangeabnp.pdpj.jus.br/api/v1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://bnp.pdpj.jus.br",
    "Referer": "https://bnp.pdpj.jus.br/",
}

# Todos os orgaos disponiveis (descoberto via GET /api/v1/parametros)
# TSE e TREs tambem existem em /parametros, mas com semPrecedentes=true
TODOS_ORGAOS = [
    # Tribunais Superiores
    "STF", "STJ", "TST", "STM", "TNU",
    # TRFs
    "TRF01", "TRF02", "TRF03", "TRF04", "TRF05", "TRF06",
    # TJs
    "TJAC", "TJAL", "TJAP", "TJAM", "TJBA", "TJCE", "TJDF", "TJES",
    "TJGO", "TJMA", "TJMT", "TJMS", "TJMG", "TJPA", "TJPB", "TJPR",
    "TJPE", "TJPI", "TJRJ", "TJRN", "TJRS", "TJRO", "TJRR", "TJSC",
    "TJSP", "TJSE", "TJTO",
    # TRTs
    "TRT01", "TRT02", "TRT03", "TRT04", "TRT05", "TRT06", "TRT07",
    "TRT08", "TRT09", "TRT10", "TRT11", "TRT12", "TRT13", "TRT14",
    "TRT15", "TRT16", "TRT17", "TRT18", "TRT19", "TRT20", "TRT21",
    "TRT22", "TRT23", "TRT24",
    # TJMs
    "TJMMG", "TJMRS", "TJMSP",
]

# Todas as especies de precedentes disponiveis
TODOS_TIPOS = [
    "SUM",   # Sumula
    "SV",    # Sumula Vinculante
    "RG",    # Tema de Repercussao Geral
    "IAC",   # Incidente de Assuncao de Competencia
    "SIRDR", # Suspensao Nacional em IRDR
    "RR",    # Recurso Especial Repetitivo
    "CT",    # Controversia
    "IRDR",  # Incidente de Resolucao de Demandas Repetitivas
    "IRR",   # Incidente de Recurso Repetitivo
    "PUIL",  # Pedido de Uniformizacao de Interpretacao de Lei
    "OJ",    # Orientacao Jurisprudencial
    "ADI",   # Acao Direta de Inconstitucionalidade (controle concentrado)
    "ADC",   # Acao Declaratoria de Constitucionalidade (controle concentrado)
    "ADO",   # ADI por Omissao (controle concentrado)
    "ADPF",  # Arguicao de Descumprimento de Preceito Fundamental (controle concentrado)
    "PN",    # Precedente Normativo
    "NT",    # Nota Tecnica
    "NTA",   # Nota de Adesao
    "ENU",   # Enunciado
    "RC",    # Representativo da Controversia
]

# Cache das especies vigentes em /parametros (a API exige lista explicita
# de tipos em toda busca: especie fora da lista fica invisivel ao resultado)
_tipos_cache: Optional[List[str]] = None

# Mapeamento de grupos para facilitar filtros
GRUPOS_ORGAOS = {
    "superiores": ["STF", "STJ", "TST", "STM", "TNU"],
    "trfs": [f"TRF0{i}" for i in range(1, 7)],
    "tjs": [s for s in TODOS_ORGAOS if s.startswith("TJ") and not s.startswith("TJM")],
    "trts": [f"TRT{str(i).zfill(2)}" for i in range(1, 25)],
    "tjms": ["TJMMG", "TJMRS", "TJMSP"],
}


# ============================================================
# FUNCOES AUXILIARES
# ============================================================

def _limpar_html(texto: str) -> str:
    """Remove tags HTML e normaliza espacos."""
    if not texto:
        return ""
    texto = re.sub(r'</?(?:mark|p|br|strong|em|b|i)(?:\s[^>]*)?\s*/?>', ' ', texto)
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


def _resolver_orgaos(orgaos: Optional[List[str]]) -> List[str]:
    """Resolve lista de orgaos, expandindo grupos se necessario."""
    if not orgaos:
        return TODOS_ORGAOS

    resultado = []
    for o in orgaos:
        chave = o.lower()
        if chave in GRUPOS_ORGAOS:
            resultado.extend(GRUPOS_ORGAOS[chave])
        else:
            resultado.append(o.upper())
    return resultado


def _handle_error(e: Exception) -> str:
    """Formatacao consistente de erros."""
    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 400:
            return "Erro: Requisicao invalida. Verifique os parametros."
        elif status == 403:
            return "Erro: Acesso negado ao BNP."
        elif status == 429:
            return "Erro: Limite de requisicoes excedido. Aguarde."
        elif status >= 500:
            return f"Erro: Servidor BNP indisponivel (HTTP {status})"
        return f"Erro: Falha na requisicao (HTTP {status})"
    elif isinstance(e, httpx.TimeoutException):
        return "Erro: Timeout na requisicao ao BNP. Tente novamente."
    elif isinstance(e, httpx.ConnectError):
        return "Erro: Nao foi possivel conectar ao BNP."
    return f"Erro: {type(e).__name__}: {str(e)}"


async def _obter_todos_tipos() -> List[str]:
    """Obtem as especies vigentes de /parametros; fallback na lista fixa."""
    global _tipos_cache
    if _tipos_cache:
        return _tipos_cache
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/parametros", headers=HEADERS, timeout=10.0
            )
            response.raise_for_status()
            especies = response.json().get("especies", [])
        # siglas com espaco sao aliases de grupo (ex. "ADI ADC ADO ADPF"),
        # ja cobertas pelas siglas individuais
        siglas = [e.get("sigla", "") for e in especies]
        siglas = [s for s in siglas if s and " " not in s]
        if siglas:
            _tipos_cache = siglas
            return siglas
    except Exception:
        pass
    return TODOS_TIPOS


async def _buscar_api(busca: str, max_resultados: int = 10,
                      orgaos: Optional[List[str]] = None,
                      tipos: Optional[List[str]] = None,
                      pagina: int = 1,
                      nr: str = "") -> dict:
    """Faz busca na API do BNP e retorna resposta JSON."""
    orgaos_resolvidos = _resolver_orgaos(orgaos)
    tipos_resolvidos = tipos if tipos else await _obter_todos_tipos()

    body = {
        "filtro": {
            "buscaGeral": busca,
            "todasPalavras": "",
            "quaisquerPalavras": "",
            "semPalavras": "",
            "trechoExato": "",
            "atualizacaoDesde": "",
            "atualizacaoAte": "",
            "cancelados": False,
            "ordenacao": "Text",
            "nr": nr,
            "pagina": pagina,
            "tamanhoPagina": max_resultados,
            "orgaos": orgaos_resolvidos,
            "tipos": tipos_resolvidos,
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/precedentes",
            json=body,
            headers=HEADERS,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()


# ============================================================
# PYDANTIC MODELS
# ============================================================

class BuscaInput(BaseModel):
    """Input para busca de precedentes no BNP."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    busca: str = Field(
        ...,
        description=(
            "Query de busca. Sintaxe OpenSearch/Lucene: "
            '+termo (obrigatorio), -termo (excluir), "frase exata". '
            'Exemplos: "pensao por morte", +aposentadoria +especial, '
            'previdenciario -militar'
        ),
        min_length=2,
        max_length=500
    )
    max_resultados: int = Field(
        default=10,
        description="Maximo de resultados por pagina (1-50)",
        ge=1,
        le=50
    )
    orgaos: Optional[List[str]] = Field(
        default=None,
        description=(
            "Filtro por tribunais. Siglas: STF, STJ, TST, STM, TNU, "
            "TRF01-TRF06, TJAC-TJTO, TRT01-TRT24. "
            "Grupos: 'superiores', 'trfs', 'tjs', 'trts'. "
            "Vazio = todos os tribunais."
        )
    )
    tipos: Optional[List[str]] = Field(
        default=None,
        description=(
            "Filtro por especie de precedente. Siglas: "
            "SUM (Sumula), SV (Sumula Vinculante), RG (Repercussao Geral), "
            "RR (Recurso Repetitivo), IAC, IRDR, IRR, SIRDR, CT, PUIL, OJ, "
            "ADI, ADC, ADO, ADPF (controle concentrado do STF), "
            "PN, NT (Nota Tecnica), NTA, ENU, RC. "
            "Vazio = todas as especies."
        )
    )
    pagina: int = Field(
        default=1,
        description="Numero da pagina (1-based)",
        ge=1
    )
    nr: Optional[str] = Field(
        default=None,
        description=(
            "Filtro pelo numero exato do precedente. Combine com 'tipos' "
            "para localizar um precedente especifico: Tema 1283 do STJ = "
            "nr='1283' + tipos=['RR']; ADI 4277 = nr='4277' + tipos=['ADI']. "
            "Vazio = sem filtro de numero."
        ),
        max_length=20
    )

    @field_validator('busca')
    @classmethod
    def validar_busca(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Termo de busca nao pode ser vazio")
        return v.strip()


class RelatorioInput(BaseModel):
    """Input para geracao de relatorio de precedentes."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )

    busca: str = Field(
        ...,
        description=(
            "Query de busca. Mesma sintaxe de buscar_precedentes."
        ),
        min_length=2,
        max_length=500
    )
    max_resultados: int = Field(
        default=10,
        description="Maximo de resultados para o relatorio (1-30)",
        ge=1,
        le=30
    )
    orgaos: Optional[List[str]] = Field(
        default=None,
        description="Filtro por tribunais (mesma sintaxe de buscar_precedentes)"
    )
    tipos: Optional[List[str]] = Field(
        default=None,
        description="Filtro por especie de precedente"
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
    name="buscar_precedentes",
    annotations={
        "title": "Buscar Precedentes no BNP/CNJ",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def buscar_precedentes(params: BuscaInput) -> str:
    """
    Busca precedentes qualificados no Banco Nacional de Precedentes (BNP/CNJ).

    Abrange todos os tribunais brasileiros: STF, STJ, TST, TRFs, TJs, TRTs.
    Inclui sumulas, sumulas vinculantes, temas de repercussao geral,
    recursos repetitivos, IRDRs e demais precedentes vinculantes.

    SINTAXE DE BUSCA (OpenSearch/Lucene):
      +termo          palavra obrigatoria
      -termo          excluir palavra
      "frase exata"   busca por frase exata
      termo1 termo2   qualquer um (OR implicito)

    EXEMPLOS:
      "pensao por morte"             frase exata
      +aposentadoria +especial       ambas obrigatorias
      previdenciario -militar        com exclusao
      "dano moral" +consumidor       combinando operadores

    FILTROS POR TRIBUNAL (orgaos):
      Individuais: STF, STJ, TST, STM, TNU, TRF01-TRF06
      Grupos: "superiores", "trfs", "tjs", "trts"

    FILTROS POR ESPECIE (tipos):
      SUM, SV, RG, RR, IAC, IRDR, IRR, SIRDR, CT, PUIL, OJ,
      ADI, ADC, ADO, ADPF (controle concentrado), PN, NT, NTA, ENU, RC

    LOCALIZACAO EXATA (nr):
      nr='1283' + tipos=['RR']   Tema 1283 do STJ
      nr='4277' + tipos=['ADI']  ADI 4277

    NOTA: um resultado pode casar apenas parte dos termos buscados;
    quando isso ocorre, <termos_sem_correspondencia> lista os termos
    que NAO aparecem naquele registro.

    LEITURA HONESTA DOS PRECEDENTES - REGRAS DE OURO:
    1. SITUACAO manda: leia <situacao> de CADA precedente antes de aplica-lo.
       "Transitado em julgado" = definitivo. "Acordao Publicado (RE Pendente)" =
       tese fixada mas ainda cabe reversao no STF (nao e definitivo). "Controversia"
       (tipo CT) = tema em discussao, SEM tese vinculante ainda. "Cancelado"/superado
       = NAO citar como vigente. Nunca trate um precedente nao-final como pacifico.
    2. SUSPENSAO: se ha <suspensao ativa="true">, sinalize SEMPRE - e para TODOS os
       precedentes citados, nao so o primeiro. ATENCAO: o BNP diz que HA suspensao,
       mas NAO diz o ALCANCE dela (quais processos/instancias estao sobrestados). O
       alcance vem dos dados abertos do STJ (dadosabertos.web.stj.jus.br, temas.csv,
       campo informacoesComplementares) - reporte a suspensao e que o alcance exige
       essa conferencia externa; nao afirme "pode aplicar ja" sem isso.
    3. SO EXISTE O QUE A FERRAMENTA DEVOLVEU: antes de citar um Tema/Sumula, CONFIRME-O
       no BNP (busque por nr+tipos). Nao cite numero de tema, tese ou "distinguishing"
       de memoria de treino sem o BNP ter retornado o registro. Cada precedente citado
       aponta um id (ex.: stj-rr-1229) que o retorno trouxe.

    Args:
        params: Parametros de busca (busca, max_resultados, orgaos, tipos, pagina)

    Returns:
        XML estruturado com precedentes encontrados
    """
    try:
        data = await _buscar_api(
            busca=params.busca,
            max_resultados=params.max_resultados,
            orgaos=params.orgaos,
            tipos=params.tipos,
            pagina=params.pagina,
            nr=params.nr or ""
        )

        resultados = data.get("resultados", [])
        total = data.get("total", 0)

        if not resultados:
            return (
                f'<!-- Busca: "{params.busca}" | Total: 0 -->\n'
                f'<precedentes_bnp total="0">\n'
                f'  <mensagem>Nenhum precedente encontrado.</mensagem>\n'
                f'</precedentes_bnp>'
            )

        linhas = [
            f'<!-- Busca: "{params.busca}" | Pagina: {params.pagina} | '
            f'Exibindo: {len(resultados)} de {total} -->',
            f'<precedentes_bnp total="{total}">'
        ]

        for i, r in enumerate(resultados, 1):
            linhas.append(f'  <precedente indice="{i}">')
            linhas.append(f'    <id>{_escape_xml(r.get("id", ""))}</id>')
            linhas.append(f'    <tipo>{_escape_xml(r.get("tipo", ""))}</tipo>')
            linhas.append(f'    <numero>{r.get("nr", "")}</numero>')
            linhas.append(f'    <orgao>{_escape_xml(r.get("orgao", ""))}</orgao>')
            linhas.append(f'    <situacao>{_escape_xml(r.get("situacao", ""))}</situacao>')
            linhas.append(f'    <ultima_atualizacao>{_escape_xml(r.get("ultimaAtualizacao", ""))}</ultima_atualizacao>')

            questao = _limpar_html(r.get("questao", ""))
            if questao:
                questao = _truncar_texto(questao, 2000)
                linhas.append(f'    <questao>{_escape_xml(questao)}</questao>')

            tese = _limpar_html(r.get("tese", ""))
            if tese:
                tese = _truncar_texto(tese, 3000)
                linhas.append(f'    <tese>{_escape_xml(tese)}</tese>')

            paradigmas = r.get("processosParadigma", [])
            if paradigmas:
                linhas.append('    <processos_paradigma>')
                for p in paradigmas[:5]:
                    numero = p.get("numero", "")
                    link = p.get("link", "")
                    linhas.append(f'      <processo numero="{_escape_xml(numero)}" link="{_escape_xml(link)}" />')
                linhas.append('    </processos_paradigma>')

            suspensoes = r.get("suspensoes", [])
            for s in suspensoes:
                if s.get("ativa"):
                    linhas.append(
                        f'    <suspensao ativa="true" data="{_escape_xml(s.get("dataSuspensao", ""))}">'
                        f'{_escape_xml(s.get("descricao", ""))}</suspensao>'
                    )

            historico = r.get("historico", [])
            if historico:
                linhas.append('    <historico>')
                for h in historico[-5:]:
                    data_h = str(h.get("dataCriacao", ""))[:10]
                    linhas.append(
                        f'      <evento data="{_escape_xml(data_h)}">'
                        f'{_escape_xml(h.get("situacao", ""))}</evento>'
                    )
                linhas.append('    </historico>')

            # a busca pode retornar registro que nao casa todos os termos
            faltantes = r.get("missing", [])
            if faltantes:
                linhas.append(
                    f'    <termos_sem_correspondencia>'
                    f'{_escape_xml(", ".join(str(t) for t in faltantes))}'
                    f'</termos_sem_correspondencia>'
                )

            linhas.append('  </precedente>')

        linhas.append('</precedentes_bnp>')
        return "\n".join(linhas)

    except Exception as e:
        return f'<erro>{_handle_error(e)}</erro>'


@mcp.tool(
    name="gerar_relatorio_precedentes",
    annotations={
        "title": "Gerar Relatorio de Precedentes do BNP/CNJ",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def gerar_relatorio_precedentes(params: RelatorioInput) -> str:
    """
    Busca precedentes no BNP e gera relatorio formatado em Markdown.

    USE ESTA TOOL quando precisar de um relatorio para apresentar ao usuario.
    Para analise programatica, prefira buscar_precedentes (retorna XML).

    A sintaxe de busca e a MESMA de buscar_precedentes. Valem as MESMAS regras de
    leitura honesta: situacao de cada precedente (definitivo x RE pendente x
    controversia x cancelado); suspensao ativa sinalizada para TODOS os citados (e o
    BNP nao traz o ALCANCE - vem dos dados abertos do STJ); e so cite Tema/Sumula que
    o BNP efetivamente retornou (nunca de memoria de treino).

    Args:
        params: Parametros (busca, max_resultados, orgaos, tipos)

    Returns:
        Relatorio em Markdown com precedentes e metadados
    """
    try:
        data = await _buscar_api(
            busca=params.busca,
            max_resultados=params.max_resultados,
            orgaos=params.orgaos,
            tipos=params.tipos,
        )

        resultados = data.get("resultados", [])
        total = data.get("total", 0)
        aggs_orgaos = data.get("aggsOrgaos", [])
        aggs_especies = data.get("aggsEspecies", [])
        data_hora = datetime.now().strftime("%d/%m/%Y as %H:%M")

        linhas = [
            "# Relatorio de Precedentes - BNP/CNJ",
            "",
            f"**Busca realizada:** `{params.busca}`",
            f"**Data/Hora:** {data_hora}",
            f"**Precedentes encontrados:** {total}",
            f"**Exibindo:** {len(resultados)}",
        ]

        if aggs_orgaos:
            dist = ", ".join(f"{a['tipo']}({a['total']})" for a in aggs_orgaos[:10])
            linhas.append(f"**Distribuicao por tribunal:** {dist}")

        if aggs_especies:
            dist = ", ".join(f"{a['tipo']}({a['total']})" for a in aggs_especies[:10])
            linhas.append(f"**Distribuicao por especie:** {dist}")

        linhas.extend(["", "---", ""])

        if not resultados:
            linhas.append("*Nenhum precedente encontrado.*")
            return "\n".join(linhas)

        tipo_descricao = {
            "SUM": "Sumula", "SV": "Sumula Vinculante",
            "RG": "Repercussao Geral", "RR": "Recurso Repetitivo",
            "IAC": "Incidente de Assuncao de Competencia",
            "IRDR": "Incidente de Resolucao de Demandas Repetitivas",
            "IRR": "Incidente de Recurso Repetitivo",
            "SIRDR": "Suspensao Nacional em IRDR",
            "CT": "Controversia", "PUIL": "Uniformizacao de Lei",
            "OJ": "Orientacao Jurisprudencial",
            "ADI": "Acao Direta de Inconstitucionalidade",
            "ADC": "Acao Declaratoria de Constitucionalidade",
            "ADO": "ADI por Omissao",
            "ADPF": "Arguicao de Descumprimento de Preceito Fundamental",
            "PN": "Precedente Normativo", "NT": "Nota Tecnica",
            "NTA": "Nota de Adesao", "ENU": "Enunciado",
            "RC": "Representativo da Controversia",
        }

        for i, r in enumerate(resultados, 1):
            tipo = r.get("tipo", "")
            tipo_nome = tipo_descricao.get(tipo, tipo)
            orgao = r.get("orgao", "")
            nr = r.get("nr", "")
            situacao = r.get("situacao", "")
            atualizacao = r.get("ultimaAtualizacao", "")

            linhas.extend([
                f"## {i}. {orgao} - {tipo_nome} n. {nr}",
                "",
                f"**Tribunal:** {orgao} | **Tipo:** {tipo_nome} | **Numero:** {nr}",
                f"**Situacao:** {situacao}",
                f"**Ultima atualizacao:** {atualizacao}",
                ""
            ])

            questao = _limpar_html(r.get("questao", ""))
            if questao:
                questao = _truncar_texto(questao, 1500)
                linhas.extend(["### Questao", "", f"> {questao}", ""])

            tese = _limpar_html(r.get("tese", ""))
            if tese:
                tese = _truncar_texto(tese, 2000)
                linhas.extend(["### Tese", "", f"> {tese}", ""])

            paradigmas = r.get("processosParadigma", [])
            if paradigmas:
                linhas.append("**Processos paradigma:**")
                for p in paradigmas[:3]:
                    numero = p.get("numero", "")
                    link = p.get("link", "")
                    linhas.append(f"- [{numero}]({link})")
                linhas.append("")

            suspensoes = r.get("suspensoes", [])
            for s in suspensoes:
                if s.get("ativa"):
                    linhas.append(
                        f"**Suspensao ativa:** {s.get('descricao', '')} "
                        f"(desde {s.get('dataSuspensao', '')})"
                    )
                    linhas.append("")

            historico = r.get("historico", [])
            if historico:
                eventos = "; ".join(
                    f"{h.get('situacao', '')} em {str(h.get('dataCriacao', ''))[:10]}"
                    for h in historico[-3:]
                )
                linhas.extend([f"**Historico de situacao:** {eventos}", ""])

            faltantes = r.get("missing", [])
            if faltantes:
                linhas.extend([
                    f"**Atencao:** o registro NAO contem o(s) termo(s) buscado(s): "
                    f"{', '.join(str(t) for t in faltantes)}",
                    ""
                ])

            linhas.extend(["---", ""])

        linhas.extend([
            "",
            f"*Relatorio gerado via MCP BNP/CNJ em {data_hora}*"
        ])

        return "\n".join(linhas)

    except Exception as e:
        return f"**Erro:** {_handle_error(e)}"


@mcp.tool(
    name="listar_filtros_bnp",
    annotations={
        "title": "Listar Filtros Disponiveis no BNP/CNJ",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def listar_filtros_bnp() -> str:
    """
    Lista todos os filtros e parametros disponiveis para busca no BNP.

    Consulta a API /parametros para retornar a lista atualizada de
    tribunais, especies de precedentes e grupos disponiveis.

    Returns:
        XML estruturado com filtros e operadores
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_URL}/parametros",
                headers=HEADERS,
                timeout=15.0
            )
            response.raise_for_status()
            data = response.json()

        linhas = ['<filtros_bnp>']

        # Operadores de busca
        linhas.append('  <operadores_busca>')
        linhas.append('    <operador codigo="+" tipo="obrigatorio">+termo - Palavra obrigatoria. Ex: +aposentadoria +especial</operador>')
        linhas.append('    <operador codigo="-" tipo="exclusao">-termo - Excluir palavra. Ex: previdenciario -militar</operador>')
        linhas.append('    <operador codigo="&quot;&quot;" tipo="frase">"frase" - Busca exata. Ex: "pensao por morte"</operador>')
        linhas.append('    <operador codigo="OR" tipo="alternativa">termo1 termo2 - OR implicito entre termos</operador>')
        linhas.append('  </operadores_busca>')

        # Tribunais
        orgaos = data.get("orgaos", [])
        linhas.append('  <tribunais>')
        for o in orgaos:
            sigla = o.get("sigla", "")
            desc = o.get("descricao", "")
            sem = ' semPrecedentes="true"' if o.get("semPrecedentes") else ""
            linhas.append(f'    <tribunal sigla="{_escape_xml(sigla)}"{sem}>{_escape_xml(desc)}</tribunal>')
        linhas.append('  </tribunais>')

        # Grupos de tribunais
        grupos = data.get("gruposTribunais", [])
        linhas.append('  <grupos_tribunais>')
        for g in grupos:
            sigla = g.get("sigla", "")
            desc = g.get("descricao", "")
            linhas.append(f'    <grupo sigla="{_escape_xml(sigla)}">{_escape_xml(desc)}</grupo>')
        linhas.append('  </grupos_tribunais>')

        # Especies
        especies = data.get("especies", [])
        linhas.append('  <especies>')
        for e in especies:
            sigla = e.get("sigla", "")
            desc = e.get("descricao", "")
            apelido = e.get("apelido") or ""
            extra = f' apelido="{_escape_xml(apelido)}"' if apelido else ""
            linhas.append(f'    <especie sigla="{_escape_xml(sigla)}"{extra}>{_escape_xml(desc)}</especie>')
        linhas.append('  </especies>')

        linhas.append('</filtros_bnp>')
        return "\n".join(linhas)

    except Exception as e:
        return f'<erro>{_handle_error(e)}</erro>'


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    mcp.run()
