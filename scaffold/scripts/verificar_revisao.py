#!/usr/bin/env python3
"""verificar_revisao.py - Gate determinístico do pipeline de revisão (v3.0)."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verificar_pipeline import rodar_cli

ETAPAS = {
    "embargabilidade": ("-analise-embargabilidade.md", "# análise de embargabilidade",
                        "análise de embargabilidade concluída.", [], 400),
    "calculos":        ("-verificacao-calculos.md", "# relatório de verificação de cálculos",
                        "verificação de cálculos concluída.", [], 400),
    "fontes":          ("-verificacao-fontes.md", "# relatório de verificação de fontes",
                        "verificação de fontes concluída.", [], 400),
    "honorarios":      ("-verificacao-honorarios.md", "# relatório de verificação de honorários",
                        "verificação de honorários concluída.", [], 400),
    # fim alternativo: o sinalizador REAL do agente verificador-remessa é
    # "Verificação de remessa necessária concluída." (formato_saida do agente e
    # artefatos reais); a tabela do orquestrador v2 impunha a frase curta
    # "Verificação de remessa concluída." — o gate aceita as duas.
    "remessa":         ("-verificacao-remessa.md", "# relatório de verificação de remessa necessária",
                        ("verificação de remessa necessária concluída.",
                         "verificação de remessa concluída."), [], 400),
    "robustecida":     ("-minuta-robustecida.md", "# minuta robustecida",
                        "minuta robustecida concluída.", ["log de alterações"], 800),
}

if __name__ == "__main__":
    rodar_cli(ETAPAS, titulo="revisao")
