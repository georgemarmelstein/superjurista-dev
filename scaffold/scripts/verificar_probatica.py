#!/usr/bin/env python3
"""verificar_probatica.py - Gate determinístico da análise probatória (v2).

Uma tabela, DOIS subconjuntos (o consolidado é o produto final comum):

- LENTES (standalone /pipeline-probatica): tríplice metodológica —
  --etapas inventario,pearl,haack,fbd,consolidado
- TRILHO ADVERSARIAL (Etapa 2.7 do /pipeline-sentenca): tribunal probatório —
  --etapas inventario,tese-pro-autor,tese-pro-reu,replica-pro-autor,replica-pro-reu,consolidado

As âncoras das teses/réplicas são os contratos CONGELADOS dos agentes de
.claude/agents/tribunal/ (acusador-probatico, defensor-probatico, juiz-mediador);
o consolidado mantém as âncoras que o restante do pipeline já consome.
"""
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
    # trilho adversarial (tribunal): contratos congelados dos agentes tribunal/
    "tese-pro-autor":    ("-tese-pro-autor.md", "# tese pró-autor",
                          "tese pró-autor concluída.", [], 500),
    "tese-pro-reu":      ("-tese-pro-reu.md", "# tese pró-réu",
                          "tese pró-réu concluída.", [], 500),
    "replica-pro-autor": ("-replica-pro-autor.md", "# réplica pró-autor",
                          "réplica pró-autor concluída.", [], 300),
    "replica-pro-reu":   ("-replica-pro-reu.md", "# réplica pró-réu",
                          "réplica pró-réu concluída.", [], 300),
    # lentes metodológicas (standalone /pipeline-probatica)
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
