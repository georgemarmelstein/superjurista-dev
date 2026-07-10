# -*- coding: utf-8 -*-
"""
MCP Server: CJF Jurisprudencia Unificada (Standalone) — v2

Acesso a jurisprudencia unificada do CJF (Conselho da Justica Federal):
STF, STJ, TNU, TRF1-TRF5, TRU1-TRU6 (Turmas Regionais de Uniformizacao)
e TR1-TR6 (Turmas Recursais).

Scraping JSF/AJAX (nao ha API JSON publica). Robustecido em 2026-07-10:
- descoberta dinamica de ids (nada de j_idt51 fixo);
- paginacao real (indices absolutos, 50 linhas por request);
- faixa de datas via formulario avancado (unica coisa que a sintaxe nao cobre);
- obter_documento_cjf (registro completo sem truncar, via dialogo sem formatacao);
- cobertura da base medida e declarada (STF/STJ/TRF5 congelados ~2019);
- sintaxe completa da ajuda oficial (31 campos, operadores NAO ADJ etc).
"""

import re
import html as html_module
from typing import Any, Dict, List, Optional, Tuple

import requests
from mcp.server.fastmcp import FastMCP
from tenacity import retry, stop_after_attempt, wait_exponential

mcp = FastMCP("cjf-jurisprudencia")

# ============================================================
# CONFIGURACAO
# ============================================================

CJF_URL = "https://jurisprudencia.cjf.jus.br/unificada/index.xhtml"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/146.0.0.0 Safari/537.36"
)

HEADERS_AJAX = {
    "Accept": "application/xml, text/xml, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Faces-Request": "partial/ajax",
    "X-Requested-With": "XMLHttpRequest",
}

TRIBUNAIS = {
    "STF": "Supremo Tribunal Federal",
    "STJ": "Superior Tribunal de Justica",
    "TNU": "Turma Nacional de Uniformizacao",
    "TRF1": "Tribunal Regional Federal da 1a Regiao",
    "TRF2": "Tribunal Regional Federal da 2a Regiao",
    "TRF3": "Tribunal Regional Federal da 3a Regiao",
    "TRF4": "Tribunal Regional Federal da 4a Regiao",
    "TRF5": "Tribunal Regional Federal da 5a Regiao",
}
TRUS = {f"TRU{i}": f"Turma Regional de Uniformizacao da {i}a Regiao" for i in range(1, 7)}
TRS = {f"TR{i}": f"Turmas Recursais da {i}a Regiao" for i in range(1, 7)}

TRIBUNAIS_DEFAULT = "STF,STJ,TNU,TRF1,TRF2,TRF3,TRF4,TRF5"

# Medido em 10/07/2026 por contagem de julgados por faixa de data (DTDP).
COBERTURA_BASE = {
    "STF": "CONGELADA — nada apos ~2019",
    "STJ": "CONGELADA — nada apos ~dez/2019",
    "TNU": "ATUALIZADA — julgados ate 06/2026",
    "TRF1": "ATUALIZADA — julgados ate 2026",
    "TRF2": "DESATUALIZADA — nada apos ~2023",
    "TRF3": "ATUALIZADA — julgados ate 2026",
    "TRF4": "ATUALIZADA — acervo pequeno (~1.7k docs 2020-2026)",
    "TRF5": "CONGELADA — nada apos ~fev/2019",
}

CONGELADOS = {"STF", "STJ", "TRF2", "TRF5"}

PAGINA_MAX_LINHAS = 50  # opcoes reais do paginador: 10, 30, 50


# ============================================================
# SESSAO JSF (com descoberta dinamica de ids)
# ============================================================

