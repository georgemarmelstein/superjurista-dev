#!/usr/bin/env python3
"""ingerir_kanban.py - Ponte determinística pipeline → Kanban.

O pipeline v3.x escreve workspaces FLAT em data/<tipo>/<numero>/, invisíveis
ao Kanban do frontend (que lê data/<tipo>/01-por-analisar/... etc.). Este
script move o workspace aprovado para data/<tipo>/01-por-analisar/<numero>,
tornando-o visível na coluna "Por analisar".

Para tipo sentenca, a ingestão é condicionada ao gate determinístico
(scripts/verificar_sentenca.py --gate, exit 0). Para outros tipos, exige-se
apenas pasta não-vazia. `--forcar` ignora o gate (nunca o destino existente).

Uso:
  python scripts/ingerir_kanban.py <numero-ou-caminho> [--tipo sentenca] [--forcar]
      → ingere UM workspace (exit 0 = ingerido; 1 = erro)
  python scripts/ingerir_kanban.py --varrer [--tipo sentenca]
      → varre data/<tipo>/ atrás de workspaces flat com nome CNJ e ingere os
        que passam no gate; uma linha por workspace (exit 0 sempre)
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

RE_CNJ = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
GATE_SCRIPT = ROOT / "scripts" / "verificar_sentenca.py"

# Pastas de estado do Kanban (nunca são workspaces flat)
PASTAS_ESTADO = re.compile(r"^0\d-")


def gate_aprova(workspace: Path, tipo: str) -> bool:
    """Retorna True se o workspace está apto à ingestão.

    tipo sentenca → gate determinístico (verificar_sentenca.py --gate, exit 0);
    demais tipos → basta a pasta existir e não estar vazia.
    """
    if tipo != "sentenca":
        return workspace.is_dir() and any(workspace.iterdir())
    resultado = subprocess.run(
        [sys.executable, str(GATE_SCRIPT), str(workspace), "--gate"],
        capture_output=True,
        cwd=str(ROOT),
    )
    return resultado.returncode == 0


def ingerir(workspace: Path, tipo: str, forcar: bool = False) -> str:
    """Move o workspace para data/<tipo>/01-por-analisar/<numero>.

    Retorna: "ok" | "gate" (gate reprovou) | "destino" (destino já existe).
    """
    destino = DATA / tipo / "01-por-analisar" / workspace.name
    if destino.exists():
        return "destino"
    if not forcar and not gate_aprova(workspace, tipo):
        return "gate"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(workspace), str(destino))
    return "ok"


def modo_unico(alvo: str, tipo: str, forcar: bool) -> int:
    """Ingere um único workspace, resolvido por número CNJ ou caminho."""
    candidato = Path(alvo)
    if candidato.is_dir():
        workspace = candidato.resolve()
    else:
        workspace = DATA / tipo / alvo
    print(f"[INICIO] 1 workspace -> data/{tipo}/01-por-analisar/")
    if not workspace.is_dir():
        print(f"[ERRO] {alvo}: workspace não encontrado ({workspace})")
        print("[FIM] 0/1 OK")
        return 1
    resultado = ingerir(workspace, tipo, forcar)
    if resultado == "destino":
        print(f"[ERRO] {workspace.name}: destino já existe")
        print("[FIM] 0/1 OK")
        return 1
    if resultado == "gate":
        print(f"[ERRO] {workspace.name}: gate reprovou — não ingerido")
        print("[FIM] 0/1 OK")
        return 1
    print(f"[OK] {workspace.name}: ingerido em data/{tipo}/01-por-analisar/")
    print("[FIM] 1/1 OK")
    return 0


def modo_varrer(tipo: str) -> int:
    """Varre data/<tipo>/ atrás de workspaces flat CNJ e ingere os aptos."""
    base = DATA / tipo
    candidatos = []
    if base.is_dir():
        for entrada in sorted(base.iterdir()):
            if not entrada.is_dir():
                continue
            if PASTAS_ESTADO.match(entrada.name):
                continue  # pasta de estado do Kanban (01-por-analisar etc.)
            if RE_CNJ.fullmatch(entrada.name):
                candidatos.append(entrada)
    print(f"[INICIO] {len(candidatos)} workspaces flat -> data/{tipo}/01-por-analisar/")
    ingeridos = 0
    pulados = 0
    for workspace in candidatos:
        resultado = ingerir(workspace, tipo)
        if resultado == "ok":
            print(f"[OK] {workspace.name}: ingerido")
            ingeridos += 1
        elif resultado == "destino":
            print(f"[PULADO] {workspace.name}: destino existe")
            pulados += 1
        else:
            print(f"[PULADO] {workspace.name}: gate pendente")
            pulados += 1
    print(f"[FIM] {ingeridos} ingeridos, {pulados} pulados")
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(
        description="Ponte pipeline → Kanban: move workspace flat aprovado "
                    "para data/<tipo>/01-por-analisar/."
    )
    ap.add_argument("alvo", nargs="?",
                    help="número CNJ ou caminho do workspace flat")
    ap.add_argument("--tipo", default="sentenca",
                    help="tipo de processo (default: sentenca)")
    ap.add_argument("--forcar", action="store_true",
                    help="ingere mesmo com gate reprovado (nunca sobrescreve destino)")
    ap.add_argument("--varrer", action="store_true",
                    help="varre data/<tipo>/ e ingere todos os workspaces flat aptos")
    args = ap.parse_args()

    if args.varrer:
        return modo_varrer(args.tipo)
    if not args.alvo:
        ap.error("informe <numero-ou-caminho> ou use --varrer")
    return modo_unico(args.alvo, args.tipo, args.forcar)


if __name__ == "__main__":
    sys.exit(main())
