#!/usr/bin/env python3
"""verificar_sentenca.py - Gate determinístico do pipeline de sentença (gate v2).

Substitui a validação por frase-âncora feita pelo ORQUESTRADOR LENDO os
documentos (v2.2): aqui quem confere os marcadores é um script — o orquestrador
só lê este output curto. Também é a base da RETOMADA: o modo varredura lista
quais etapas já têm artefato válido (pular) e quais estão pendentes (rodar).

Gate v2 — Sentença Inteligente (plano 2026-07-11, docs/plans/):
  - etapa `triagem` entre relatório e análise ($NUMERO-triagem.md, contrato C2);
  - modo --rota: parseia o bloco ```json da triagem e imprime ROTA:/TEMA:/FATO:
    para o orquestrador despachar os trilhos condicionais;
  - estado ESCALAR (contratos C3/C4): análise que fecha com "ESCALAR: <trilhos>"
    + "MOTIVO: <uma linha>" em vez de "Pronto." é válida em formato, mas
    incompleta POR DESIGN → --etapa analise sai com exit 3; na varredura e no
    --gate imprime "[ESCALAR] analise" e conta como pendente.

Marcadores casados com NORMALIZAÇÃO DE ACENTOS/CAIXA: a v2.2 exigia
"## ULTIMOS ATOS" e o artefato real (bom) traz "## ÚLTIMOS ATOS" — a âncora
literal reprovava documento correto. A exigência de acentuação continua, mas
como checagem própria (o documento precisa TER acentos), não na âncora.
ATENÇÃO (convenção deste script, diferente do motor verificar_pipeline.py):
o lado do dict NÃO é normalizado — as âncoras de ETAPAS são escritas JÁ
normalizadas (minúsculas, sem acentos).

Uso:
  python scripts/verificar_sentenca.py <workspace> [--numero N]
      → varredura: estado por etapa + linha "PENDENTES: ..." (exit 0)
  python scripts/verificar_sentenca.py <workspace> --etapa relatorio
      → valida UMA etapa (exit 0 = válida; 1 = ausente/inválida)
  python scripts/verificar_sentenca.py <workspace> --etapa analise
      → idem, com terceiro estado: exit 3 = ESCALAR
        ("[ESCALAR] analise: <trilhos> — <motivo>" — o orquestrador roda o
        trilho pedido e redespacha a análise; máx. 1 escalada por processo)
  python scripts/verificar_sentenca.py <workspace> --rota
      → lê o contrato C2 da triagem e imprime "ROTA: ..." (+ linhas TEMA:/FATO:);
        em rota direta ([]) imprime também "JUSTIFICATIVA: <justificativa_rotina>"
        — o resumo da Etapa 6 cita a justificativa sem ler o documento
        exit 0 = rota válida; 1 = triagem ausente/JSON inválido/contrato violado
  python scripts/verificar_sentenca.py <workspace> --gate
      → gate final: exit 1 se QUALQUER etapa pendente/inválida

--numero é inferido do nome da pasta quando ela segue o padrão CNJ.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

# etapa -> (sufixo do arquivo, inicio, fim, contem[], tamanho mínimo em chars)
# Âncoras JÁ normalizadas (minúsculas, sem acento) — só o documento é normalizado.
ETAPAS = {
    "linha-tempo": ("-linha-tempo.md", "# linha do tempo processual",
                    "e o que satisfaz extrair dos autos.",
                    ["marcos processuais", "timeline completa"], 500),
    "relatorio": ("-relatorio.md", "relatorio",
                  "e o que havia de relevante a relatar.", [], 500),
    "triagem": ("-triagem.md", "# triagem cognitiva do processo",
                "triagem concluida.", ["evidencias", '"rota"'], 400),
    "analise": ("-analise.md", "vamos comecar. preciso pensar profundamente sobre esse caso.",
                "pronto.", [], 500),
    "fundamentacao": ("-fundamentacao.md", "fundamentacao",
                      "juiz federal", ["dispositivo"], 500),
    "sentenca": ("-sentenca.md", "relatorio",
                 "juiz federal", ["fundamentacao", "dispositivo"], 1000),
}
TRILHOS_VALIDOS = ("pesquisa", "probatica")
JANELA_ESCALAR = 600  # o fecho ESCALAR mora no FINAL do documento (contrato C3)
RE_CNJ = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
RE_ACENTO = re.compile(r"[áéíóúâêôãõàçÁÉÍÓÚÂÊÔÃÕÀÇ]")
RE_ESCALAR = re.compile(r"^escalar:(.*)$", re.MULTILINE)
RE_BLOCO_JSON = re.compile(r"```json\s*(.*?)```", re.DOTALL)


def _norm(s):
    """minúsculo e sem acentos — âncora robusta a variação de acentuação/caixa."""
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").casefold()


def _conferir(texto, inicio, fim, contem, minimo, checar_fim=True):
    """Checagens de formato compartilhadas; devolve a lista de problemas."""
    problemas = []
    n = _norm(texto)
    if len(texto) < minimo:
        problemas.append(f"curto demais ({len(texto)} chars < {minimo})")
    if inicio not in n[:400]:
        problemas.append(f"não abre com o marcador ({inicio!r})")
    if checar_fim and fim not in n[-400:]:
        problemas.append(f"não fecha com o marcador ({fim!r})")
    for c in contem:
        if c not in n:
            problemas.append(f"sem a seção obrigatória ({c!r})")
    if not RE_ACENTO.search(texto):
        problemas.append("sem acentos de português (documento jurídico exige)")
    return problemas


def verificar_etapa(workspace, numero, etapa):
    """Lista de problemas (vazia = válida); None = arquivo AUSENTE."""
    sufixo, inicio, fim, contem, minimo = ETAPAS[etapa]
    caminho = os.path.join(workspace, f"{numero}{sufixo}")
    if not os.path.exists(caminho):
        return None
    try:
        texto = open(caminho, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        return [f"ilegível: {e}"]
    return _conferir(texto, inicio, fim, contem, minimo)


def detectar_escalar(texto):
    """Detecta o fecho ESCALAR (contrato C3) no final do documento de análise.

    Procura, nos últimos JANELA_ESCALAR chars do texto NORMALIZADO, uma LINHA
    que COMEÇA com "escalar:" (ancorada em linha — o corpo apenas MENCIONAR a
    palavra não dispara). Retorna (trilhos, motivo): trilhos é a lista de
    tokens declarados após "escalar:" (a validação contra TRILHOS_VALIDOS é
    do chamador); motivo é o texto da linha seguinte "motivo: ..." (ou "").
    Sem fecho ESCALAR → None.
    """
    n = _norm(texto)
    janela = max(0, len(n) - JANELA_ESCALAR)
    # finditer com pos: "^" só casa em início REAL de linha (pós-\n), nunca no
    # meio de uma linha cortada pela janela — a ancoragem em linha é preservada.
    for m in RE_ESCALAR.finditer(n, janela):
        trilhos = m.group(1).split()
        motivo = ""
        for linha in n[m.end():].splitlines():
            linha = linha.strip()
            if not linha:
                continue
            if linha.startswith("motivo:"):
                motivo = linha[len("motivo:"):].strip()
            break
        return trilhos, motivo
    return None


def avaliar_analise(workspace, numero):
    """Estado da etapa `analise` considerando a válvula ESCALAR (C3/C4).

    Retorna (status, dados):
      ("ausente", None)               — arquivo inexistente (exit 1)
      ("invalida", [problemas])       — formato quebrado, inclusive trilho
                                        ESCALAR inválido (exit 1)
      ("escalar", (trilhos, motivo))  — válida em formato, incompleta por
                                        design (exit 3)
      ("ok", None)                    — completa e válida (exit 0)
    """
    sufixo, inicio, fim, contem, minimo = ETAPAS["analise"]
    caminho = os.path.join(workspace, f"{numero}{sufixo}")
    if not os.path.exists(caminho):
        return "ausente", None
    try:
        texto = open(caminho, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        return "invalida", [f"ilegível: {e}"]
    escalar = detectar_escalar(texto)
    if escalar is None:
        problemas = _conferir(texto, inicio, fim, contem, minimo)
        return ("invalida", problemas) if problemas else ("ok", None)
    trilhos, motivo = escalar
    # ESCALAR dispensa o fecho normal ("pronto."); as demais checagens valem
    # e têm precedência como INVALIDA.
    problemas = _conferir(texto, inicio, fim, contem, minimo, checar_fim=False)
    invalidos = [t for t in trilhos if t not in TRILHOS_VALIDOS]
    if invalidos:
        problemas.append(f"ESCALAR com trilho inválido: {invalidos[0]}")
    elif not trilhos:
        problemas.append("ESCALAR sem trilho declarado")
    if problemas:
        return "invalida", problemas
    return "escalar", (trilhos, motivo)


def validar_rota(dados):
    """Valida o contrato C2; devolve a mensagem da violação, ou None se válido."""
    if not isinstance(dados, dict):
        return "bloco json não é um objeto"
    rota = dados.get("rota")
    if not isinstance(rota, list):
        return "campo 'rota' ausente ou não é lista"
    for t in rota:
        if t not in TRILHOS_VALIDOS:
            return f"trilho desconhecido na rota: {t!r} (aceitos: pesquisa, probatica)"
    temas = dados.get("temas_pesquisa")
    fatos = dados.get("fatos_probatorios")
    if temas is not None and not isinstance(temas, list):
        return "'temas_pesquisa' deve ser lista"
    if fatos is not None and not isinstance(fatos, list):
        return "'fatos_probatorios' deve ser lista"
    if "pesquisa" in rota and not [t for t in (temas or []) if str(t).strip()]:
        return "rota inclui 'pesquisa' mas temas_pesquisa está vazio"
    if "probatica" in rota and not [f for f in (fatos or []) if str(f).strip()]:
        return "rota inclui 'probatica' mas fatos_probatorios está vazio"
    if not rota:
        j = dados.get("justificativa_rotina")
        if not isinstance(j, str) or not j.strip():
            return "rota direta ([]) exige justificativa_rotina não-vazia (certificação afirmativa)"
    return None


def modo_rota(workspace, numero):
    """Modo --rota: parseia o contrato C2 da triagem e imprime ROTA:/TEMA:/FATO:.

    Em rota direta ([]) imprime também "JUSTIFICATIVA: <justificativa_rotina>"
    — assim o orquestrador cita a certificação de rotina no resumo final sem
    ler o documento da triagem.
    Devolve o exit code: 0 = rota válida; 1 = triagem ausente/JSON inválido/
    contrato violado (a mensagem [ERRO] diz o quê).
    """
    caminho = os.path.join(workspace, f"{numero}-triagem.md")
    if not os.path.exists(caminho):
        print("[ERRO] triagem ausente")
        return 1
    try:
        texto = open(caminho, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"[ERRO] triagem ilegível: {e}")
        return 1
    m = RE_BLOCO_JSON.search(texto)
    if not m:
        print("[ERRO] rota invalida: triagem sem bloco ```json (contrato C2)")
        return 1
    try:
        dados = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"[ERRO] rota invalida: JSON malformado ({e})")
        return 1
    erro = validar_rota(dados)
    if erro:
        print(f"[ERRO] rota invalida: {erro}")
        return 1
    rota = list(dict.fromkeys(dados["rota"]))  # dedup preservando ordem
    print("ROTA: " + (" ".join(rota) if rota else "direta"))
    if not rota:
        # validar_rota já garantiu justificativa_rotina não-vazia em rota direta
        print(f"JUSTIFICATIVA: {dados['justificativa_rotina'].strip()}")
    for tema in dados.get("temas_pesquisa") or []:
        print(f"TEMA: {tema}")
    for fato in dados.get("fatos_probatorios") or []:
        print(f"FATO: {fato}")
    return 0


def inferir_numero(workspace):
    m = RE_CNJ.search(os.path.basename(os.path.abspath(workspace)))
    return m.group(0) if m else None


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Gate determinístico do pipeline de sentença.")
    ap.add_argument("workspace")
    ap.add_argument("--numero", help="número CNJ (inferido do nome da pasta se omitido)")
    ap.add_argument("--etapa", choices=sorted(ETAPAS),
                    help="valida só esta etapa (exit-coded; analise pode sair 3 = ESCALAR)")
    ap.add_argument("--rota", action="store_true",
                    help="parseia o contrato C2 da triagem e imprime ROTA:/TEMA:/FATO: "
                         "(+ JUSTIFICATIVA: em rota direta)")
    ap.add_argument("--gate", action="store_true", help="exit 1 se qualquer etapa pendente/inválida")
    args = ap.parse_args()

    if not os.path.isdir(args.workspace):
        print(f"[ERRO] workspace inexistente: {args.workspace}")
        sys.exit(2)
    numero = args.numero or inferir_numero(args.workspace)
    if not numero:
        print("[ERRO] número CNJ não inferível do nome da pasta — passe --numero")
        sys.exit(2)

    if args.rota:
        sys.exit(modo_rota(args.workspace, numero))

    if args.etapa == "analise":
        status, dados = avaliar_analise(args.workspace, numero)
        if status == "ausente":
            print("[AUSENTE] analise")
            sys.exit(1)
        if status == "invalida":
            print("[INVALIDA] analise: " + "; ".join(dados))
            sys.exit(1)
        if status == "escalar":
            trilhos, motivo = dados
            print(f"[ESCALAR] analise: {' '.join(trilhos)} — {motivo}")
            sys.exit(3)
        print("[OK] analise")
        sys.exit(0)

    if args.etapa:
        r = verificar_etapa(args.workspace, numero, args.etapa)
        if r is None:
            print(f"[AUSENTE] {args.etapa}")
            sys.exit(1)
        if r:
            print(f"[INVALIDA] {args.etapa}: " + "; ".join(r))
            sys.exit(1)
        print(f"[OK] {args.etapa}")
        sys.exit(0)

    pendentes = []
    print(f"[INICIO] {numero} -> verificação das {len(ETAPAS)} etapas")
    for etapa in ETAPAS:
        if etapa == "analise":
            status, dados = avaliar_analise(args.workspace, numero)
            if status == "escalar":
                print("[ESCALAR] analise")
                pendentes.append(etapa)
                continue
            r = None if status == "ausente" else ([] if status == "ok" else dados)
        else:
            r = verificar_etapa(args.workspace, numero, etapa)
        if r is None:
            print(f"[AUSENTE] {etapa}")
            pendentes.append(etapa)
        elif r:
            print(f"[INVALIDA] {etapa}: " + "; ".join(r))
            pendentes.append(etapa)
        else:
            print(f"[OK] {etapa}")
    print("PENDENTES: " + (" ".join(pendentes) if pendentes else "(nenhuma)"))
    print(f"[FIM] {len(ETAPAS) - len(pendentes)}/{len(ETAPAS)} válidas")
    sys.exit(1 if (args.gate and pendentes) else 0)


if __name__ == "__main__":
    main()
