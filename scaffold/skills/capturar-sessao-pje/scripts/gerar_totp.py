#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera o codigo TOTP (Google Authenticator) do 2FA do PJE por software.

O codigo de 6 digitos do Google Authenticator e um TOTP (RFC 6238): deriva
matematicamente de um segredo (seed) em base32. Qualquer software com o mesmo
seed produz o mesmo codigo no mesmo instante. Logo, com o SEU seed, este script
calcula o mesmo numero que o celular mostra -- permitindo login desassistido.

O seed e uma CREDENCIAL FORTE. Guarde em .env (gitignored), nunca no repo/log.

Uso:
    # Le PJE_TOTP_SEED do ambiente ou do .env na raiz
    python gerar_totp.py

    # Seed explicito (util para o teste de comparacao com o celular)
    python gerar_totp.py --seed "JBSW Y3DP EHPK 3PXP"

    # Verboso: mostra segundos restantes na janela atual
    python gerar_totp.py -v

Saida padrao: apenas o codigo de 6 digitos (stdout), para consumo por script.
"""

import os
import sys
import argparse
from pathlib import Path


def carregar_seed_do_env(env_path: Path) -> str | None:
    """Le PJE_TOTP_SEED de um arquivo .env sem dependencias externas."""
    if not env_path.is_file():
        return None
    for linha in env_path.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        if chave.strip() == "PJE_TOTP_SEED":
            return valor.strip().strip('"').strip("'")
    return None


def normalizar_seed(seed: str) -> str:
    """Google Authenticator mostra o seed em grupos com espaco e caixa variavel.
    O base32 canonico e sem espacos e em maiuscula."""
    return seed.replace(" ", "").replace("-", "").upper()


def resolver_seed(arg_seed: str | None) -> str:
    """Prioridade: --seed > env PJE_TOTP_SEED > .env na raiz do projeto."""
    if arg_seed:
        return arg_seed
    if os.getenv("PJE_TOTP_SEED"):
        return os.environ["PJE_TOTP_SEED"]
    # .env fica na raiz do projeto: sobe 4 niveis a partir de scripts/
    raiz = Path(__file__).resolve().parents[4]
    seed = carregar_seed_do_env(raiz / ".env")
    if seed:
        return seed
    raise SystemExit(
        "[ERRO] Seed nao encontrado. Defina PJE_TOTP_SEED no .env "
        "(raiz do projeto) ou passe --seed."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera codigo TOTP do 2FA do PJE")
    parser.add_argument("--seed", help="Seed base32 (sobrepoe .env). Espacos sao ignorados.")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Mostra segundos restantes na janela atual")
    args = parser.parse_args()

    try:
        import pyotp
    except ImportError:
        print("[ERRO] pyotp nao instalado. Rode: python -m pip install pyotp",
              file=sys.stderr)
        return 1

    seed = normalizar_seed(resolver_seed(args.seed))

    try:
        totp = pyotp.TOTP(seed)
        codigo = totp.now()
    except Exception as e:  # base32 invalido, etc.
        print(f"[ERRO] Seed invalido: {e}", file=sys.stderr)
        return 1

    if args.verbose:
        import time
        restante = 30 - int(time.time()) % 30
        print(f"{codigo}  (valido por mais ~{restante}s)")
    else:
        # Saida limpa: so o codigo, para o passo de login consumir
        print(codigo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
