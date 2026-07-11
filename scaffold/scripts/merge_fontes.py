#!/usr/bin/env python3
"""merge_fontes.py - Merge determinístico da cadeia de custódia de citações (v3.0).

Os agentes de pesquisa (BNP, CJF, JULIA, triagem, STJ, TNU) gravam, cada um, um
parcial `fontes-<origem>.json` no workspace — nenhum agente escreve o arquivo
final. Este script é o único responsável por produzir `$NUMERO-fontes.json`
(Contrato C1), que `scripts/verificar_citacoes.py` usa como corpus autorizado
para o gate de citações verbatim. Nenhum LLM participa do merge: a validação,
a deduplicação e a atribuição de IDs são puramente determinísticas.

Cada parcial pode ser o objeto completo ({"processo", "versao", "fontes": [...]})
ou apenas a lista de fontes — ambas as formas são toleradas, só a lista importa.

Validação por item (whitelist ORIGENS_AUTORIZADAS; campos obrigatórios não-vazios;
"campo" restrito a tese/ementa/acordao/sumula). Item inválido é REJEITADO (mas os
irmãos válidos do mesmo parcial e dos demais parciais são preservados no arquivo
final). IDs são REATRIBUÍDOS sequencialmente por prefixo de origem — o id que o
parcial trouxer é descartado. O prefixo vem do campo origem_mcp de cada item, não
do nome do arquivo parcial (por isso itens de fontes-triagem.json, que podem vir
de qualquer MCP real, recebem o prefixo correto).

Deduplicação por (origem_mcp, referencia, norm(trecho_verbatim)), com a mesma
normalização (NFD sem acentos + casefold + espaços colapsados) de
verificar_citacoes.py — reimplementada aqui porque os scripts são standalone.

Uso:
  python scripts/merge_fontes.py <workspace> [--id N]

Exit codes:
  0 - merge concluído sem rejeições (ou nenhum parcial encontrado — arquivo NÃO
      criado nesse caso)
  1 - houve item(ns) rejeitado(s) ou parcial(is) com JSON inválido; ainda assim
      as fontes válidas são gravadas em $NUMERO-fontes.json
  2 - erro de uso (workspace inexistente)
"""
import argparse
import glob
import json
import os
import re
import sys
import unicodedata

RE_CNJ = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")

ORIGENS_AUTORIZADAS = {"bnp-api", "cjf-jurisprudencia", "julia-trf5",
                        "pesquisa-stj", "tnu-eproc"}
PREFIXOS = {"bnp-api": "BNP", "cjf-jurisprudencia": "CJF", "julia-trf5": "JULIA",
            "pesquisa-stj": "STJ", "tnu-eproc": "TNU"}
CAMPOS_VALIDOS = {"tese", "ementa", "acordao", "sumula"}
OBRIGATORIOS = ("origem_mcp", "tribunal", "tipo", "referencia", "campo", "trecho_verbatim")


def _norm(s):
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").casefold()
    return re.sub(r"\s+", " ", s).strip()


def _opcional(v):
    return v if v else None


def coletar_fontes(bruto):
    """Tolera parcial como objeto completo ({"fontes": [...]}) ou lista bruta."""
    if isinstance(bruto, dict):
        return bruto.get("fontes", [])
    if isinstance(bruto, list):
        return bruto
    return []


def validar_item(item):
    """Retorna (ok, motivo). motivo é None quando ok."""
    if not isinstance(item, dict):
        return False, "item não é um objeto JSON"
    for campo_nome in OBRIGATORIOS:
        valor = item.get(campo_nome)
        if not isinstance(valor, str) or not valor.strip():
            return False, f"campo obrigatório ausente/vazio: {campo_nome}"
    origem = item["origem_mcp"]
    if origem not in ORIGENS_AUTORIZADAS:
        return False, f"origem_mcp não autorizada: {origem}"
    if item["campo"] not in CAMPOS_VALIDOS:
        return False, "campo inválido: {} (esperado um de {})".format(
            item["campo"], sorted(CAMPOS_VALIDOS))
    return True, None


def normalizar_item(item):
    """Item já validado -> dict no formato final do Contrato C1 (sem id ainda)."""
    return {
        "origem_mcp": item["origem_mcp"],
        "tribunal": item["tribunal"],
        "tipo": item["tipo"],
        "referencia": item["referencia"],
        "orgao_julgador": _opcional(item.get("orgao_julgador")),
        "data_julgamento": _opcional(item.get("data_julgamento")),
        "campo": item["campo"],
        "trecho_verbatim": item["trecho_verbatim"],
        "url": _opcional(item.get("url")),
    }


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser(
        description="Merge determinístico dos parciais fontes-*.json em $NUMERO-fontes.json.")
    ap.add_argument("workspace")
    ap.add_argument("--id", dest="ident", help="prefixo do processo (inferido do nome da pasta)")
    a = ap.parse_args()

    if not os.path.isdir(a.workspace):
        print(f"[ERRO] workspace inexistente: {a.workspace}")
        sys.exit(2)

    base = os.path.basename(os.path.abspath(a.workspace))
    m = RE_CNJ.search(base)
    ident = a.ident or (m.group(0) if m else base)

    parciais = sorted(glob.glob(os.path.join(a.workspace, "fontes-*.json")))
    print(f"[INICIO] {len(parciais)} parcial(is) -> {ident}-fontes.json")

    if not parciais:
        print("[AVISO] nenhum parcial fontes-*.json encontrado")
        sys.exit(0)

    houve_erro = False
    validas = []
    vistos = set()
    rejeitadas = 0
    duplicatas = 0

    for caminho in parciais:
        nome = os.path.basename(caminho)
        try:
            with open(caminho, encoding="utf-8") as f:
                bruto = json.load(f)
        except json.JSONDecodeError:
            print(f"[ERRO] {nome}: JSON inválido")
            houve_erro = True
            continue
        for item in coletar_fontes(bruto):
            ok, motivo = validar_item(item)
            if not ok:
                referencia = item.get("referencia") if isinstance(item, dict) else None
                rotulo = referencia or "?"
                print(f"[ERRO] item rejeitado ({rotulo}): {motivo}")
                houve_erro = True
                rejeitadas += 1
                continue
            chave = (item["origem_mcp"], item["referencia"], _norm(item["trecho_verbatim"]))
            if chave in vistos:
                duplicatas += 1
                print(f"[AVISO] duplicata ignorada: {item['origem_mcp']} {item['referencia']}")
                continue
            vistos.add(chave)
            validas.append(normalizar_item(item))

    contadores = {}
    fontes_finais = []
    for v in validas:
        prefixo = PREFIXOS[v["origem_mcp"]]
        contadores[prefixo] = contadores.get(prefixo, 0) + 1
        v_id = f"{prefixo}-{contadores[prefixo]:03d}"
        print(f"[OK] {v_id}: {v['referencia']}")
        fontes_finais.append({"id": v_id, **v})

    saida = {"processo": ident, "versao": 1, "fontes": fontes_finais}
    caminho_saida = os.path.join(a.workspace, f"{ident}-fontes.json")
    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(saida, f, ensure_ascii=False, indent=2)

    print(f"[FIM] {len(fontes_finais)} válidas, {rejeitadas} rejeitadas, {duplicatas} duplicatas")
    sys.exit(1 if houve_erro else 0)


if __name__ == "__main__":
    main()
