# MCP Server: TNU — Jurisprudência oficial via eproc

Busca na base **oficial e viva** da Turma Nacional de Uniformização
(`eproctnu-jur.cjf.jus.br`), com **inteiro teor real** por documento e
**citação oficial pronta** em cada resultado. Engenharia reversa (HAR +
sondagem viva) e validação empírica em 10/07/2026.

## Por que este MCP (e não o portal unificado do CJF) para a TNU

| Critério | eproc TNU (este MCP) | CJF unificada |
|---|---|---|
| Atualização | **Viva** (publicações da semana corrente) | Atual p/ TNU (~06/2026) |
| Inteiro teor | **Sim — o acórdão completo, por id, stateless** | Não (só registro do acervo) |
| Precedentes relevantes | **Filtro dedicado** (representativos da TNU) | Não |
| Busca no texto integral | **Sim** (`campo=inteiro_teor`, ~5× mais docs) | Campo ITEO irregular |
| Protocolo | POST simples + PHPSESSID (sem ViewState) | Postback JSF (ViewState) |
| Cobertura | Só TNU | STF+STJ+TNU+TRFs+TRU (desiguais) |

Complementares: STF/STJ atuais → **BNP**; TRF5 → **JULIA**; TRFs/TRU/histórico
STF-STJ → **CJF unificada**.

## Tools

| Tool | O que faz |
|---|---|
| `buscar_tnu` | Busca com operadores validados, filtros (classe, relator, processo, datas, precedentes relevantes, caput, agrupamento — todos os campos do formulário), paginação e ordenação. Classe/relator/tipo aceitam **múltiplos valores por vírgula**. XML com `citacao_oficial` por item. |
| `obter_inteiro_teor_tnu` | O acórdão completo em texto puro, pelo `id` do resultado — em janelas (`inicio`/`max_chars`) para documentos longos. |
| `gerar_relatorio_tnu` | Mesma busca, Markdown para apresentar. |
| `listar_filtros_tnu` | Classes e relatores **ao vivo** + tipos, operadores e cobertura. |

## Sintaxe (validada empiricamente em 10/07/2026, com contagens)

| Operador | Efeito | Validação (base "aposentadoria" = 2.329) |
|---|---|---|
| espaço | E implícito | `aposentadoria rural` = 383 (idêntico ao `e`) |
| `e` | AND (case/acento-insensitive) | 383 |
| `ou` | OR | 2.860 |
| `não`/`nao` | NOT | 1.946 |
| `prox` | proximidade (SEM número — `prox5` = 0!) | 211 |
| `*` | wildcard sufixo E prefixo | `aposentad*` = 2.388; `*doença` = 592 |
| `"..."` | frase exata | `"prescrição intercorrente"` = 4 |

## Instalação

```bash
pip install -r requirements.txt
claude mcp add -s user tnu-eproc -- python C:/Users/georg/.claude/mcp-servers/tnu-eproc/server.py
```

## Detalhes técnicos (engenharia reversa 10/07/2026)

- **Busca**: POST `externo_controlador.php?acao=jurisprudencia@jurisprudencia/ajax_paginar_resultado`
  — funciona direto (sem `listar_resultados` prévio), devolve total + cards,
  páginas de 25/50/100 (`selTamanhoPagina` + `hdnPaginaAtual`).
- **Encoding**: formulários em **ISO-8859-1** (UTF-8 quebra filtros acentuados
  — ex.: classe processual; foi a causa de um falso "0 resultados").
- **`selClasse[]`**: o value é a **chave em caixa mista** do JSON de
  `ajax_carregar_listas_pesquisa` (ex.: `Pedido de Uniformização de
  Interpretação de Lei (Turma)`), não o texto em maiúsculas.
- **Inteiro teor**: GET `download_inteiro_teor&id_jurisprudencia=<id>` —
  100% stateless (nem cookie), ~190KB de HTML → texto.
- **Citação oficial**: atributo `data-citacao` de cada card (ementa completa +
  linha `(TNU, PUIL ..., Relator ..., D.E. ...)`).
- **Acervo**: acórdãos da TNU (tipos "monocrática" e "presidente" existem no
  formulário mas retornaram 0 nos testes).
- **Agrupar Resultados** (`chkAgruparResultados`, default marcado no site):
  dedup do lado do servidor de documentos quase idênticos do mesmo processo
  ("aposentadoria": 2.329 → 2.264); a estrutura do card não muda (1 doc por
  card). Exposto como `agrupar_resultados` (default True, fiel ao site).
- **Multi-select**: `selClasse[]`/`selRelator[]`/`selTipoDocumento[]` aceitam
  repetição — as tools recebem listas separadas por vírgula (multi-relator
  validado: 113 + 69 = 182).
- **Sem CAPTCHA**; retry com backoff (3 tentativas).
- **Bateria ao vivo: 16/16 + 6/6 OK** (busca, paginação cruzando fronteira de
  página do servidor, inteiro teor em janelas, todos os filtros do formulário,
  agrupamento, multi-valores, erros honestos).