class CJFSession:
    """Sessao JSF: ViewState + cookies + descoberta de ids na pagina.

    Os ids `j_idtNN` sao gerados pelo JSF e mudam se o CJF regenerar a
    pagina — por isso NADA aqui e fixo: o name dos checkboxes de tribunal,
    os campos do painel avancado e os botoes por linha sao descobertos por
    parse a cada sessao (com fallback nos valores conhecidos de 07/2026).
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8"}
        )
        self.viewstate: Optional[str] = None
        self.nome_checkbox_tribunais = "formulario:j_idt51"  # fallback
        self.campos_avancados: Dict[str, str] = {}
        self._avancada_ativa = False
        self._tru_ativa = False
        self._tr_ativa = False

    # ---------- primitivas HTTP ----------

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3))
    def iniciar(self) -> None:
        """GET inicial: ViewState + name real dos checkboxes de tribunal."""
        resp = self.session.get(CJF_URL, timeout=30)
        resp.raise_for_status()
        m = re.search(
            r'name="javax\.faces\.ViewState"[^>]*value="([^"]+)"', resp.text
        )
        if not m:
            raise ValueError("ViewState nao encontrado na pagina do CJF")
        self.viewstate = m.group(1)
        # descoberta: o checkbox cujo value e um tribunal conhecido
        cb = re.search(
            r'<input[^>]*name="([^"]+)"[^>]*type="checkbox"[^>]*value="(?:STF|STJ|TNU|TRF\d)"',
            resp.text,
        ) or re.search(
            r'<input[^>]*type="checkbox"[^>]*name="([^"]+)"[^>]*value="(?:STF|STJ|TNU|TRF\d)"',
            resp.text,
        )
        if cb:
            self.nome_checkbox_tribunais = cb.group(1)

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3))
    def _post(self, form: List[Tuple[str, str]]) -> str:
        """POST parcial JSF; atualiza o ViewState devolvido na resposta."""
        if not self.viewstate:
            self.iniciar()
        resp = self.session.post(
            CJF_URL,
            data=form + [("javax.faces.ViewState", self.viewstate)],
            headers=HEADERS_AJAX,
            timeout=90,
        )
        resp.raise_for_status()
        m = re.search(
            r'<update id="javax\.faces\.ViewState"[^>]*><!\[CDATA\[(.*?)\]\]>',
            resp.text,
        )
        if m:
            self.viewstate = m.group(1)
        return resp.text

    # ---------- toggles de paineis (renderizam componentes no servidor) ----------

    def ativar_avancada(self) -> None:
        """Liga o painel avancado e mapeia os campos por label (ids dinamicos)."""
        if self._avancada_ativa:
            return
        resp = self._post([
            ("javax.faces.partial.ajax", "true"),
            ("javax.faces.source", "formulario:ckbAvancada"),
            ("javax.faces.partial.execute", "formulario:ckbAvancada"),
            ("javax.faces.partial.render", "formulario:pesquisaAvancada"),
            ("javax.faces.behavior.event", "change"),
            ("javax.faces.partial.event", "change"),
            ("formulario:ckbAvancada_input", "on"),
            ("formulario", "formulario"),
            ("formulario:textoLivre", ""),
        ])
        cd = _cdata(resp)
        # pareia cada label com o proximo input/select na ordem do documento
        pares: List[Tuple[str, str]] = []
        for lb in re.finditer(r"<label[^>]*>([^<]{1,60})</label>", cd):
            rotulo = " ".join(lb.group(1).split()).lower()
            campo = re.search(
                r'<(?:input|select)[^>]*name="(formulario:[^"]+)"',
                cd[lb.end():lb.end() + 800],
            )
            if campo:
                pares.append((rotulo, campo.group(1)))
        mapa = {}
        datas = []
        for rotulo, campo in pares:
            if campo.endswith("_focus"):
                continue
            if rotulo == "data (dd/mm/aaaa)" or (rotulo == "a" and datas):
                datas.append(campo)
            elif rotulo == "a":
                datas.append(campo)
            elif "tipo" in rotulo:
                mapa["tipo_data"] = campo
        if len(datas) >= 2:
            mapa["data_inicio"], mapa["data_fim"] = datas[0], datas[1]
        # fallbacks conhecidos (07/2026)
        mapa.setdefault("data_inicio", "formulario:j_idt43_input")
        mapa.setdefault("data_fim", "formulario:j_idt45_input")
        mapa.setdefault("tipo_data", "formulario:combo_tipo_data_input")
        self.campos_avancados = mapa
        self._avancada_ativa = True

    def ativar_tru(self) -> None:
        """Liga o painel das Turmas Regionais de Uniformizacao (TRU1-TRU6)."""
        if self._tru_ativa:
            return
        self._post([
            ("javax.faces.partial.ajax", "true"),
            ("javax.faces.source", "formulario:truMarcado"),
            ("javax.faces.partial.execute", "formulario:truMarcado"),
            ("javax.faces.partial.render", "formulario:tribunais"),
            ("javax.faces.behavior.event", "change"),
            ("javax.faces.partial.event", "change"),
            ("formulario:truMarcado_input", "on"),
            ("formulario", "formulario"),
            ("formulario:textoLivre", ""),
        ])
        self._tru_ativa = True

    def ativar_tr(self) -> None:
        """Liga o painel das Turmas Recursais (TR1-TR6)."""
        if self._tr_ativa:
            return
        self._post([
            ("javax.faces.partial.ajax", "true"),
            ("javax.faces.source", "formulario:trMarcado"),
            ("javax.faces.partial.execute", "formulario:trMarcado"),
            ("javax.faces.partial.render", "formulario:tribunais"),
            ("javax.faces.behavior.event", "change"),
            ("javax.faces.partial.event", "change"),
            ("formulario:trMarcado_input", "on"),
            ("formulario", "formulario"),
            ("formulario:textoLivre", ""),
        ])
        self._tr_ativa = True

    # ---------- montagem do formulario ----------

    def form_base(
        self,
        busca: str,
        tribunais: List[str],
        trus: List[str],
        trs: List[str],
        data_inicio: str = "",
        data_fim: str = "",
        tipo_data: str = "DTDP",
    ) -> List[Tuple[str, str]]:
        base: List[Tuple[str, str]] = [
            ("formulario", "formulario"),
            ("formulario:textoLivre", busca),
        ]
        for t in tribunais:
            base.append((self.nome_checkbox_tribunais, t))
        if trus:
            base.append(("formulario:truMarcado_input", "on"))
            for t in trus:
                base.append(("formulario:tribuna_tru", t))
        if trs:
            base.append(("formulario:trMarcado_input", "on"))
            for t in trs:
                base.append(("formulario:tribuna_tr", t))
        if data_inicio or data_fim:
            c = self.campos_avancados
            base.append(("formulario:ckbAvancada_input", "on"))
            base.append((c["data_inicio"], data_inicio))
            base.append((c["data_fim"], data_fim))
            base.append((c["tipo_data"].replace("_input", "_focus"), ""))
            base.append((c["tipo_data"], tipo_data))
        return base

    # ---------- acoes ----------

    def buscar(self, base: List[Tuple[str, str]]) -> str:
        return self._post([
            ("javax.faces.partial.ajax", "true"),
            ("javax.faces.source", "formulario:actPesquisar"),
            ("javax.faces.partial.execute", "@all"),
            ("javax.faces.partial.render", "formulario:resultado"),
            ("formulario:actPesquisar", "formulario:actPesquisar"),
        ] + base)

    def paginar(self, base: List[Tuple[str, str]], first: int, rows: int) -> str:
        return self._post([
            ("javax.faces.partial.ajax", "true"),
            ("javax.faces.source", "formulario:tabelaDocumentos"),
            ("javax.faces.partial.execute", "formulario:tabelaDocumentos"),
            ("javax.faces.partial.render", "formulario:tabelaDocumentos"),
            ("formulario:tabelaDocumentos", "formulario:tabelaDocumentos"),
            ("formulario:tabelaDocumentos_pagination", "true"),
            ("formulario:tabelaDocumentos_first", str(first)),
            ("formulario:tabelaDocumentos_rows", str(rows)),
            ("formulario:tabelaDocumentos_encodeFeature", "true"),
        ] + base)

    def obter_texto_documento(
        self, resposta_busca: str, indice_absoluto: int,
        base: List[Tuple[str, str]],
    ) -> str:
        """Abre o dialogo 'sem formatacao' da linha e devolve o texto integral.

        O botao por linha tem id gerado — e descoberto na propria resposta
        (o PrimeFaces.ab que atualiza formulario:dialogSemFormatacao).
        O dialogo e dinamico: o conteudo vem num segundo postback (contentLoad).
        """
        cd = _cdata(resposta_busca)
        m = re.search(
            r'PrimeFaces\.ab\(\{s:"(formulario:tabelaDocumentos:'
            + str(indice_absoluto)
            + r':[^"]+)",u:"formulario:dialogSemFormatacao"',
            cd,
        )
        if not m:
            raise ValueError(
                f"Botao do documento (linha {indice_absoluto}) nao encontrado"
            )
        btn = m.group(1)
        self._post([
            ("javax.faces.partial.ajax", "true"),
            ("javax.faces.source", btn),
            ("javax.faces.partial.execute", "@all"),
            ("javax.faces.partial.render", "formulario:dialogSemFormatacao"),
            (btn, btn),
        ] + base)
        conteudo = self._post([
            ("javax.faces.partial.ajax", "true"),
            ("javax.faces.source", "formulario:dialogSemFormatacao"),
            ("javax.faces.partial.execute", "formulario:dialogSemFormatacao"),
            ("javax.faces.partial.render", "formulario:dialogSemFormatacao"),
            ("formulario:dialogSemFormatacao_contentLoad", "true"),
            ("formulario:dialogSemFormatacao", "formulario:dialogSemFormatacao"),
        ] + base)
        cd2 = _cdata(conteudo)
        cd2 = re.sub(r"<script.*?</script>", " ", cd2, flags=re.DOTALL)
        texto = re.sub(r"<br\s*/?>", "\n", cd2)
        texto = re.sub(r"<[^>]+>", " ", texto)
        texto = re.sub(r"[ \t]+", " ", texto)
        texto = re.sub(r"\n\s*\n+", "\n\n", texto)
        # remove o ViewState que sobra no fim do partial-response
        texto = re.sub(r"-?\d{15,}:-?\d{15,}\s*$", "", texto.strip()).strip()
        return texto


# ============================================================
# EXTRACAO
# ============================================================

def _cdata(resposta: str) -> str:
    """Junta os blocos CDATA do partial-response, ja des-escapados."""
    content = html_module.unescape(resposta)
    blocos = re.findall(r"<!\[CDATA\[(.*?)\]\]>", content, re.DOTALL)
    return "".join(blocos)


def _limpar_html(texto: str) -> str:
    if not texto:
        return ""
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def _truncar(texto: str, max_chars: int = 6000) -> str:
    if not texto or len(texto) <= max_chars:
        return texto
    truncado = texto[:max_chars]
    ultimo_ponto = truncado.rfind(".")
    if ultimo_ponto > max_chars * 0.8:
        truncado = truncado[: ultimo_ponto + 1]
    return truncado + " [...]"


def _escape_xml(texto: str) -> str:
    if not texto:
        return ""
    return (
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _extrair_totais(cd: str) -> Dict[str, int]:
    totais = {}
    pattern = r"<td[^>]*>\s*([^<]+?)\s*</td>\s*<td[^>]*>.*?(\d+)\s*Documento"
    for m in re.finditer(pattern, cd, re.DOTALL):
        rotulo = " ".join(m.group(1).split())
        # rotulos: "STJ", "TRF5", "TRU 5ª Região", "TR 3ª Região"
        mt = re.fullmatch(r"(TRU?)\s*(\d)ª?\s*Regi.o", rotulo, re.IGNORECASE)
        sigla = f"{mt.group(1).upper()}{mt.group(2)}" if mt else rotulo
        if sigla in TRIBUNAIS or sigla in TRUS or sigla in TRS:
            totais[sigla] = int(m.group(2))
    return totais


def _extrair_erro_portal(cd: str) -> str:
    """Mensagens de validacao/erro que o portal devolve no lugar do resultado."""
    m = re.search(r"Error!?\s*([^<]{5,200})", cd)
    return " ".join(m.group(1).split()) if m else ""


# rotulo normalizado -> chave do documento
_CAMPOS_DOC = [
    ("tipo", "tipo"),
    ("numero", "numero"),
    ("número", "numero"),
    ("classe", "classe"),
    ("relator", "relator"),
    ("origem", "origem"),
    ("julgador", "orgao"),
    ("data da publica", "data_publicacao"),
    ("data", "data"),
    ("fonte", "fonte_publicacao"),
    ("decis", "decisao"),
    ("legislativa", "referencia_legislativa"),
]


def _extrair_documentos(resposta: str) -> List[Dict[str, Any]]:
    """Extrai os documentos estruturados da resposta AJAX JSF."""
    cd = _cdata(resposta)
    doc_starts = list(re.finditer(r'<div id="item_resultado-([^"]+)">', cd))
    docs = []
    field_re = re.compile(
        r'<span class="label_pontilhada">([^<]+)</span>'
        r".*?</tr>\s*<tr>\s*<td[^>]*>(.*?)</td>",
        re.DOTALL,
    )
    for i, match in enumerate(doc_starts):
        doc_id = match.group(1)
        start = match.start()
        end = doc_starts[i + 1].start() if i + 1 < len(doc_starts) else len(cd)
        block = cd[start:end]
        doc: Dict[str, Any] = {"id": doc_id}

        for fm in field_re.finditer(block):
            rotulo = " ".join(fm.group(1).split()).lower()
            val = _limpar_html(fm.group(2))
            if not val:
                continue
            for fragmento, chave in _CAMPOS_DOC:
                if fragmento in rotulo:
                    doc.setdefault(chave, val)
                    break

        ementa_re = re.search(
            rf'painel_ementa-{re.escape(doc_id)}"[^>]*>(.*?)</div>',
            block,
            re.DOTALL,
        )
        if ementa_re:
            ementa = _limpar_html(ementa_re.group(1))
            ementa = re.sub(r"^\.\.\w+:\s*", "", ementa)
            doc["ementa"] = ementa

        if doc.get("numero") or doc.get("ementa"):
            docs.append(doc)
    return docs


def _handle_error(e: Exception) -> str:
    if isinstance(e, requests.HTTPError):
        status = e.response.status_code
        if status == 403:
            return "Acesso negado pelo portal CJF."
        if status == 429:
            return "Limite de requisicoes excedido. Aguarde."
        if status >= 500:
            return (
                f"Portal CJF instavel (HTTP {status}) — e comum; "
                "tente novamente em alguns segundos."
            )
        return f"Falha na requisicao (HTTP {status})."
    if isinstance(e, requests.Timeout):
        return "Timeout na conexao com o portal CJF."
    if isinstance(e, requests.ConnectionError):
        return "Nao foi possivel conectar ao portal CJF."
    return f"{type(e).__name__}: {str(e)}"


# ============================================================
# PARSE DOS PARAMETROS DE TRIBUNAL / EXECUCAO DA BUSCA
# ============================================================

def _parse_tribunais(tribunais: str) -> Tuple[List[str], List[str], List[str]]:
    """Divide a lista em (tribunais principais, TRUs, TRs). 'TODOS' = os 8."""
    principais, trus, trs = [], [], []
    for item in tribunais.split(","):
        t = item.strip().upper()
        if not t:
            continue
        if t == "TODOS":
            principais.extend(k for k in TRIBUNAIS if k not in principais)
        elif t in TRIBUNAIS:
            principais.append(t)
        elif t in TRUS:
            trus.append(t)
        elif t == "TRU":
            trus.extend(TRUS.keys())
        elif t in TRS:
            trs.append(t)
        elif t == "TR":
            trs.extend(TRS.keys())
        else:
            raise ValueError(
                f"Tribunal desconhecido: {t}. Validos: "
                f"{', '.join(list(TRIBUNAIS) + list(TRUS) + list(TRS))}, TRU, TR, TODOS"
            )
    return principais, trus, trs


def _aviso_cobertura(principais: List[str]) -> str:
    frios = [t for t in principais if t in CONGELADOS]
    if not frios:
        return ""
    return (
        "Base do CJF desatualizada para: "
        + "; ".join(f"{t} ({COBERTURA_BASE[t]})" for t in frios)
        + ". Zero resultado recente nesses acervos NAO significa inexistencia "
        "de jurisprudencia — confirme em fonte atual (BNP para STF/STJ; "
        "JULIA para TRF5)."
    )


def _executar_busca(
    busca: str,
    tribunais: str,
    max_resultados: int,
    pagina: int,
    data_inicio: str,
    data_fim: str,
    tipo_data: str,
) -> Tuple[List[Dict], Dict[str, int], str, CJFSession, List[Tuple[str, str]], str]:
    """Busca com paginacao. Retorna (docs, totais, aviso, sessao, form_base, erro_portal)."""
    principais, trus, trs = _parse_tribunais(tribunais)
    if not (principais or trus or trs):
        raise ValueError("Nenhum tribunal selecionado.")
    max_resultados = max(1, min(int(max_resultados), 100))
    pagina = max(1, int(pagina))
    tipo = {"julgamento": "DTDP", "publicacao": "DTPP"}.get(
        tipo_data.strip().lower(), "DTDP"
    )
    if (data_inicio or data_fim) and not (data_inicio and data_fim):
        raise ValueError(
            "Para filtrar por data informe data_inicio E data_fim (DD/MM/AAAA)."
        )

    sess = CJFSession()
    sess.iniciar()
    if data_inicio:
        sess.ativar_avancada()
    if trus:
        sess.ativar_tru()
    if trs:
        sess.ativar_tr()

    base = sess.form_base(busca, principais, trus, trs, data_inicio, data_fim, tipo)
    resposta = sess.buscar(base)
    cd = _cdata(resposta)
    totais = _extrair_totais(cd)
    erro_portal = _extrair_erro_portal(cd) if not totais else ""

    inicio = (pagina - 1) * max_resultados
    fim = inicio + max_resultados
    docs: List[Dict] = []

    if inicio == 0 and fim <= 30:
        docs = _extrair_documentos(resposta)[:max_resultados]
    else:
        first = (inicio // PAGINA_MAX_LINHAS) * PAGINA_MAX_LINHAS
        while first < fim:
            resp_pag = sess.paginar(base, first, PAGINA_MAX_LINHAS)
            pagina_docs = _extrair_documentos(resp_pag)
            if not pagina_docs:
                break
            for j, d in enumerate(pagina_docs):
                absoluto = first + j
                if inicio <= absoluto < fim:
                    docs.append(d)
            first += PAGINA_MAX_LINHAS
    aviso = _aviso_cobertura(principais)
    return docs, totais, aviso, sess, base, erro_portal


# ============================================================
# TOOLS
# ============================================================

@mcp.tool()
def buscar_jurisprudencia_cjf(
    busca: str,
    tribunais: str = TRIBUNAIS_DEFAULT,
    max_resultados: int = 30,
    pagina: int = 1,
    data_inicio: str = "",
    data_fim: str = "",
    tipo_data: str = "julgamento",
) -> str:
    """
    Busca jurisprudencia unificada no portal do CJF (Conselho da Justica
    Federal): STF, STJ, TNU, TRF1-TRF5, TRU1-TRU6 e TR1-TR6 numa so consulta.
    Pontos fortes REAIS da base: TNU e TRFs 1/3/4 atualizados; STF/STJ
    historicos (ate ~2019); pesquisa federal unificada com operadores ricos.

    SINTAXE DE BUSCA (operadores MAIUSCULOS; sem pontuacao; sem artigos/preposicoes):

    BOOLEANOS: E, OU, NAO, XOU | agrupamento com parenteses | frase exata "entre aspas"
    PROXIMIDADE: ADJ[n] (adjacentes NA ordem, ate n termos entre eles, n<=99),
                 PROX[n] (proximos em QUALQUER ordem), COM (mesma sentenca),
                 MESMO (mesmo paragrafo)
    NEGATIVOS: NAO ADJ[n], NAO PROX[n], NAO COM, NAO MESMO, termo[-CAMPO]
    WILDCARDS: $ (qualquer sufixo: aposentad$), $[n] (ate n chars), ? (1 char exato)
               ATENCAO: wildcards NAO funcionam em campos de data.

    CAMPOS (termo[CAMPO] ou termo.CAMPO.; aceita nome curto ou longo):
    | Curto | Longo               | Conteudo               |
    |-------|---------------------|------------------------|
    | EMEN  | EMENTA              | Ementa                 |
    | DECI  | DECISAO             | Decisao                |
    | INDE  | INDEXACAO           | Indexacao tematica     |
    | REL   | RELATOR             | Relator                |
    | REV   | REVISOR             | Revisor                |
    | RELA  | RELATOR_ACORDAO     | Relator para acordao   |
    | RELC  | RELATOR_CONVOCADO   | Relator convocado      |
    | PROC  | PROCESSO            | Numero do processo     |
    | PRFO  | PROCESSO_FORMATADO  | Numero formatado       |
    | CLAS  | CLASSE              | Classe processual      |
    | ORGA  | ORGAO_JULGADOR      | Orgao julgador         |
    | TRIB  | TRIBUNAL            | Tribunal               |
    | UF    | UF                  | Unidade da federacao   |
    | REFL  | REF_LEGISLATIVA     | Legislacao citada      |
    | PREC  | PRECEDENTES         | Precedentes citados    |
    | SUCE  | SUCESSIVOS          | Julgados sucessivos    |
    | DOUT  | DOUTRINA            | Doutrina citada        |
    | ITEO  | INTEIRO_TEOR        | Inteiro teor (quando indexado) |
    | TXTO  | TXT_ORIGEM          | Texto de origem        |
    | OBS   | OBSERVACOES         | Observacoes            |
    | FONT  | FONTE_PUBLICACAO    | Fonte de publicacao    |
    | DTDP  | DATA_DECISAO_PESQ   | Data do julgamento (AAAAMMDD exata) |
    | DTPP  | DATA_PUBLICACAO_PESQ| Data da publicacao (AAAAMMDD exata) |

    DATAS: data exata = 20191219[DTPP] (AAAAMMDD, sem wildcard).
    FAIXA de datas = use os parametros data_inicio/data_fim (DD/MM/AAAA).

    EXEMPLOS:
    - (pensao E morte)[EMEN] E (homoafetivo OU "mesmo sexo")[EMEN]
    - KUKINA[REL] E prescricao
    - Lei-8112[REFL] E (revisao ADJ2 geral)
    - "aposentadoria especial"[EMEN] E EPI PROX3 neutralizacao
    - 1803486[PROC]

    REGRAS DE LEITURA HONESTA (obrigatorias):
    1. So cite o que a ferramenta devolveu — nunca complete numero de processo,
       relator, data ou tese de memoria.
    2. COBERTURA DESIGUAL DA BASE (medida em 10/07/2026): TNU, TRF1, TRF3 e
       TRF4 estao ATUALIZADOS (julgados ate 2026); STF e STJ estao CONGELADOS
       (nada apos ~dez/2019); TRF5 CONGELADO (nada apos ~fev/2019); TRF2 parou
       ~2023. Zero resultado recente em acervo congelado NAO significa
       inexistencia de jurisprudencia: caracterize como NAO VERIFICAVEL no CJF
       e confirme em fonte atual (BNP para precedentes STF/STJ; JULIA para TRF5).
    3. O resultado e o registro do acervo do CJF (ementa, decisao, metadados),
       nao o inteiro teor oficial — confirme no tribunal de origem antes de
       citacao formal.

    Args:
        busca: Query com a sintaxe CJF acima.
        tribunais: Lista separada por virgula. Opcoes: STF, STJ, TNU,
                   TRF1-TRF5, TRU1-TRU6 (ou TRU = todas), TR1-TR6 (ou TR =
                   todas), TODOS (= os 8 principais). Default: os 8 principais.
        max_resultados: Resultados por pagina (1-100, default 30).
        pagina: Pagina do resultado (1 = primeiros max_resultados, 2 = os
                seguintes...). O total por tribunal vem em <totais>.
        data_inicio: Inicio da faixa de datas, DD/MM/AAAA (opcional; exige data_fim).
        data_fim: Fim da faixa de datas, DD/MM/AAAA.
        tipo_data: A que a faixa se refere: "julgamento" (default) ou "publicacao".

    Returns:
        XML: <totais> por tribunal, <aviso_cobertura> quando aplicavel e
        <item> com id, tipo, numero, classe, relator, origem, orgao, data,
        data_publicacao, fonte_publicacao, referencia_legislativa, ementa
        (truncada em 6000 chars — use obter_documento_cjf(id) para o registro
        integral) e decisao.
    """
    try:
        docs, totais, aviso, _, _, erro_portal = _executar_busca(
            busca, tribunais, max_resultados, pagina,
            data_inicio, data_fim, tipo_data,
        )
    except ValueError as e:
        return f"<erro>{_escape_xml(str(e))}</erro>"
    except Exception as e:
        return f"<erro>{_escape_xml(_handle_error(e))}</erro>"

    linhas = [
        f'<jurisprudencia_cjf busca="{_escape_xml(busca)}" '
        f'pagina="{max(1, int(pagina))}" itens="{len(docs)}">'
    ]
    if totais:
        linhas.append("  <totais>")
        for trib, n in sorted(totais.items()):
            linhas.append(f'    <tribunal sigla="{trib}" documentos="{n}"/>')
        linhas.append("  </totais>")
    if erro_portal:
        linhas.append(
            f"  <erro_portal>{_escape_xml(erro_portal)}</erro_portal>"
        )
    if aviso:
        linhas.append(f"  <aviso_cobertura>{_escape_xml(aviso)}</aviso_cobertura>")
    if not docs:
        linhas.append("  <mensagem>Nenhum resultado nesta pagina.</mensagem>")
    for i, doc in enumerate(docs, 1):
        linhas.append(
            f'  <item indice="{i}" id="{_escape_xml(doc.get("id", ""))}">'
        )
        for tag in ("tipo", "numero", "classe", "relator", "origem", "orgao",
                    "data", "data_publicacao", "fonte_publicacao",
                    "referencia_legislativa"):
            if doc.get(tag):
                linhas.append(
                    f"    <{tag}>{_escape_xml(doc[tag])}</{tag}>"
                )
        if doc.get("ementa"):
            linhas.append(
                f"    <ementa>{_escape_xml(_truncar(doc['ementa']))}</ementa>"
            )
        if doc.get("decisao"):
            linhas.append(
                f"    <decisao>{_escape_xml(_truncar(doc['decisao'], 2000))}</decisao>"
            )
        linhas.append("  </item>")
    linhas.append("</jurisprudencia_cjf>")
    return "\n".join(linhas)


@mcp.tool()
def obter_documento_cjf(
    id_documento: str,
    busca: str,
    tribunais: str = TRIBUNAIS_DEFAULT,
    data_inicio: str = "",
    data_fim: str = "",
    tipo_data: str = "julgamento",
) -> str:
    """
    Recupera o REGISTRO INTEGRAL (sem truncamento) de um documento retornado
    por buscar_jurisprudencia_cjf — a ementa completa, a decisao e a linha de
    citacao oficial, em texto puro.

    Use quando a ementa veio truncada ("[...]") na busca ou quando for citar
    o documento e precisar do texto integral do registro.

    IMPORTANTE: o portal e stateful — informe a MESMA busca (e mesmos
    tribunais/datas) que retornou o documento; a ferramenta refaz a pesquisa,
    localiza o id (varre ate 200 resultados) e abre o documento.

    O que volta e o registro do acervo do CJF (ementa/decisao/metadados), nao
    necessariamente o inteiro teor oficial do julgado — confirme no tribunal
    de origem antes de citacao formal.

    Args:
        id_documento: O atributo id do <item> da busca (ex.: STJ000736273,
                      TRF500466408).
        busca: A mesma query usada na busca que retornou o documento.
        tribunais: Os mesmos tribunais da busca original.
        data_inicio: A mesma faixa de datas da busca original (se usada).
        data_fim: Idem.
        tipo_data: Idem ("julgamento" ou "publicacao").

    Returns:
        Texto integral do registro, ou <erro> se o documento nao for
        localizado entre os 200 primeiros resultados da busca informada
        (refine a busca para aproxima-lo do topo).
    """
    try:
        principais, trus, trs = _parse_tribunais(tribunais)
        tipo = {"julgamento": "DTDP", "publicacao": "DTPP"}.get(
            tipo_data.strip().lower(), "DTDP"
        )
        sess = CJFSession()
        sess.iniciar()
        if data_inicio:
            sess.ativar_avancada()
        if trus:
            sess.ativar_tru()
        if trs:
            sess.ativar_tr()
        base = sess.form_base(
            busca, principais, trus, trs, data_inicio, data_fim, tipo
        )
        resposta = sess.buscar(base)

        alvo = id_documento.strip()
        first = 0
        while first < 200:
            if first > 0:
                resposta = sess.paginar(base, first, PAGINA_MAX_LINHAS)
            cd = _cdata(resposta)
            achados = re.findall(r'<div id="item_resultado-([^"]+)">', cd)
            if not achados:
                break
            if alvo in achados:
                indice_absoluto = first + achados.index(alvo)
                texto = sess.obter_texto_documento(
                    resposta, indice_absoluto, base
                )
                return (
                    f"[DOCUMENTO {alvo} — registro integral do acervo CJF]\n\n"
                    + texto
                )
            first += len(achados) if first > 0 else 30
        return (
            f"<erro>Documento {_escape_xml(alvo)} nao localizado entre os "
            "primeiros 200 resultados desta busca. Refine a query para "
            "aproxima-lo do topo (ex.: adicione o numero: "
            f"{_escape_xml(alvo[-7:])}[PROC]).</erro>"
        )
    except ValueError as e:
        return f"<erro>{_escape_xml(str(e))}</erro>"
    except Exception as e:
        return f"<erro>{_escape_xml(_handle_error(e))}</erro>"


@mcp.tool()
def gerar_relatorio_cjf(
    busca: str,
    tribunais: str = TRIBUNAIS_DEFAULT,
    max_resultados: int = 10,
    pagina: int = 1,
    data_inicio: str = "",
    data_fim: str = "",
    tipo_data: str = "julgamento",
) -> str:
    """
    Busca jurisprudencia no CJF e devolve relatorio Markdown formatado, com
    totais por tribunal e ementas. Para analise programatica prefira
    buscar_jurisprudencia_cjf (XML); esta tool e para apresentar a um humano.

    Sintaxe de busca, tribunais, paginacao, faixa de datas e REGRAS DE
    LEITURA HONESTA identicos aos de buscar_jurisprudencia_cjf (leia la) —
    em especial a cobertura desigual da base: TNU/TRF1/TRF3/TRF4 atualizados;
    STF/STJ/TRF5 congelados ~2019; TRF2 parou ~2023.

    Args:
        busca: Query com sintaxe CJF.
        tribunais: Lista separada por virgula (STF, STJ, TNU, TRF1-5,
                   TRU1-6/TRU, TR1-6/TR, TODOS).
        max_resultados: Resultados por pagina (1-50, default 10).
        pagina: Pagina do resultado.
        data_inicio: Inicio da faixa de datas, DD/MM/AAAA (opcional).
        data_fim: Fim da faixa, DD/MM/AAAA.
        tipo_data: "julgamento" (default) ou "publicacao".

    Returns:
        Relatorio em Markdown com ementas e metadados.
    """
    try:
        docs, totais, aviso, _, _, erro_portal = _executar_busca(
            busca, tribunais, min(int(max_resultados), 50), pagina,
            data_inicio, data_fim, tipo_data,
        )
    except ValueError as e:
        return f"**Erro:** {e}"
    except Exception as e:
        return f"**Erro:** {_handle_error(e)}"

    linhas = [
        "# Relatorio de Jurisprudencia — CJF",
        "",
        f"**Busca:** `{busca}`",
        f"**Pagina:** {max(1, int(pagina))} | **Documentos nesta pagina:** {len(docs)}",
        "",
    ]
    if totais:
        linhas.extend(["## Totais por tribunal", "", "| Tribunal | Docs |", "|---|---|"])
        for trib, n in sorted(totais.items()):
            linhas.append(f"| {trib} | {n} |")
        linhas.append("")
    if erro_portal:
        linhas.append(f"> **Portal:** {erro_portal}")
        linhas.append("")
    if aviso:
        linhas.append(f"> **Aviso de cobertura:** {aviso}")
        linhas.append("")
    linhas.extend(["---", ""])
    if not docs:
        linhas.append("*Nenhum documento nesta pagina.*")
        return "\n".join(linhas)

    for i, doc in enumerate(docs, 1):
        linhas.append(f"## {i}. {doc.get('numero', 'N/I')} ({doc.get('id', '')})")
        linhas.append("")
        for rotulo, chave in [
            ("Classe", "classe"), ("Relator(a)", "relator"),
            ("Orgao julgador", "orgao"), ("Origem", "origem"),
            ("Data", "data"), ("Publicacao", "data_publicacao"),
            ("Fonte", "fonte_publicacao"),
        ]:
            if doc.get(chave):
                linhas.append(f"**{rotulo}:** {doc[chave]}")
        linhas.append("")
        if doc.get("ementa"):
            linhas.extend(["### Ementa", "", f"> {_truncar(doc['ementa'], 4000)}", ""])
        if doc.get("decisao"):
            linhas.extend(["### Decisao", "", f"> {_truncar(doc['decisao'], 2000)}", ""])
        linhas.extend(["---", ""])
    linhas.append("*Relatorio gerado via MCP CJF (registro de acervo — confirme no tribunal de origem antes de citacao formal).*")
    return "\n".join(linhas)


@mcp.tool()
def listar_filtros_cjf() -> str:
    """
    Lista tribunais (com o estado de atualizacao da base de cada um),
    operadores, campos de busca e wildcards disponiveis no CJF.

    Consulte antes de montar buscas complexas — e para saber em quais
    tribunais a base esta atualizada (TNU/TRF1/TRF3/TRF4) e em quais esta
    congelada (STF/STJ ~2019, TRF5 ~fev/2019, TRF2 ~2023).

    Returns:
        XML com tribunais+cobertura, operadores, campos e wildcards.
    """
    linhas = ["<filtros_cjf>"]
    linhas.append(f'  <cobertura_medida_em>10/07/2026</cobertura_medida_em>')
    linhas.append("  <tribunais>")
    for cod, nome in TRIBUNAIS.items():
        linhas.append(
            f'    <tribunal codigo="{cod}" cobertura="{_escape_xml(COBERTURA_BASE[cod])}">{nome}</tribunal>'
        )
    for cod, nome in TRUS.items():
        linhas.append(
            f'    <tribunal codigo="{cod}" cobertura="acervo irregular — '
            f'TRU1 grande, TRU2/TRU5/TRU6 quase vazias (10/07/2026)">{nome}</tribunal>'
        )
    for cod, nome in TRS.items():
        linhas.append(f'    <tribunal codigo="{cod}">{nome}</tribunal>')
    linhas.append('    <tribunal codigo="TODOS">Os 8 principais numa consulta</tribunal>')
    linhas.append("  </tribunais>")

    linhas.append("  <operadores>")
    ops = [
        ("\"...\"", "Frase exata", '"pensao por morte"'),
        ("( )", "Agrupamento/precedencia", "(a E b) NAO c"),
        ("E", "AND - ambos os termos", "pensao E morte"),
        ("OU", "OR - qualquer termo", "bpc OU loas"),
        ("NAO", "NOT - exclui termo", "servidor NAO militar"),
        ("XOU", "XOR - um ou outro, nao ambos", "pensao XOU aposentadoria"),
        ("ADJ[n]", "Adjacentes NA ordem (n<=99, default 1)", "Comissao ADJ2 Justica"),
        ("PROX[n]", "Proximos em qualquer ordem", "aposentadoria PROX3 invalidez"),
        ("COM", "Na mesma sentenca", "pensao COM dependente"),
        ("MESMO", "No mesmo paragrafo", "beneficio MESMO previdenciario"),
        ("NAO ADJ[n]", "2o termo NAO adjacente", "multa NAO ADJ2 ambiental"),
        ("NAO PROX[n]", "2o termo NAO proximo", "dano NAO PROX3 moral"),
        ("NAO COM", "2o termo fora da sentenca", "pensao NAO COM militar"),
        ("NAO MESMO", "2o termo fora do paragrafo", "tutela NAO MESMO antecipada"),
        ("termo[-CAMPO]", "Termo NAO pode ocorrer no campo", "previdencia[-DOUT]"),
    ]
    for cod, desc, ex in ops:
        linhas.append(
            f'    <operador codigo="{_escape_xml(cod)}" exemplo="{_escape_xml(ex)}">{desc}</operador>'
        )
    linhas.append("  </operadores>")

    linhas.append("  <campos>")
    campos = [
        ("ID", "ID_DOCUMENTO", "Identificador do documento"),
        ("ORIG", "ORIGEM", "Origem"),
        ("TIPO", "TIPO_DOCUMENTO", "Tipo do documento"),
        ("CLAS", "CLASSE", "Classe processual"),
        ("UF", "UF", "Unidade da federacao"),
        ("TRIB", "TRIBUNAL", "Tribunal"),
        ("ORGA", "ORGAO_JULGADOR", "Orgao julgador"),
        ("DTDE", "DATA_DECISAO", "Data da decisao"),
        ("DTDP", "DATA_DECISAO_PESQ", "Data do julgamento (AAAAMMDD exata)"),
        ("DTPP", "DATA_PUBLICACAO_PESQ", "Data da publicacao (AAAAMMDD exata)"),
        ("PROC", "PROCESSO", "Numero do processo"),
        ("PRFO", "PROCESSO_FORMATADO", "Numero formatado"),
        ("EMEN", "EMENTA", "Ementa"),
        ("DECI", "DECISAO", "Decisao"),
        ("TXTO", "TXT_ORIGEM", "Texto de origem"),
        ("ITEO", "INTEIRO_TEOR", "Inteiro teor (quando indexado)"),
        ("REL", "RELATOR", "Relator"),
        ("REV", "REVISOR", "Revisor"),
        ("RELA", "RELATOR_ACORDAO", "Relator para acordao"),
        ("RELC", "RELATOR_CONVOCADO", "Relator convocado"),
        ("RESP", "RELATOR_SUPLENTE", "Relator suplente"),
        ("OBS", "OBSERVACOES", "Observacoes"),
        ("REFL", "REF_LEGISLATIVA", "Referencia legislativa"),
        ("PREC", "PRECEDENTES", "Precedentes citados"),
        ("SUCE", "SUCESSIVOS", "Sucessivos"),
        ("DOUT", "DOUTRINA", "Doutrina citada"),
        ("INDE", "INDEXACAO", "Indexacao tematica"),
        ("CATA", "CATALOGO", "Catalogo"),
        ("FONT", "FONTE_PUBLICACAO", "Fonte de publicacao"),
        ("OUTF", "OUTRAS_FONTES", "Outras fontes"),
        ("OURE", "OUTRAS_REFERENCIAS", "Outras referencias"),
    ]
    for curto, longo, desc in campos:
        linhas.append(
            f'    <campo curto="{curto}" longo="{longo}">{desc}</campo>'
        )
    linhas.append("  </campos>")

    linhas.append("  <wildcards>")
    linhas.append('    <wildcard simbolo="$">Qualquer sufixo (aposentad$). NAO funciona em datas.</wildcard>')
    linhas.append('    <wildcard simbolo="$[n]">Ate n caracteres (A$3Z)</wildcard>')
    linhas.append('    <wildcard simbolo="?">Exatamente 1 caractere (MA??)</wildcard>')
    linhas.append("  </wildcards>")
    linhas.append("</filtros_cjf>")
    return "\n".join(linhas)


@mcp.tool()
def verificar_cobertura_cjf(tribunais: str = TRIBUNAIS_DEFAULT) -> str:
    """
    Mede AO VIVO a atualizacao da base do CJF por tribunal, contando julgados
    por faixa de data (2025-2026; se zero, 2020-2026). Use quando uma busca
    por periodo recente voltar vazia e voce precisar distinguir "base
    desatualizada" de "jurisprudencia inexistente" — a diferenca entre um
    NAO_VERIFICAVEL honesto e um falso negativo.

    Custa 1-2 requisicoes por tribunal (alguns segundos cada); prefira
    verificar so os tribunais da sua duvida.

    Args:
        tribunais: Lista separada por virgula (subconjunto de STF, STJ, TNU,
                   TRF1-TRF5). Default: os 8.

    Returns:
        XML com a contagem por faixa e a leitura (ATUALIZADA/DESATUALIZADA)
        por tribunal, mais a medicao de referencia de 10/07/2026.
    """
    try:
        principais, _, _ = _parse_tribunais(tribunais)
        principais = [t for t in principais if t in TRIBUNAIS]
        if not principais:
            raise ValueError("Informe ao menos um dos 8 tribunais principais.")
        sess = CJFSession()
        sess.iniciar()
        sess.ativar_avancada()

        linhas = ["<cobertura_cjf>"]
        for t in principais:
            base = sess.form_base("", [t], [], [], "01/01/2025", "31/12/2026", "DTDP")
            cd = _cdata(sess.buscar(base))
            totais = _extrair_totais(cd)
            recentes = totais.get(t, 0)
            if recentes > 0:
                linhas.append(
                    f'  <tribunal sigla="{t}" julgados_2025_2026="{recentes}" '
                    f'leitura="ATUALIZADA"/>'
                )
                continue
            base = sess.form_base("", [t], [], [], "01/01/2020", "31/12/2026", "DTDP")
            cd = _cdata(sess.buscar(base))
            desde_2020 = _extrair_totais(cd).get(t, 0)
            leitura = (
                "DESATUALIZADA — parou entre 2020 e 2024"
                if desde_2020 > 0
                else "CONGELADA — nada desde 2020"
            )
            linhas.append(
                f'  <tribunal sigla="{t}" julgados_2025_2026="0" '
                f'julgados_2020_2026="{desde_2020}" leitura="{leitura}"/>'
            )
        linhas.append(
            "  <referencia>Medicao de 10/07/2026: TNU/TRF1/TRF3/TRF4 "
            "atualizados; STF/STJ congelados ~2019; TRF5 ~fev/2019; TRF2 "
            "~2023.</referencia>"
        )
        linhas.append("</cobertura_cjf>")
        return "\n".join(linhas)
    except ValueError as e:
        return f"<erro>{_escape_xml(str(e))}</erro>"
    except Exception as e:
        return f"<erro>{_escape_xml(_handle_error(e))}</erro>"


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    mcp.run()
