#!/usr/bin/env python3
"""verificar_probatica.py - Gate determinístico do pipeline probático (v3.0)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verificar_pipeline import rodar_cli

ETAPAS = {
    # fim alternativo: o sinalizador do agente inventariador é "É o que satisfaz
    # inventariar do acervo probatório."; artefatos reais do pipeline v2 fecham com
    # "Inventário probatório concluído." (o v2 impunha essa frase) — ambos valem.
    "inventario":  ("-inventario.md", "# inventário probatório",
                    ("é o que satisfaz inventariar do acervo probatório.",
                     "inventário probatório concluído."), [], 500),
    "pearl":       ("-pearl.md", "# análise probatória causal",
                    "análise causal concluída.", [], 500),
    "haack":       ("-haack.md", "# análise probatória foundherentista",
                    "análise foundherentista concluída.", [], 500),
    "fbd":         ("-probatica-fbd.md", "## movimento 1",
                    "análise probatória fbd concluída.", [], 500),
    "consolidado": ("-probatica-consolidado.md", "# síntese probatória consolidada",
                    "síntese probatória consolidada concluída.", ["convergências"], 500),
}

if __name__ == "__main__":
    rodar_cli(ETAPAS, titulo="probatica")
