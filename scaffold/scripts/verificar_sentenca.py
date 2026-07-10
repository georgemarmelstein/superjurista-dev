#!/usr/bin/env python3
"""verificar_sentenca.py - Gate determinístico do pipeline de sentença (v3.0).

Substitui a validação por frase-âncora feita pelo ORQUESTRADOR LENDO os
documentos (v2.2): aqui quem confere os marcadores é um script — o orquestrador
só lê este output curto. Também é a base da RETOMADA: o modo varredura lista
quais etapas já têm artefato válido (pular) e quais estão pendentes (rodar).

Marcadores casados com NORMALIZAÇÃO DE ACENTOS/CAIXA: a v2.2 exigia
"## ULTIMOS ATOS" e o artefato real (bom) traz "## ÚLTIMOS ATOS" — a âncora
literal reprovava documento correto. A exigência de acentuação continua, mas
como checagem própria (o documento precisa TER acentos), não na âncora.

Uso:
  python scripts/verificar_sentenca.py <workspace> [--numero N]
      → varredura: estado por etapa + linha "PENDENTES: ..." (exit 0)
  python scripts/verificar_sentenca.py <workspace> --etapa relatorio
      → valida UMA etapa (exit 0 = válida; 1 = ausente/inválida)
  python scripts/verificar_sentenca.py <workspace> --gate
      → gate final: exit 1 se QUALQUER etapa pendente/ inválida

--numero é inferido do nome da pasta quando ela segue o padrão CNJ.
"""
import argparse
import os
import re
import sys
import unicodedata

# etapa -> (sufixo do arquivo, inicio, fim, contem[], tamanho mínimo em chars)
ETAPAS = {
    "linha-tempo": ("-linha-tempo.md", "# linha do tempo processual",
                    "e o que satisfaz extrair dos autos.",
                    ["marcos processuais", "timeline completa"], 500),
    "relatorio": ("-relatorio.md", "relatorio",
                  "e o que havia de relevante a relatar.", [], 500),
    "analise": ("-analise.md", "vamos comecar. preciso pensar profundamente sobre esse caso.",
                "pronto.", [], 500),
    "fundamentacao": ("-fundamentacao.md", "fundamentacao",
                      "juiz federal", ["dispositivo"], 500),
    "sentenca": ("-sentenca.md", "relatorio",
                 "juiz federal", ["fundamentacao", "dispositivo"], 1000),
}
RE_CNJ = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
RE_ACENTO = re.compile(r"[áéíóúâêôãõàçÁÉÍÓÚÂÊÔÃÕÀÇ]")


def _norm(s):
    """minúsculo e sem acentos — âncora robusta a variação de acentuação/caixa."""
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").casefold()


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
    problemas = []
    n = _norm(texto)
    if len(texto) < minimo:
        problemas.append(f"curto demais ({len(texto)} chars < {minimo})")
    if inicio not in n[:400]:
        problemas.append(f"não abre com o marcador ({inicio!r})")
    if fim not in n[-400:]:
        problemas.append(f"não fecha com o marcador ({fim!r})")
    for c in contem:
        if c not in n:
            problemas.append(f"sem a seção obrigatória ({c!r})")
    if not RE_ACENTO.search(texto):
        problemas.append("sem acentos de português (documento jurídico exige)")
    return problemas


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
    ap.add_argument("--etapa", choices=sorted(ETAPAS), help="valida só esta etapa (exit-coded)")
    ap.add_argument("--gate", action="store_true", help="exit 1 se qualquer etapa pendente/inválida")
    args = ap.parse_args()

    if not os.path.isdir(args.workspace):
        print(f"[ERRO] workspace inexistente: {args.workspace}")
        sys.exit(2)
    numero = args.numero or inferir_numero(args.workspace)
    if not numero:
        print("[ERRO] número CNJ não inferível do nome da pasta — passe --numero")
        sys.exit(2)

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
