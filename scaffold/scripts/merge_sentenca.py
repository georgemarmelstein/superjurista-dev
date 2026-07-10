#!/usr/bin/env python3
"""merge_sentenca.py - Etapa 5 do pipeline de sentença, determinística (v3.0).

Na v2.2 o ORQUESTRADOR fazia o merge lendo os dois documentos inteiros no
próprio contexto (Read + Read + Write). A operação é uma concatenação — não
precisa de LLM nem de contexto: este script lê relatório + fundamentação,
concatena e grava a sentença, validando o resultado com as mesmas âncoras
normalizadas do verificar_sentenca.py.

Uso: python scripts/merge_sentenca.py <workspace> [--numero N]
Exit 0 = sentença gravada e válida; 1 = entrada faltando ou resultado inválido.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verificar_sentenca import verificar_etapa, inferir_numero  # noqa: E402


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Merge determinístico relatório+fundamentação → sentença.")
    ap.add_argument("workspace")
    ap.add_argument("--numero")
    args = ap.parse_args()

    numero = args.numero or inferir_numero(args.workspace)
    if not numero:
        print("[ERRO] número CNJ não inferível — passe --numero")
        sys.exit(2)

    # as ENTRADAS precisam estar válidas — se falhar aqui, o defeito é da etapa anterior
    for etapa in ("relatorio", "fundamentacao"):
        r = verificar_etapa(args.workspace, numero, etapa)
        if r is None or r:
            print(f"[ERRO] entrada {etapa} " + ("ausente" if r is None else "inválida: " + "; ".join(r)))
            sys.exit(1)

    ler = lambda sufixo: open(os.path.join(args.workspace, f"{numero}{sufixo}"),
                              encoding="utf-8").read().rstrip("\n")
    saida = os.path.join(args.workspace, f"{numero}-sentenca.md")
    with open(saida, "w", encoding="utf-8") as f:
        f.write(ler("-relatorio.md") + "\n\n" + ler("-fundamentacao.md") + "\n")

    r = verificar_etapa(args.workspace, numero, "sentenca")
    if r:
        print("[ERRO] sentença gravada mas inválida: " + "; ".join(r))
        sys.exit(1)
    print(f"[FIM] sentença -> {saida.replace(os.sep, '/')} ({os.path.getsize(saida)} bytes)")
    sys.exit(0)


if __name__ == "__main__":
    main()
