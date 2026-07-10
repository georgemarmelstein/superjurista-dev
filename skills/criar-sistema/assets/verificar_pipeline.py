#!/usr/bin/env python3
"""verificar_pipeline.py - Motor genérico de gate determinístico (padrão v3.0).

Generaliza scripts/verificar_sentenca.py: um pipeline NOVO não reimplementa a
mecânica de validação — declara só a sua tabela ETAPAS e chama rodar_cli(). É o
mesmo movimento que verificar_embargos.py já faz importando verificar_sentenca;
aqui a mecânica vive num motor reutilizável, com os dois acréscimos que o plano
de replicação (Tarefa 1) pediu: --etapas (subconjunto) e `fim` aceitando tupla
(fim alternativo, ex.: "juiz federal" OU "juíza federal" OU "desembargador").

COMO UM PIPELINE GERADO USA ESTE MOTOR
--------------------------------------
Cada sistema gerado ganha um verificar_<sistema>.py de poucas linhas:

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from verificar_pipeline import rodar_cli

    ETAPAS = {
        # etapa: (sufixo_do_arquivo, inicio, fim, contem[], minimo_chars)
        "linha-tempo": ("-linha-tempo.md", "# linha do tempo processual",
                        "é o que satisfaz extrair dos autos.",
                        ["marcos processuais"], 500),
        "fundamentacao": ("-fundamentacao.md", "fundamentação",
                          ("juiz federal", "juíza federal", "desembargador"),
                          ["dispositivo"], 500),
    }

    if __name__ == "__main__":
        rodar_cli(ETAPAS, titulo="meu-sistema")

USO (idêntico ao verificar_sentenca.py, mais --etapas)
------------------------------------------------------
    python scripts/verificar_<sistema>.py <workspace>
        -> varredura: estado por etapa + linha "PENDENTES: ..." (o PLANO)
    python scripts/verificar_<sistema>.py <workspace> --etapa <nome>
        -> valida UMA etapa (exit 0 = válida; 1 = ausente/inválida)
    python scripts/verificar_<sistema>.py <workspace> --etapas a,b
        -> varredura de um SUBCONJUNTO (para pipelines-subconjunto)
    python scripts/verificar_<sistema>.py <workspace> --gate
        -> gate final: exit 1 se QUALQUER etapa pendente/inválida

Marcadores casados com NORMALIZAÇÃO de acento/caixa: a âncora literal reprovava
artefato correto ("ÚLTIMOS" != "ULTIMOS"). Aqui as âncoras do ETAPAS podem ser
escritas com acento e caixa naturais — o motor normaliza os dois lados. A
exigência de acentuação continua, mas como checagem própria do documento (o
texto precisa TER acentos), não embutida na âncora.

O identificador (prefixo dos arquivos) é o padrão CNJ no nome da pasta quando
houver; caso contrário, o próprio basename da pasta. Passe --id para forçar.
"""
import argparse
import os
import re
import sys
import unicodedata

RE_CNJ = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")
RE_ACENTO = re.compile(r"[áéíóúâêôãõàçÁÉÍÓÚÂÊÔÃÕÀÇ]")


def _norm(s):
    """minúsculo e sem acentos — âncora robusta a variação de acentuação/caixa."""
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn").casefold()


def inferir_id(workspace, padrao=RE_CNJ):
    """Prefixo dos arquivos: padrão CNJ no nome da pasta; senão o basename."""
    base = os.path.basename(os.path.abspath(workspace))
    m = padrao.search(base)
    return m.group(0) if m else (base or None)


def verificar_etapa(workspace, identificador, etapa, etapas):
    """Lista de problemas (vazia = válida); None = arquivo AUSENTE.

    etapas[etapa] = (sufixo, inicio, fim, contem, minimo). `fim` pode ser str
    (um marcador) ou tupla/lista (fim alternativo — casa se QUALQUER um bater).
    """
    sufixo, inicio, fim, contem, minimo = etapas[etapa]
    caminho = os.path.join(workspace, f"{identificador}{sufixo}")
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
    if _norm(inicio) not in n[:400]:
        problemas.append(f"não abre com o marcador ({inicio!r})")
    fins = (fim,) if isinstance(fim, str) else tuple(fim)
    if not any(_norm(f) in n[-400:] for f in fins):
        problemas.append(f"não fecha com nenhum marcador ({fins!r})")
    for c in contem:
        if _norm(c) not in n:
            problemas.append(f"sem a seção obrigatória ({c!r})")
    if not RE_ACENTO.search(texto):
        problemas.append("sem acentos de português (documento jurídico exige)")
    return problemas


def rodar_cli(etapas, titulo="pipeline", inferir=inferir_id):
    """Ponto de entrada do gate de um pipeline. `etapas` é a tabela do sistema."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=f"Gate determinístico ({titulo}) - padrão v3.0.")
    ap.add_argument("workspace")
    ap.add_argument("--id", "--numero", dest="ident",
                    help="prefixo dos arquivos (inferido do nome da pasta se omitido)")
    ap.add_argument("--etapa", choices=sorted(etapas), help="valida só esta etapa (exit-coded)")
    ap.add_argument("--etapas", help="subconjunto separado por vírgula (ex.: linha-tempo,relatorio)")
    ap.add_argument("--gate", action="store_true", help="exit 1 se qualquer etapa pendente/inválida")
    a = ap.parse_args()

    if not os.path.isdir(a.workspace):
        print(f"[ERRO] workspace inexistente: {a.workspace}")
        sys.exit(2)
    identificador = a.ident or inferir(a.workspace)
    if not identificador:
        print("[ERRO] identificador não inferível do nome da pasta — passe --id")
        sys.exit(2)

    if a.etapa:
        r = verificar_etapa(a.workspace, identificador, a.etapa, etapas)
        if r is None:
            print(f"[AUSENTE] {a.etapa}")
            sys.exit(1)
        if r:
            print(f"[INVALIDA] {a.etapa}: " + "; ".join(r))
            sys.exit(1)
        print(f"[OK] {a.etapa}")
        sys.exit(0)

    if a.etapas:
        alvo = [e.strip() for e in a.etapas.split(",") if e.strip()]
        desconhecidas = [e for e in alvo if e not in etapas]
        if desconhecidas:
            print(f"[ERRO] etapa(s) desconhecida(s): {', '.join(desconhecidas)}")
            sys.exit(2)
    else:
        alvo = list(etapas)

    pendentes = []
    print(f"[INICIO] {identificador} -> verificação das {len(alvo)} etapas ({titulo})")
    for etapa in alvo:
        r = verificar_etapa(a.workspace, identificador, etapa, etapas)
        if r is None:
            print(f"[AUSENTE] {etapa}")
            pendentes.append(etapa)
        elif r:
            print(f"[INVALIDA] {etapa}: " + "; ".join(r))
            pendentes.append(etapa)
        else:
            print(f"[OK] {etapa}")
    print("PENDENTES: " + (" ".join(pendentes) if pendentes else "(nenhuma)"))
    print(f"[FIM] {len(alvo) - len(pendentes)}/{len(alvo)} válidas")
    sys.exit(1 if (a.gate and pendentes) else 0)


if __name__ == "__main__":
    print("[ERRO] verificar_pipeline.py é um MOTOR, não um gate executável direto.\n"
          "       Crie um verificar_<sistema>.py que declare ETAPAS e chame\n"
          "       rodar_cli(ETAPAS). Veja o docstring no topo deste arquivo.",
          file=sys.stderr)
    sys.exit(2)
