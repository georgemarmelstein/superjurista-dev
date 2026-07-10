# -*- coding: utf-8 -*-
"""
MCP Server: TNU — Jurisprudência oficial via eproc (Standalone)

Busca na base VIVA de jurisprudência da Turma Nacional de Uniformização
(eproctnu-jur.cjf.jus.br), com inteiro teor real por documento.

Engenharia reversa em 10/07/2026 (HAR + sondagem viva):
- POST simples a ajax_paginar_resultado (sem ViewState/CSRF; cookie PHPSESSID
  apenas na busca); encoding ISO-8859-1 nos formulários.
- Inteiro teor por GET stateless (só o id do documento).
- Operadores validados empiricamente (contagens): e/ou/não minúsculos ou
  maiúsculos, espaço = e, *, prox, "frase exata".
"""

import re
import html as html_module
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

import requests
from mcp.server.fastmcp import FastMCP
from tenacity import retry, stop_after_attempt, wait_exponential

mcp = FastMCP("tnu-eproc")

# ============================================================
# CONFIGURACAO
# ============================================================

BASE = "https://eproctnu-jur.cjf.jus.br/eproc/"
URL_FORM = BASE + "externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar"
URL_BUSCA = BASE + "externo_controlador.php?acao=jurisprudencia@jurisprudencia/ajax_paginar_resultado"
URL_LISTAS = BASE + "externo_controlador.php?acao=jurisprudencia@jurisprudencia/ajax_carregar_listas_pesquisa"
URL_TEOR = BASE + "externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor&id_jurisprudencia="

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/146.0.0.0 Safari/537.36"
)

TIPOS_DOCUMENTO = {"acordao": "1", "monocratica": "2", "presidente": "3"}
ORDENACOES = {"recentes": "1", "antigos": "2"}
CAMPOS = {"ementa": "E", "inteiro_teor": "I"}
TAMANHOS_SERVIDOR = (25, 50, 100)  # opções reais do paginador


# ============================================================
# SESSAO
# ============================================================

