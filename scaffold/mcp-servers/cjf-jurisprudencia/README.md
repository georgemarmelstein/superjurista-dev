# MCP Server: CJF Jurisprudência Unificada (v2)

Acesso à jurisprudência unificada do CJF (Conselho da Justiça Federal):
**STF, STJ, TNU, TRF1–TRF5, TRU1–TRU6 e TR1–TR6** numa só consulta.
Scraping JSF/AJAX (não há API JSON pública). Robustecido em 10/07/2026.

## Cobertura da base (medida em 10/07/2026 — LEIA ANTES DE CONFIAR)

| Tribunal | Estado da base |
|---|---|
| TNU | **Atualizada** (julgados até 06/2026) |
| TRF1 | **Atualizada** |
| TRF3 | **Atualizada** |
| TRF4 | Atual, acervo pequeno (~1,7k docs 2020–2026) |
| TRF2 | Desatualizada — nada após ~2023 |
| STF | **Congelada** — nada após ~2019 |
| STJ | **Congelada** — nada após ~dez/2019 |
| TRF5 | **Congelada** — nada após ~fev/2019 |
| TRU1 | Acervo grande; TRU2/5/6 quase vazias |

Zero resultado recente em acervo congelado **não** significa inexistência de
jurisprudência — confirme em fonte atual (BNP para STF/STJ; JULIA para TRF5).
A tool `verificar_cobertura_cjf` mede isso ao vivo.

## Tools

| Tool | O que faz |
|---|---|
| `buscar_jurisprudencia_cjf` | Busca com sintaxe completa, paginação real (`pagina`), faixa de datas (`data_inicio`/`data_fim`) e aviso de cobertura. XML. |
| `obter_documento_cjf` | Registro integral (sem truncar) de um documento pelo `id` da busca. |
| `gerar_relatorio_cjf` | Mesma busca, saída Markdown para apresentar. |
| `listar_filtros_cjf` | Tribunais + cobertura, 31 campos, operadores (incl. `NAO ADJ`, `[-CAMPO]`), wildcards. |
| `verificar_cobertura_cjf` | Mede ao vivo a atualização da base por tribunal. |

## Sintaxe (resumo — a lista completa está na descrição das tools)

- Booleanos: `E OU NAO XOU`, parênteses, `"frase exata"`.
- Proximidade: `ADJ[n]`, `PROX[n]`, `COM`, `MESMO` + formas negativas
  (`NAO ADJ` etc.) e `termo[-CAMPO]`.
- Campos: `termo[CAMPO]` — 31 campos (EMEN, DECI, REL, PROC, CLAS, REFL,
  PREC, INDE, UF...). Nome curto ou longo.
- Datas: exata `20191219[DTPP]` (AAAAMMDD, **wildcards não funcionam em
  datas**); faixa somente pelos parâmetros `data_inicio`/`data_fim`
  (DD/MM/AAAA) — único filtro que exige o formulário avançado do portal.

## Instalação

```bash
pip install -r requirements.txt
```

Registrar no `.mcp.json` da raiz do projeto, com caminho absoluto (o
`/instalar-superjurista` faz isso automaticamente; servidor novo só carrega em sessão nova):

```json
{
  "mcpServers": {
    "cjf-jurisprudencia": {
      "command": "python",
      "args": ["<RAIZ_DO_PROJETO>/.claude/mcp-servers/cjf-jurisprudencia/server.py"]
    }
  }
}
```

## Detalhes técnicos

- **Endpoint**: POST `https://jurisprudencia.cjf.jus.br/unificada/index.xhtml`
  (JSF/PrimeFaces, partial/ajax, ViewState + JSESSIONID).
- **Ids dinâmicos**: o name dos checkboxes de tribunal, os campos do painel
  avançado e os botões por linha são **descobertos por parse** a cada sessão
  (fallback nos valores de 07/2026). Nada de `j_idt51` fixo.
- **Paginação**: postback do `tabelaDocumentos` com índices absolutos,
  50 linhas por request.
- **Documento integral**: botão "sem formatação" da linha + `contentLoad`
  do diálogo dinâmico (2 postbacks).
- **TRU/TR**: toggle renderiza o subpainel no servidor; valores
  `formulario:tribuna_tru`/`tribuna_tr` (TRU1–6/TR1–6).
- **Retry**: backoff exponencial, 3 tentativas (o portal dá 504 com frequência).
- **Testado ao vivo** em 10/07/2026: bateria de 12 casos (busca, paginação,
  datas, TRU, documento integral em página 2, cobertura, erros honestos).
