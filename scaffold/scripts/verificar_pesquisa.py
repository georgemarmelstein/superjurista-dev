#!/usr/bin/env python3
"""verificar_pesquisa.py - Gate determinístico do pipeline de pesquisa (v3.0)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verificar_pipeline import rodar_cli

ETAPAS = {
    # etapa: (sufixo, inicio, fim, contem[], minimo_chars)
    "bnp":         ("-pesquisa-bnp.md", "# pesquisa bnp",
                    "pesquisa bnp concluída.", [], 300),
    "cjf":         ("-pesquisa-cjf.md", "# pesquisa cjf",
                    "pesquisa cjf concluída.", [], 300),
    "julia":       ("-pesquisa-julia.md", "# pesquisa julia",
                    "pesquisa julia concluída.", [], 300),
    "stj":         ("-pesquisa-stj.md", "# pesquisa stj",
                    "pesquisa stj concluída.", [], 300),
    "tnu":         ("-pesquisa-tnu.md", "# pesquisa tnu",
                    "pesquisa tnu concluída.", [], 300),
    "consolidado": ("-precedentes-consolidado.md", "# relatório consolidado de precedentes",
                    "consolidação realizada", ["hierarquia"], 500),
}

if __name__ == "__main__":
    rodar_cli(ETAPAS, titulo="pesquisa")