class TNUSession:
    """Sessão do eproc: um GET inicial dá o PHPSESSID; buscas são POSTs
    simples em ISO-8859-1 (sem token). O inteiro teor nem cookie exige."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9"}
        )
        self._iniciada = False

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3))
    def iniciar(self) -> None:
        if self._iniciada:
            return
        resp = self.session.get(URL_FORM, timeout=30)
        resp.raise_for_status()
        self._iniciada = True

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3))
    def buscar(self, form: List[Tuple[str, str]]) -> str:
        """POST em ISO-8859-1 (o site nao entende UTF-8 nos filtros
        acentuados, ex.: classe processual)."""
        self.iniciar()
        corpo = urlencode(form, encoding="iso-8859-1", errors="replace")
        resp = self.session.post(
            URL_BUSCA,
            data=corpo,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=90,
        )
        resp.raise_for_status()
        resp.encoding = "iso-8859-1"
        return resp.text

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3))
    def listas(self) -> Dict:
        self.iniciar()
        resp = self.session.post(
            URL_LISTAS, data={"arrOrigem[]": "1"}, timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10),
           stop=stop_after_attempt(3))
    def inteiro_teor(self, id_documento: str) -> str:
        resp = self.session.get(URL_TEOR + id_documento, timeout=90)
        resp.raise_for_status()
        resp.encoding = "iso-8859-1"
        return resp.text


# ============================================================
# HELPERS
# ============================================================

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


def _handle_error(e: Exception) -> str:
    if isinstance(e, requests.HTTPError):
        status = e.response.status_code
        if status == 429:
            return "Limite de requisicoes do eproc excedido. Aguarde."
        if status >= 500:
            return f"eproc TNU indisponivel (HTTP {status}); tente de novo."
        return f"Falha na requisicao (HTTP {status})."
    if isinstance(e, requests.Timeout):
        return "Timeout na conexao com o eproc TNU."
    if isinstance(e, requests.ConnectionError):
        return "Nao foi possivel conectar ao eproc TNU."
    return f"{type(e).__name__}: {str(e)}"


# ============================================================
# MONTAGEM DO FORMULARIO E PARSE
# ============================================================

def _lista(valores: str) -> List[str]:
    """Divide um parametro multi-valor separado por virgula."""
    return [v.strip() for v in valores.split(",") if v.strip()]


def _montar_form(
    busca: str,
    campo: str,
    tam_pagina: int,
    pagina_servidor: int,
    ordenacao: str,
    precedentes: bool,
    caput: bool,
    agrupar: bool,
    classe: str,
    relator: str,
    processo: str,
    dj_ini: str, dj_fim: str,
    dp_ini: str, dp_fim: str,
    tipo_documento: str,
) -> List[Tuple[str, str]]:
    form: List[Tuple[str, str]] = [
        ("txtPesquisa", busca),
        ("selOrigem[]", "1"),
        ("rdoCampo", CAMPOS.get(campo, "E")),
        ("txtProcesso", processo),
        ("dtDecisaoInicio", dj_ini), ("dtDecisaoFim", dj_fim),
        ("hdnDecisaoInicio", dj_ini), ("hdnDecisaoFim", dj_fim),
        ("dtPublicacaoInicio", dp_ini), ("dtPublicacaoFim", dp_fim),
        ("hdnPublicacaoInicio", dp_ini), ("hdnPublicacaoFim", dp_fim),
        ("hdnPaginaAtual", str(pagina_servidor)),
        ("selTamanhoPagina", str(tam_pagina)),
        ("selOrdenacao", ORDENACOES.get(ordenacao, "1")),
    ]
    if precedentes:
        form.append(("chkPrecedenteRelevante", "on"))
    if caput:
        form.append(("chkCaput", "on"))
    if agrupar:
        form.append(("chkAgruparResultados", "on"))
    for c in _lista(classe):
        form.append(("selClasse[]", c))
    for r in _lista(relator):
        form.append(("selRelator[]", r))
    for t in _lista(tipo_documento):
        codigo = TIPOS_DOCUMENTO.get(t.lower())
        if not codigo:
            raise ValueError(
                f"tipo_documento invalido: {t}. "
                f"Validos: {', '.join(TIPOS_DOCUMENTO)} (ou vazio = todos)."
            )
        form.append(("selTipoDocumento[]", codigo))
    return form


def _extrair_total(html: str) -> Optional[int]:
    m = re.search(r"([\d.]+)\s*documentos? encontrados?", html)
    return int(m.group(1).replace(".", "")) if m else None


def _extrair_documentos(html: str) -> List[Dict[str, str]]:
    """Extrai os cards de resultado (id, metadados, ementa, citacao)."""
    inicios = list(re.finditer(
        r'<div class="card mb-3 resultadoItem" id="resultado([^"]+)">', html
    ))
    docs = []
    for i, m in enumerate(inicios):
        doc_id = m.group(1)
        start = m.start()
        end = inicios[i + 1].start() if i + 1 < len(inicios) else len(html)
        bloco = html[start:end]
        doc: Dict[str, str] = {"id": doc_id}

        tipo = re.search(
            r'class="resValueTipoJurisprudencia">([^<]+)<', bloco
        )
        if tipo:
            doc["tipo"] = tipo.group(1).strip()

        # pares resLabel -> resValue (a janela vai ate o proximo resLabel)
        labels = list(re.finditer(r'class="resLabel[^"]*"[^>]*>([^<]+)<', bloco))
        for j, lb in enumerate(labels):
            rotulo = " ".join(lb.group(1).split()).upper()
            fim_janela = (labels[j + 1].start()
                          if j + 1 < len(labels) else len(bloco))
            janela = bloco[lb.end():fim_janela]
            vm = re.search(
                r'class="resValue[^"]*"[^>]*>([\s\S]*?)$', janela
            )
            # a janela pode terminar no meio da tag seguinte — descarta o toco
            valor = _limpar_html(
                re.sub(r"<[^>]*$", "", vm.group(1))
            ) if vm else ""
            if not valor:
                continue
            chave = {
                "PROCESSO": "processo",
                "UF": "uf",
                "DATA DO JULGAMENTO": "data_julgamento",
                "DATA DA PUBLICAÇÃO": "data_publicacao",
                "DATA DA PUBLICACAO": "data_publicacao",
                "RELATOR": "relator",
                "DECISÃO": "decisao",
                "DECISAO": "decisao",
                "EMENTA": "ementa",
            }.get(rotulo)
            if chave and chave not in doc:
                doc[chave] = valor

        # citacao oficial pronta (data-citacao, entity-escapada no HTML)
        cit = re.search(r'data-citacao="([\s\S]*?)"', bloco)
        if cit:
            citacao = html_module.unescape(cit.group(1))
            # a linha oficial e o ultimo parentetico "(TNU, ...)"
            oficial = re.findall(r"\((TNU,[\s\S]*?)\)", citacao)
            if oficial:
                doc["citacao_oficial"] = "(" + " ".join(oficial[-1].split()) + ")"
            if "ementa" not in doc:
                doc["ementa"] = " ".join(
                    re.sub(r"^EMENTA:\s*", "", citacao).split()
                )

        if doc.get("processo") or doc.get("ementa"):
            docs.append(doc)
    return docs


def _executar_busca(
    busca: str,
    campo: str,
    max_resultados: int,
    pagina: int,
    ordenacao: str,
    precedentes: bool,
    caput: bool,
    agrupar: bool,
    classe: str,
    relator: str,
    processo: str,
    dj_ini: str, dj_fim: str,
    dp_ini: str, dp_fim: str,
    tipo_documento: str,
) -> Tuple[List[Dict[str, str]], Optional[int]]:
    """Busca com paginacao: o servidor pagina em 25/50/100; o slice pedido
    ([pagina] x [max_resultados]) e coletado em 1-2 requisicoes."""
    campo = campo.strip().lower()
    if campo not in CAMPOS:
        raise ValueError('campo deve ser "ementa" ou "inteiro_teor".')
    if ordenacao.strip().lower() not in ORDENACOES:
        raise ValueError('ordenacao deve ser "recentes" ou "antigos".')
    for rotulo, (a, b) in {
        "julgamento": (dj_ini, dj_fim), "publicacao": (dp_ini, dp_fim)
    }.items():
        if bool(a) != bool(b):
            raise ValueError(
                f"Faixa de data de {rotulo}: informe inicio E fim (DD/MM/AAAA)."
            )
    max_resultados = max(1, min(int(max_resultados), 50))
    pagina = max(1, int(pagina))

    alvo_ini = (pagina - 1) * max_resultados
    alvo_fim = alvo_ini + max_resultados
    tam = next((t for t in TAMANHOS_SERVIDOR if t >= alvo_fim), 100)

    sess = TNUSession()
    docs: List[Dict[str, str]] = []
    total: Optional[int] = None
    pag_servidor = alvo_ini // tam + 1
    while len(docs) < max_resultados:
        form = _montar_form(
            busca, campo, tam, pag_servidor,
            ordenacao.strip().lower(), precedentes, caput, agrupar,
            classe, relator, processo, dj_ini, dj_fim, dp_ini, dp_fim,
            tipo_documento,
        )
        html = sess.buscar(form)
        if total is None:
            total = _extrair_total(html)
        pagina_docs = _extrair_documentos(html)
        if not pagina_docs:
            break
        base_abs = (pag_servidor - 1) * tam
        for j, d in enumerate(pagina_docs):
            absoluto = base_abs + j
            if alvo_ini <= absoluto < alvo_fim:
                docs.append(d)
        if base_abs + len(pagina_docs) >= alvo_fim or len(pagina_docs) < tam:
            break
        pag_servidor += 1
    return docs, total


# ============================================================
# TOOLS
# ============================================================

@mcp.tool()
def buscar_tnu(
    busca: str,
    campo: str = "ementa",
    max_resultados: int = 10,
    pagina: int = 1,
    ordenacao: str = "recentes",
    somente_precedentes_relevantes: bool = False,
    somente_caput: bool = False,
    agrupar_resultados: bool = True,
    classe: str = "",
    relator: str = "",
    processo: str = "",
    data_julgamento_inicio: str = "",
    data_julgamento_fim: str = "",
    data_publicacao_inicio: str = "",
    data_publicacao_fim: str = "",
    tipo_documento: str = "",
) -> str:
    """
    Busca jurisprudencia na base OFICIAL E VIVA da TNU (Turma Nacional de
    Uniformizacao) via eproc — atualizada ate a semana corrente (verificado
    em 10/07/2026), com INTEIRO TEOR real por documento (obter_inteiro_teor_tnu)
    e citacao oficial pronta em cada resultado.

    E a fonte preferencial para jurisprudencia da TNU. (O portal unificado do
    CJF tambem cobre a TNU, mas sem inteiro teor nem filtro de precedentes
    relevantes; STF/STJ nao estao aqui — use o BNP para precedentes
    qualificados.)

    SINTAXE DE BUSCA (validada empiricamente em 10/07/2026; operadores
    case-insensitive; acentos ignorados):
    | Operador | Efeito                                | Exemplo                        |
    |----------|---------------------------------------|--------------------------------|
    | (espaco) | E implicito                           | aposentadoria rural            |
    | e        | Ambos os termos                       | aposentadoria e rural          |
    | ou       | Qualquer dos termos                   | aposentadoria ou pensao        |
    | nao      | Exclui o termo seguinte               | aposentadoria nao rural        |
    | prox     | Termos proximos (sem numero: prox5=0!)| aposentadoria prox rural       |
    | *        | Wildcard em sufixo OU prefixo         | aposentad*  /  *doenca         |
    | "..."    | Frase exata                           | "prescricao intercorrente"     |

    REGRAS DE LEITURA HONESTA (obrigatorias):
    1. So cite o que a ferramenta devolveu — nunca complete numero de processo,
       relator, data ou tese de memoria. A linha <citacao_oficial> de cada
       resultado e a forma correta de citar.
    2. O acervo indexado e de ACORDAOS da TNU (nos testes, tipos "monocratica"
       e "presidente" retornaram zero). Zero resultado aqui NAO exclui
       jurisprudencia de outros orgaos: STF/STJ estao no BNP; TRF5 no JULIA;
       TRFs/TRU no portal unificado do CJF.
    3. Antes de citacao formal, confirme no inteiro teor
       (obter_inteiro_teor_tnu com o id do resultado).

    Args:
        busca: Termos com a sintaxe acima.
        campo: Onde pesquisar: "ementa" (default desta ferramenta — mais
               preciso) ou "inteiro_teor" (o default do site: corpus completo,
               ~5x mais documentos, mais ruido).
        max_resultados: Resultados por pagina desta ferramenta (1-50, default 10).
        pagina: Pagina do resultado (1 = primeiros max_resultados...).
        ordenacao: "recentes" (default) ou "antigos".
        somente_precedentes_relevantes: True = so a jurisprudencia selecionada
               pela TNU como precedente relevante (representativos).
        somente_caput: True = pesquisa so no caput da ementa.
        agrupar_resultados: True (default, igual ao site) = o servidor
               deduplica documentos quase identicos do mesmo processo;
               False = todos os registros brutos (total um pouco maior).
        classe: Classe(s) processual(is) EXATA(s) como em listar_filtros_tnu,
               separadas por virgula se mais de uma (ex.: "Pedido de
               Uniformização de Interpretação de Lei (Turma)").
        relator: Nome(s) COMPLETO(s) em maiusculas como em listar_filtros_tnu,
               separados por virgula se mais de um (ex.: "ODILON ROMANO NETO").
        processo: Numero do processo (com ou sem mascara CNJ).
        data_julgamento_inicio: Faixa da data de julgamento, DD/MM/AAAA
               (informe inicio e fim).
        data_julgamento_fim: Idem.
        data_publicacao_inicio: Faixa da data de publicacao/disponibilizacao,
               DD/MM/AAAA (informe inicio e fim).
        data_publicacao_fim: Idem.
        tipo_documento: "" (todos, default), ou lista separada por virgula de:
               "acordao", "monocratica", "presidente".

    Returns:
        XML com <total_encontrado> e <item> contendo id (a chave do inteiro
        teor), processo, uf, tipo, data_julgamento, data_publicacao, relator,
        decisao, ementa (truncada em 6000 chars) e citacao_oficial.
    """
    try:
        docs, total = _executar_busca(
            busca, campo, max_resultados, pagina, ordenacao,
            somente_precedentes_relevantes, somente_caput,
            agrupar_resultados, classe, relator, processo,
            data_julgamento_inicio, data_julgamento_fim,
            data_publicacao_inicio, data_publicacao_fim,
            tipo_documento,
        )
    except ValueError as e:
        return f"<erro>{_escape_xml(str(e))}</erro>"
    except Exception as e:
        return f"<erro>{_escape_xml(_handle_error(e))}</erro>"

    linhas = [
        f'<jurisprudencia_tnu busca="{_escape_xml(busca)}" '
        f'campo="{_escape_xml(campo)}" pagina="{max(1, int(pagina))}" '
        f'itens="{len(docs)}">'
    ]
    if total is not None:
        linhas.append(f"  <total_encontrado>{total}</total_encontrado>")
    if not docs:
        linhas.append("  <mensagem>Nenhum resultado nesta pagina.</mensagem>")
    for i, doc in enumerate(docs, 1):
        linhas.append(
            f'  <item indice="{i}" id="{_escape_xml(doc.get("id", ""))}">'
        )
        for tag in ("processo", "uf", "tipo", "data_julgamento",
                    "data_publicacao", "relator"):
            if doc.get(tag):
                linhas.append(f"    <{tag}>{_escape_xml(doc[tag])}</{tag}>")
        if doc.get("decisao"):
            linhas.append(
                f"    <decisao>{_escape_xml(_truncar(doc['decisao'], 2000))}</decisao>"
            )
        if doc.get("ementa"):
            linhas.append(
                f"    <ementa>{_escape_xml(_truncar(doc['ementa']))}</ementa>"
            )
        if doc.get("citacao_oficial"):
            linhas.append(
                f"    <citacao_oficial>{_escape_xml(doc['citacao_oficial'])}</citacao_oficial>"
            )
        linhas.append("  </item>")
    linhas.append("</jurisprudencia_tnu>")
    return "\n".join(linhas)


@mcp.tool()
def obter_inteiro_teor_tnu(
    id_documento: str,
    max_chars: int = 30000,
    inicio: int = 0,
) -> str:
    """
    Recupera o INTEIRO TEOR real (relatorio, voto e dispositivo) de um
    documento da TNU, pelo id retornado em buscar_tnu. Acesso direto e
    stateless — nao precisa repetir a busca.

    Documentos longos: o texto vem em janelas de max_chars; se o retorno
    terminar com [CONTINUA...], chame de novo com inicio = valor indicado.

    So cite o que este texto contem; a citacao formal usa a linha
    <citacao_oficial> do resultado da busca.

    Args:
        id_documento: O atributo id do <item> de buscar_tnu (ex.:
                      771751379005581667765574507389).
        max_chars: Tamanho maximo da janela de texto (default 30000).
        inicio: Posicao inicial da janela (para continuar um documento longo).

    Returns:
        Texto puro do inteiro teor (janela pedida), com cabecalho
        identificando o documento e a faixa retornada.
    """
    try:
        sess = TNUSession()
        html = sess.inteiro_teor(id_documento.strip())
        texto = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", html)
        texto = re.sub(r"<br\s*/?>", "\n", texto)
        texto = re.sub(r"</(p|div|tr|li|h\d)>", "\n", texto)
        texto = re.sub(r"<[^>]+>", " ", texto)
        texto = html_module.unescape(texto)
        texto = re.sub(r"[ \t]+", " ", texto)
        texto = re.sub(r"\n\s*\n+", "\n\n", texto).strip()

        inicio = max(0, int(inicio))
        max_chars = max(1000, min(int(max_chars), 100000))
        janela = texto[inicio:inicio + max_chars]
        cabecalho = (
            f"[INTEIRO TEOR TNU — documento {id_documento} | "
            f"chars {inicio}-{inicio + len(janela)} de {len(texto)}]\n\n"
        )
        rodape = ""
        if inicio + len(janela) < len(texto):
            rodape = (
                f"\n\n[CONTINUA... chame de novo com inicio={inicio + len(janela)}]"
            )
        return cabecalho + janela + rodape
    except Exception as e:
        return f"<erro>{_escape_xml(_handle_error(e))}</erro>"


@mcp.tool()
def gerar_relatorio_tnu(
    busca: str,
    campo: str = "ementa",
    max_resultados: int = 10,
    pagina: int = 1,
    ordenacao: str = "recentes",
    somente_precedentes_relevantes: bool = False,
    agrupar_resultados: bool = True,
    classe: str = "",
    relator: str = "",
    data_julgamento_inicio: str = "",
    data_julgamento_fim: str = "",
    data_publicacao_inicio: str = "",
    data_publicacao_fim: str = "",
) -> str:
    """
    Busca jurisprudencia da TNU e devolve relatorio Markdown formatado para
    apresentar a um humano. Para analise programatica prefira buscar_tnu (XML).

    Sintaxe, filtros e REGRAS DE LEITURA HONESTA identicos aos de buscar_tnu
    (leia la). Base viva da TNU via eproc; citacao oficial em cada item.

    Args:
        busca: Termos de busca (sintaxe de buscar_tnu).
        campo: "ementa" (default) ou "inteiro_teor".
        max_resultados: Itens no relatorio (1-20, default 10).
        pagina: Pagina do resultado.
        ordenacao: "recentes" (default) ou "antigos".
        somente_precedentes_relevantes: True = so precedentes relevantes.
        agrupar_resultados: True (default, igual ao site) = deduplica
               documentos quase identicos do mesmo processo.
        classe: Classe(s) exata(s), separadas por virgula (ver listar_filtros_tnu).
        relator: Nome(s) completo(s) em maiusculas, separados por virgula
               (ver listar_filtros_tnu).
        data_julgamento_inicio: Faixa DD/MM/AAAA (inicio e fim).
        data_julgamento_fim: Idem.
        data_publicacao_inicio: Faixa DD/MM/AAAA (inicio e fim).
        data_publicacao_fim: Idem.

    Returns:
        Relatorio em Markdown.
    """
    try:
        docs, total = _executar_busca(
            busca, campo, min(int(max_resultados), 20), pagina, ordenacao,
            somente_precedentes_relevantes, False, agrupar_resultados,
            classe, relator, "",
            data_julgamento_inicio, data_julgamento_fim,
            data_publicacao_inicio, data_publicacao_fim, "",
        )
    except ValueError as e:
        return f"**Erro:** {e}"
    except Exception as e:
        return f"**Erro:** {_handle_error(e)}"

    linhas = [
        "# Relatorio de Jurisprudencia — TNU (eproc)",
        "",
        f"**Busca:** `{busca}` (campo: {campo})",
        f"**Total na base:** {total if total is not None else 'n/i'} | "
        f"**Pagina:** {max(1, int(pagina))} | **Itens:** {len(docs)}",
        "",
        "---",
        "",
    ]
    if not docs:
        linhas.append("*Nenhum documento nesta pagina.*")
        return "\n".join(linhas)
    for i, doc in enumerate(docs, 1):
        linhas.append(f"## {i}. {doc.get('processo', 'N/I')}")
        linhas.append("")
        for rotulo, chave in [
            ("Tipo", "tipo"), ("UF", "uf"), ("Relator(a)", "relator"),
            ("Julgamento", "data_julgamento"),
            ("Publicacao", "data_publicacao"),
        ]:
            if doc.get(chave):
                linhas.append(f"**{rotulo}:** {doc[chave]}")
        linhas.append("")
        if doc.get("ementa"):
            linhas.extend(["### Ementa", "", f"> {_truncar(doc['ementa'], 4000)}", ""])
        if doc.get("decisao"):
            linhas.extend(["### Decisao", "", f"> {_truncar(doc['decisao'], 1500)}", ""])
        if doc.get("citacao_oficial"):
            linhas.extend([f"**Citacao:** {doc['citacao_oficial']}", ""])
        linhas.append(f"*Inteiro teor: obter_inteiro_teor_tnu(\"{doc.get('id','')}\")*")
        linhas.extend(["", "---", ""])
    linhas.append(
        "*Base viva da TNU via eproc — confirme citacoes no inteiro teor.*"
    )
    return "\n".join(linhas)


@mcp.tool()
def listar_filtros_tnu() -> str:
    """
    Lista os filtros vigentes da base TNU/eproc — classes processuais e
    relatores ATUAIS (consultados ao vivo), tipos de documento, operadores
    validados e dicas de uso. Consulte antes de filtrar por classe ou relator
    (os valores devem ser EXATOS).

    Returns:
        XML com classes, relatores, tipos, operadores e observacoes de
        cobertura da base.
    """
    linhas = ["<filtros_tnu>"]
    try:
        dados = TNUSession().listas()
        classes = list(dados.get("arrClasse", {}).keys())
        relatores = list(dados.get("arrRelator", {}).keys())
        linhas.append('  <origem_listas>consulta viva ao eproc</origem_listas>')
    except Exception:
        classes, relatores = [], []
        linhas.append(
            "  <origem_listas>indisponivel agora — tente de novo</origem_listas>"
        )
    linhas.append("  <classes>")
    for c in classes:
        linhas.append(f"    <classe>{_escape_xml(c)}</classe>")
    linhas.append("  </classes>")
    linhas.append("  <relatores>")
    for r in relatores:
        linhas.append(f"    <relator>{_escape_xml(r)}</relator>")
    linhas.append("  </relatores>")

    linhas.append("  <tipos_documento>")
    for nome in TIPOS_DOCUMENTO:
        obs = (' obs="retornou 0 nos testes de 10/07/2026 — acervo indexado '
               'e de acordaos"') if nome != "acordao" else ""
        linhas.append(f'    <tipo{obs}>{nome}</tipo>')
    linhas.append("  </tipos_documento>")

    linhas.append("  <operadores validados_em=\"10/07/2026\">")
    ops = [
        ("espaco", "E implicito", "aposentadoria rural"),
        ("e", "Ambos os termos (case-insensitive)", "aposentadoria e rural"),
        ("ou", "Qualquer dos termos", "aposentadoria ou pensao"),
        ("nao", "Exclui o termo (com ou sem acento)", "aposentadoria nao rural"),
        ("prox", "Termos proximos — SEM numero (prox5 nao existe)", "aposentadoria prox rural"),
        ("*", "Wildcard em sufixo ou prefixo", "aposentad* / *doenca"),
        ('"..."', "Frase exata", '"prescricao intercorrente"'),
    ]
    for cod, desc, ex in ops:
        linhas.append(
            f'    <operador codigo="{_escape_xml(cod)}" exemplo="{_escape_xml(ex)}">{desc}</operador>'
        )
    linhas.append("  </operadores>")

    linhas.append(
        "  <cobertura>Base OFICIAL e VIVA da TNU (eproc) — em 10/07/2026 "
        "havia publicacoes da semana corrente. Acervo indexado: acordaos da "
        "TNU. Nao cobre STF/STJ (use BNP) nem TRFs/TRU (use o portal "
        "unificado do CJF).</cobertura>"
    )
    linhas.append(
        "  <dica>campo=inteiro_teor pesquisa o corpus completo (~5x mais "
        "docs que a ementa); somente_precedentes_relevantes=True traz so os "
        "representativos selecionados pela TNU; agrupar_resultados=True "
        "(default, igual ao site) deduplica documentos quase identicos do "
        "mesmo processo; classe/relator/tipo_documento aceitam varios "
        "valores separados por virgula.</dica>"
    )
    linhas.append("</filtros_tnu>")
    return "\n".join(linhas)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    mcp.run()
