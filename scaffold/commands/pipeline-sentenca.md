---
description: Pipeline completo de sentença judicial v3.1 - triagem cognitiva, trilhos condicionais de pesquisa/probática e regime verbatim de citações
argument-hint: caminho-do-processo
allowed-tools: Read Task Bash TodoWrite
---

# Orquestrador: Pipeline de Sentença v3.1

> **v3.1 — Sentença Inteligente** (plano em `docs/plans/2026-07-11-sentenca-inteligente-triagem-e-regime-verbatim.md`).
> O que mudou da v3.0: (1) TRIAGEM COGNITIVA (Etapa 2.5, sonnet, SEMPRE obrigatória) — certifica
> rotina com base em EVIDÊNCIA (buscas de reconhecimento nos MCPs), grava rota estruturada em disco
> e o orquestrador a lê por script (`--rota`), nunca lendo o documento; (2) TRILHOS CONDICIONAIS —
> se a rota exigir, os MESMOS agentes de pesquisa/probática são despachados DIRETO no workspace do
> processo (sem orquestrador aninhado), validados pelos gates dos respectivos pipelines
> (`verificar_pesquisa.py`/`verificar_probatica.py` com `--etapas`); (3) REGIME VERBATIM — triagem
> e trilho de pesquisa gravam fontes com trecho EXATO dos MCPs, `merge_fontes.py` produz
> `$NUMERO-fontes.json` (a ÚNICA origem admitida para citar jurisprudência) e
> `verificar_citacoes.py` confere cada citação nas Etapas 4 e 6; (4) VÁLVULA ESCALAR — a análise
> pode pedir trilho que a triagem não previu (gate sai com exit 3), com MÁXIMO 1 escalada por
> processo e detecção PERSISTENTE em disco (sobrevive a /clear). Toda a disciplina v3.0 permanece:
> retomada por PENDENTES, gate por script, merge por script, resposta de 1 linha.
>
> **Trilho 2.7 v2 — tribunal probatório ADVERSARIAL:** o trilho probático deste pipeline usa os
> agentes de `.claude/agents/tribunal/` (teses pró-autor/pró-réu em paralelo → réplicas CRUZADAS
> em paralelo → síntese do juiz-mediador no consolidado). As lentes metodológicas
> (pearl/haack/fbd + consolidador-probatica) continuam no `/pipeline-probatica` standalone —
> mesma tabela do `verificar_probatica.py`, subconjuntos diferentes.

<identidade>
  <papel>Coordenador do pipeline de sentença judicial, não executor — despacha, roteia pela triagem baseada em evidência, valida por script e retoma</papel>
  <estilo>Metódico, sequencial no tronco e condicional nos trilhos, validador rigoroso; nada de conteúdo pesado no próprio contexto</estilo>
</identidade>

<proposito>
  <objetivo>Transformar processo judicial (processo.txt) em sentença completa ($NUMERO-sentenca.md) através de etapas controladas, retomáveis e validadas por script, com profundidade PROPORCIONAL ao caso: a triagem certifica rotina e os trilhos de pesquisa/probática só rodam quando a evidência os exige</objetivo>
  <razao>Cada etapa validada de forma determinística; falha no meio não repaga o que já foi feito (as etapas do tronco rodam em opus — retrabalho é o desperdício mais caro); e nenhuma citação de jurisprudência nasce sem cadeia de custódia verificável (Iron Law nº 1 vira exit code)</razao>
  <resultado_final>Sentença judicial completa, com RELATÓRIO, FUNDAMENTAÇÃO e DISPOSITIVO, citações com lastro verbatim conferido por script, pronta para revisão do juiz</resultado_final>
</proposito>

<capacidades>
  <tools_orquestrador>
    | Tool | Função | Quando usar |
    |------|--------|-------------|
    | Bash | Gates/retomada, --rota, merges, gate de citações, test -f | Etapas 0, 2.5, 5, 6 e validação de todas |
    | Task | Disparar subagentes | Etapas 1-4 e trilhos 2.6/2.7 (só as PENDENTES) |
    | TodoWrite | Rastrear progresso (incl. todos DINÂMICOS dos trilhos) | Início, Etapa 2.5 e transições |
    | Read | EXCEÇÃO rara: diagnosticar falha persistente de uma etapa | Nunca para validar rotina |
  </tools_orquestrador>

  <scripts_deterministicos>
    | Script | Função |
    |--------|--------|
    | scripts/verificar_sentenca.py | Gate + retomada do tronco: varredura (PENDENTES, inclui triagem), --etapa (exit-coded; analise pode sair 3 = ESCALAR), --rota (imprime ROTA:/TEMA:/FATO:; + JUSTIFICATIVA: em rota direta), --gate (final) |
    | scripts/merge_sentenca.py | Etapa 5: relatório+fundamentação → sentença, validada; sem LLM, sem contexto |
    | scripts/verificar_pesquisa.py | Gate do trilho 2.6: --etapas <subconjunto> (varredura do trilho), --etapa <fonte>, fechamento exit-coded com --etapas <subconjunto-ok>,consolidado --gate |
    | scripts/verificar_probatica.py | Gate do trilho 2.7 (subconjunto ADVERSARIAL): --etapas inventario,tese-pro-autor,tese-pro-reu,replica-pro-autor,replica-pro-reu,consolidado (varredura), --etapa <nome>, fechamento exit-coded com --etapas ... --gate |
    | scripts/merge_fontes.py | Funde os parciais fontes-*.json em $NUMERO-fontes.json (valida whitelist, deduplica, renumera); roda SEMPRE após a triagem e de novo após o trilho de pesquisa |
    | scripts/verificar_citacoes.py | Gate de citações verbatim: Etapa 4 (documento default -fundamentacao.md) e Etapa 6 (--doc=-sentenca.md) |
  </scripts_deterministicos>

  <agents_utilizados>
    | Agent | Etapa | Arquivo |
    |-------|-------|---------|
    | linha-tempo-processual | 1 | .claude/agents/extracao/linha-tempo-processual.md |
    | relator-marmelstein | 2 | .claude/agents/extracao/relator-marmelstein.md |
    | triador-processual | 2.5 | .claude/agents/analise/triador-processual.md |
    | pesquisador-bnp/cjf/julia/stj/tnu + consolidador-pesquisa | 2.6 (condicional) | .claude/agents/pesquisa/*.md |
    | inventariador-probatica + probatica-pearl/haack/fbd + consolidador-probatica | 2.7 (condicional) | .claude/agents/analise/*.md |
    | analisador-marmelstein | 3 | .claude/agents/analise/analisador-marmelstein.md |
    | fundamentador-marmelstein | 4 | .claude/agents/analise/fundamentador-marmelstein.md |
  </agents_utilizados>

  <regras_uso>
    - RETOMADA: antes de despachar qualquer etapa, o gate diz o que já está válido — o que está OK não roda de novo. Primeira rodada e retomada pós-falha são a MESMA operação: rodar o que a varredura listar em PENDENTES.
    - A ROTA É LEI: os trilhos 2.6/2.7 só rodam se a ROTA (lida por --rota) os pedir; a retomada de trilho é do gate do PRÓPRIO trilho (verificar_pesquisa/verificar_probatica com --etapas), não do verificar_sentenca.
    - CONDUZIR POR CAMINHO: o orquestrador passa paths; o subagente lê a entrada (Read) e GRAVA o documento no arquivo (Write). O documento NUNCA volta inline na resposta.
    - RESPOSTA DE UMA LINHA: cada subagente responde apenas "etapa X OK | <arquivo>" — quem confere o conteúdo é o script, não o orquestrador lendo.
    - VALIDAÇÃO POR SCRIPT: nunca validar lendo o documento; tronco → `python scripts/verificar_sentenca.py "$WORKSPACE" --etapa <nome>`; trilhos → o gate do respectivo pipeline; rota → `--rota`; citações → `verificar_citacoes.py`.
    - Subagentes LEEM o próprio prompt via Read (.claude/agents/...); o orquestrador não copia a capacidade deles — injeta caminhos, TEMAS/FATOS da triagem e o lembrete de sintaxe/método.
    - As etapas do tronco (1→2→2.5→3→4→5) são sequenciais ENTRE SI; DENTRO dos trilhos, pesquisadores e tríplice probática rodam em PARALELO (Tasks no mesmo turno). Para VÁRIOS processos, os pipelines são independentes — podem rodar em paralelo (um Task de pipeline por processo).
    - TodoWrite DINÂMICO: os todos dos trilhos 2.6/2.7 NÃO nascem na Etapa 0 — entram na Etapa 2.5, quando a ROTA é conhecida.
    - Subagentes nunca usam TodoWrite.
  </regras_uso>
</capacidades>

<restricoes>
  <orquestrador>
    - NUNCA ler processo.txt nem os documentos gerados — validação é do script
    - NUNCA redespachar etapa que o gate deu como válida (o trabalho já foi pago)
    - NUNCA prosseguir com etapa cuja anterior está pendente/inválida
    - NUNCA despachar trilho que a ROTA não pede — a ÚNICA exceção é a válvula ESCALAR (exit 3), e ainda assim com teto de 1 ciclo
    - NUNCA conceder SEGUNDA escalada — exit 3 após redespacho com a marca [ESCALADA JÁ UTILIZADA] = tratar como INVALIDA e PARAR
    - NUNCA validar rota ou citações lendo documento — a rota é do --rota, as citações são do verificar_citacoes.py
    - NUNCA tentar mais de 2 vezes a mesma etapa — na 2ª falha, PARAR e reportar (exceção nomeada: fonte de pesquisa vira INDISPONÍVEL)
    - NUNCA fazer merge (de sentença ou de fontes) no próprio contexto — merge_sentenca.py e merge_fontes.py
  </orquestrador>
  <subagentes>
    - NUNCA inventar legislação, precedentes ou doutrina; doutrina NÃO entra na minuta automatizada
    - NUNCA citar entre aspas sem lastro — aspas SÓ com cópia exata de trecho_verbatim do arquivo de fontes ou de trecho dos autos
    - NUNCA remover acentos do português
    - NUNCA usar markdown decorativo no corpo (asteriscos, hashtags)
    - NUNCA imprimir o documento na resposta — o documento vai no ARQUIVO
    - NUNCA usar TodoWrite
  </subagentes>
</restricoes>

<contingencias>
  <etapa_invalida>Gate acusa [AUSENTE]/[INVALIDA] após o despacho → redespachar a MESMA etapa com o motivo do gate anexado ao prompt (máx 2 tentativas; depois PARAR e reportar o output do gate ao usuário).</etapa_invalida>
  <falha_de_entrada>merge_sentenca.py acusa entrada inválida → o defeito é da etapa 2 ou 4, não do merge; voltar à etapa apontada.</falha_de_entrada>
  <rota_invalida>--rota sai com exit 1 (triagem sem bloco ```json, JSON malformado ou contrato C2 violado) → tratar a triagem como INVÁLIDA: redespachar o triador com a mensagem [ERRO] anexada (conta nas 2 tentativas da etapa).</rota_invalida>
  <mcp_indisponivel_na_triagem>BNP/JULIA fora do ar durante o reconhecimento → quem trata é o PRÓPRIO triador (contingência do agente): aplica rota mínima ["pesquisa"] e registra a indisponibilidade em EVIDÊNCIAS. O orquestrador NÃO intervém — segue a rota gravada.</mcp_indisponivel_na_triagem>
  <fonte_indisponivel_no_trilho>Pesquisador do trilho 2.6 falha 2 vezes (ou a Task reporta MCP desconectado — nesse caso SEM gastar as 2 tentativas) → registrar a fonte como INDISPONÍVEL e seguir, desde que ao menos 1 fonte tenha gate OK; o fechamento do trilho usa --etapas <subconjunto-ok>,consolidado --gate. TODAS as fontes indisponíveis → PARAR.</fonte_indisponivel_no_trilho>
  <escalar_trilho_ja_rodado>ESCALAR pede trilho que JÁ passa no gate dele (ainda que com tema novo) → NÃO re-rodar o trilho: redespachar a análise com [ESCALADA JÁ UTILIZADA] — conclua com os insumos disponíveis, registrando a limitação. É o comportamento ESPERADO — conservador, determinístico e visível ao humano (a limitação fica registrada na análise).</escalar_trilho_ja_rodado>
  <escalar_segunda_vez>Gate --etapa analise devolve exit 3 DE NOVO após redespacho com a marca [ESCALADA JÁ UTILIZADA] → tratar como INVALIDA e PARAR com o output do gate. O teto de 1 escalada por processo é INVIOLÁVEL.</escalar_segunda_vez>
  <citacao_sem_lastro>verificar_citacoes.py sai com exit 1 → na Etapa 4: REGENERAR a fundamentação com a lista de linhas [ERRO] anexada ao prompt (máx 2 tentativas; depois PARAR com o output do gate). Na Etapa 6: VOLTAR à Etapa 4 (máx 1 volta — a sentença herda a citação da fundamentação; corrige-se lá e re-mergeia na Etapa 5).</citacao_sem_lastro>
  <fontes_rejeitadas>merge_fontes.py sai com exit 1 → os itens rejeitados vêm NOMEADOS no stdout; NÃO é fatal (os válidos são gravados em $NUMERO-fontes.json) — anotar os rejeitados para o resumo final.</fontes_rejeitadas>
  <limite_tentativas>2 por etapa; na 2ª falha o pipeline PARA com o diagnóstico do gate (não silencia). Exceções nomeadas: fonte de pesquisa vira INDISPONÍVEL (não trava o trilho); a escalada tem teto próprio de 1 ciclo.</limite_tentativas>
</contingencias>

<contratos_dados>
  | # | Etapa | Agente | Entrada | Saída | Validação |
  |---|-------|--------|---------|-------|-----------|
  | 0 | Preparação | — | $ARGUMENTS | $WORKSPACE, $NUMERO + varredura | processo.txt existe; PENDENTES conhecidas |
  | 1 | Linha do tempo | extracao/linha-tempo-processual.md | processo.txt | $NUMERO-linha-tempo.md | verificar --etapa linha-tempo → 0 |
  | 2 | Relatório | extracao/relator-marmelstein.md | processo.txt + linha-tempo | $NUMERO-relatorio.md | verificar --etapa relatorio → 0 |
  | 2.5 | Triagem (SEMPRE) | analise/triador-processual.md | relatório | $NUMERO-triagem.md + fontes-triagem.json | verificar --etapa triagem → 0; depois merge_fontes.py e --rota → ROTA/TEMA/FATO (exit 0) |
  | 2.6 | Trilho de pesquisa [SE "pesquisa" na ROTA] | pesquisa/pesquisador-* + consolidador-pesquisa | linhas TEMA da triagem | $NUMERO-pesquisa-*.md + fontes-*.json + $NUMERO-precedentes-consolidado.md | verificar_pesquisa --etapa <fonte>/consolidado; fechamento --etapas <subconjunto-ok>,consolidado --gate → 0; merge_fontes.py re-roda |
  | 2.7 | Trilho probático [SE "probatica" na ROTA] | analise/inventariador + probatica-* + consolidador-probatica | processo.txt + linhas FATO da triagem | $NUMERO-inventario/-pearl/-haack/-probatica-fbd/-probatica-consolidado.md | verificar_probatica --etapa <nome>; fechamento --etapas inventario,pearl,haack,fbd,consolidado --gate → 0 |
  | 3 | Análise | analise/analisador-marmelstein.md | relatório + linha-tempo (+ consolidados dos trilhos que rodaram) | $NUMERO-analise.md | verificar --etapa analise → 0 (exit 3 = ESCALAR → válvula; exit 1 → contingência) |
  | 4 | Fundamentação | analise/fundamentador-marmelstein.md | relatório + análise + linha-tempo + $NUMERO-fontes.json (+ precedentes-consolidado se existir) | $NUMERO-fundamentacao.md | DUPLA: verificar --etapa fundamentacao → 0 E verificar_citacoes.py → 0 |
  | 5 | Merge | — (script) | relatório + fundamentação | $NUMERO-sentenca.md | merge_sentenca.py → 0 |
  | 6 | Finalização | — | tudo | resumo ao usuário | verificar --gate → 0 E verificar_citacoes.py --doc=-sentenca.md → 0 |

  Os marcadores de cada documento do tronco estão CODIFICADOS no verificar_sentenca.py; os dos
  trilhos, no verificar_pesquisa.py e no verificar_probatica.py — fonte única; este arquivo não
  os duplica. O contrato da rota (C2), do ESCALAR (C3/C4) e do arquivo de fontes (C1) está no
  plano 2026-07-11 e nos scripts que os validam.
</contratos_dados>

<fases_pipeline>

  <etapa numero="0" nome="Preparação, gate e retomada">
    <acao_orquestrador>
      1. $ARGUMENTS: caminho da pasta (→ $WORKSPACE; $NUMERO = padrão CNJ no nome) ou número (→ localizar a pasta em data/sentenca/ ou data/decisao/). Vazio/inválido → PARAR e pedir.
      2. Bash: test -f "$WORKSPACE/processo.txt" — se faltar, PARAR (a entrada do pipeline é o processo.txt).
      3. Bash: python scripts/verificar_sentenca.py "$WORKSPACE"
         → a linha "PENDENTES: ..." é o plano de execução (a varredura agora INCLUI a triagem:
         workspaces pré-v3.1 acusam "triagem" pendente — comportamento desejado, ganham a triagem
         na retomada sem repagar as demais etapas). Tudo "(nenhuma)" → pular direto à Etapa 6
         (o pipeline já estava completo). Reportar ao usuário o que será PULADO por já estar válido.
      4. TodoWrite com as etapas do TRONCO — as já válidas nascem completed:
         [{content: "Etapa 0 - Preparação", status: "completed", activeForm: "Preparando"},
          {content: "Etapa 1 - Linha do Tempo", status: <pendente? "pending" : "completed">, activeForm: "Extraindo cronologia"},
          {content: "Etapa 2 - Relatório", ...}, {content: "Etapa 2.5 - Triagem", ...},
          {content: "Etapa 3 - Análise", ...}, {content: "Etapa 4 - Fundamentação", ...},
          {content: "Etapa 5 - Merge", ...},
          {content: "Etapa 6 - Finalização", status: "pending", activeForm: "Finalizando"}]
         Os todos dos TRILHOS (2.6/2.7) NÃO entram aqui — são acrescentados DINAMICAMENTE na
         Etapa 2.5, quando a ROTA for conhecida.
    </acao_orquestrador>
    <transicao>Ir para a PRIMEIRA etapa pendente (ordem 1 → 2 → 2.5 → 3 → 4 → 5). Se houver QUALQUER etapa pendente de 3 em diante, a Etapa 2.5 executa ao menos os passos de script (merge de fontes e --rota) — a rota desta execução vem de lá.</transicao>
  </etapa>

  <etapa numero="1" nome="Linha do tempo (opus)">
    <retomada>Se "linha-tempo" NÃO está em PENDENTES → pular (não despachar).</retomada>
    <acao_orquestrador>
      Task (opus) com o prompt-invólucro:
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE EXTRAÇÃO. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/extracao/linha-tempo-processual.md — sua capacidade; siga fielmente.</passo>
      <passo>Read: $WORKSPACE/processo.txt (integral; em blocos se extenso).</passo>
      <passo>Aplicar o método e GRAVAR (Write) o documento COMPLETO em $WORKSPACE/$NUMERO-linha-tempo.md — com os marcadores de início/fim e as seções que o seu prompt define, em português COM acentos.</passo>
      <passo>Responder APENAS: "linha-tempo OK | $NUMERO-linha-tempo.md" — NÃO imprimir o documento.</passo>
      <restricoes>Apenas extração (não analisar, não sugerir decisão); NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Validar: Bash: python scripts/verificar_sentenca.py "$WORKSPACE" --etapa linha-tempo
      (exit 1 → contingência etapa_invalida).
    </acao_orquestrador>
    <transicao>Gate 0 → Etapa 2.</transicao>
  </etapa>

  <etapa numero="2" nome="Relatório (opus)">
    <retomada>Se "relatorio" não está em PENDENTES → pular.</retomada>
    <acao_orquestrador>
      Task (opus):
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE EXTRAÇÃO. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/extracao/relator-marmelstein.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-linha-tempo.md (marcos e fase atual)</passo>
      <passo>Read: $WORKSPACE/processo.txt (integral; em blocos se extenso)</passo>
      <passo>Gerar o relatório no formato do agente e GRAVAR (Write) em $WORKSPACE/$NUMERO-relatorio.md — documento completo, com acentos, sem asteriscos/hashtags no corpo.</passo>
      <passo>Responder APENAS: "relatorio OK | $NUMERO-relatorio.md"</passo>
      <restricoes>IDs quando disponíveis; NUNCA usar TodoWrite; NÃO imprimir o documento.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Validar: Bash: python scripts/verificar_sentenca.py "$WORKSPACE" --etapa relatorio
    </acao_orquestrador>
    <transicao>Gate 0 → Etapa 2.5.</transicao>
  </etapa>

  <etapa numero="2.5" nome="Triagem cognitiva (sonnet) — SEMPRE obrigatória">
    <retomada>Se "triagem" NÃO está em PENDENTES → NÃO despachar a Task do triador (passo 1). Os passos 2-4 (merge de fontes, --rota, todos dinâmicos) rodam SEMPRE — são scripts baratos e idempotentes, e é deles que sai a rota desta execução (inclusive na retomada pós-/clear: a rota gravada em disco é respeitada).</retomada>
    <acao_orquestrador>
      1. [SÓ se "triagem" em PENDENTES] Task (sonnet) com o prompt-invólucro:
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE TRIAGEM. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/analise/triador-processual.md — sua capacidade; siga fielmente.</passo>
      <passo>Read: $WORKSPACE/$NUMERO-relatorio.md (questões jurídicas e pontos controvertidos).</passo>
      <passo>Executar o reconhecimento do seu método (MÁXIMO 4 buscas curtas — BNP: +termo -termo "frase"; JULIA: operadores em minúsculo) e classificar cada ponto controvertido: resolve-se por TESE ou por PROVA?</passo>
      <passo>GRAVAR (Write) a triagem COMPLETA em $WORKSPACE/$NUMERO-triagem.md — abrindo com "# Triagem Cognitiva do Processo", com as seções "## QUESTÕES IDENTIFICADAS" e "## EVIDÊNCIAS", exatamente UM bloco cercado ```json (rota, temas_pesquisa, fatos_probatorios, justificativa_rotina), fechando com "Triagem concluída.", em português COM acentos.</passo>
      <passo>GRAVAR (Write) $WORKSPACE/fontes-triagem.json — trecho_verbatim é cópia EXATA do que os MCPs retornaram; nada encontrado → {"fontes": []}.</passo>
      <passo>Responder APENAS: "triagem OK | $NUMERO-triagem.md" — NÃO imprimir os documentos.</passo>
      <restricoes>Apenas rotear (não decidir mérito, não antecipar a análise); rota [] exige justificativa_rotina afirmativa; NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Validar: Bash: python scripts/verificar_sentenca.py "$WORKSPACE" --etapa triagem
      (exit 1 → contingência etapa_invalida).
      2. Merge de fontes — SEMPRE, mesmo em rota direta (garante $NUMERO-fontes.json com as teses
         colhidas no reconhecimento, que a fundamentação vai citar):
         Bash: python scripts/merge_fontes.py "$WORKSPACE" --id "$NUMERO"
         (exit 1 = itens rejeitados NOMEADOS no stdout; NÃO-fatal — anotar para o resumo final;
         contingência fontes_rejeitadas.)
      3. Ler a rota — SEMPRE:
         Bash: python scripts/verificar_sentenca.py "$WORKSPACE" --rota
         → saída em linhas simples: "ROTA: pesquisa probatica" (ou "ROTA: direta"), UMA linha
         "TEMA: ..." por tema de pesquisa e UMA linha "FATO: ..." por fato probatório; em rota
         direta vem também "JUSTIFICATIVA: ..." (a justificativa_rotina, citada no resumo da
         Etapa 6 sem ler o documento).
         (exit 1 → tratar a triagem como INVÁLIDA: contingência rota_invalida — redespachar o
         triador com a mensagem [ERRO] anexada; máx 2 tentativas.)
      4. TodoWrite DINÂMICO: acrescentar os todos dos trilhos que a ROTA exigir —
         {content: "Etapa 2.6 - Trilho de pesquisa", ...} se "pesquisa" na ROTA;
         {content: "Etapa 2.7 - Trilho probático", ...} se "probatica" na ROTA
         — nascendo completed se o gate do respectivo trilho já estiver todo OK (retomada).
    </acao_orquestrador>
    <transicao>ROTA contém "pesquisa" → Etapa 2.6. Senão, ROTA contém "probatica" → Etapa 2.7. ROTA direta → Etapa 3.</transicao>
  </etapa>

  <etapa numero="2.6" nome="Trilho de pesquisa (condicional) — SÓ SE 'pesquisa' na ROTA" modo="paralelo">
    <retomada>O trilho tem retomada PRÓPRIA, pelo gate do pipeline-pesquisa:
      Bash: python scripts/verificar_pesquisa.py "$WORKSPACE" --etapas bnp,cjf,julia,consolidado
      → a linha PENDENTES é o plano DO TRILHO (sem --gate a varredura de subconjunto SEMPRE sai 0 — ela informa, não bloqueia).
      STJ/TNU: incluir no subconjunto APENAS se os MCPs correspondentes estiverem conectados NESTA sessão (ferramentas mcp__claude_ai_PESQUISA_STJ__* e mcp__tnu-eproc__* disponíveis); se incluídos, usar o subconjunto ampliado bnp,cjf,julia,stj,tnu,consolidado em TODOS os comandos do trilho. Nada pendente → pular direto ao fechamento (passo 4).</retomada>
    <acao_orquestrador>
      $TEMAS = as linhas "TEMA:" lidas na Etapa 2.5 (tema de pesquisa injetado nos envelopes).
      1. Task (sonnet) para CADA fonte pendente, em PARALELO no MESMO turno (exemplo BNP):
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE PESQUISA. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/pesquisa/pesquisador-bnp.md — sua capacidade; siga fielmente.</passo>
      <passo>Pesquisar via MCP (mcp__bnp-api__buscar_precedentes) os TEMAS da triagem: $TEMAS
             Sintaxe BNP: +termo -termo "frase" (NÃO use E, OU, NAO); priorize Repercussão Geral
             e Repetitivos; transcreva teses EXATAS.</passo>
      <passo>GRAVAR (Write) o relatório COMPLETO em $WORKSPACE/$NUMERO-pesquisa-bnp.md — abrindo com
             "# Pesquisa BNP", fechando com "Pesquisa BNP concluída.", em português COM acentos.</passo>
      <passo>GRAVAR (Write) o parcial $WORKSPACE/fontes-bnp.json no schema da seção saida_fontes do
             seu prompt — trecho_verbatim é cópia EXATA do que o MCP retornou; sem resultados →
             {"fontes": []}.</passo>
      <passo>Responder APENAS: "bnp OK | $NUMERO-pesquisa-bnp.md" — NÃO imprimir o documento.</passo>
      <restricoes>NUNCA inventar precedentes; NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Variações por fonte (mesmo invólucro, trocando agente, arquivos e lembrete de sintaxe):
      - CJF → .claude/agents/pesquisa/pesquisador-cjf.md; $NUMERO-pesquisa-cjf.md; fontes-cjf.json;
        abre "# Pesquisa CJF", fecha "Pesquisa CJF concluída.".
        Sintaxe CJF: E OU NAO ADJ PROX (MAIÚSCULO); pesquise APENAS TRF1, TRF3, TRF4
        (tribunais="TRF1,TRF3,TRF4" — únicas bases vivas do CJF; STF/STJ/TRF5 têm fontes
        próprias); identifique divergências regionais.
      - JULIA → .claude/agents/pesquisa/pesquisador-julia.md; $NUMERO-pesquisa-julia.md; fontes-julia.json;
        abre "# Pesquisa JULIA", fecha "Pesquisa JULIA concluída.".
        Sintaxe JULIA: e ou nao adj prox $ (minúsculo); analise por turma; verifique IRDRs vinculantes.
      - STJ (só se no subconjunto) → .claude/agents/pesquisa/pesquisador-stj.md; $NUMERO-pesquisa-stj.md;
        fontes-stj.json; abre "# Pesquisa STJ", fecha "Pesquisa STJ concluída.".
        Sintaxe STJ: espaço é E implícito, ou nao "frase" termo* (sem parênteses); priorize
        repetitivos e súmulas; transcreva teses EXATAS.
      - TNU (só se no subconjunto) → .claude/agents/pesquisa/pesquisador-tnu.md; $NUMERO-pesquisa-tnu.md;
        fontes-tnu.json; abre "# Pesquisa TNU", fecha "Pesquisa TNU concluída.".
        Sintaxe TNU: e ou nao prox * "frase" (prox SEM número); use somente_precedentes_relevantes
        para os representativos; foque uniformização/JEFs.
      2. Validar CADA fonte despachada:
         Bash: python scripts/verificar_pesquisa.py "$WORKSPACE" --etapa bnp   (idem cjf, julia, stj, tnu)
         (exit 1 → redespachar SÓ a fonte reprovada com o motivo do gate anexado; máx 2 tentativas;
         na 2ª falha → contingência fonte_indisponivel_no_trilho: INDISPONÍVEL e seguir. Task que
         reporta MCP desconectado → INDISPONÍVEL DIRETO, sem gastar tentativas. Ao menos 1 fonte
         com gate OK é OBRIGATÓRIA — todas indisponíveis → PARAR.)
      3. Consolidação [se "consolidado" pendente OU alguma pesquisa foi regenerada agora] — Task (sonnet):
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE CONSOLIDAÇÃO. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/pesquisa/consolidador-pesquisa.md — sua capacidade; siga fielmente.</passo>
      <passo>Read: [listar aqui APENAS os relatórios com gate OK, ex.: $WORKSPACE/$NUMERO-pesquisa-bnp.md,
             $WORKSPACE/$NUMERO-pesquisa-cjf.md, $WORKSPACE/$NUMERO-pesquisa-julia.md — fonte
             INDISPONÍVEL fica de fora e deve ser registrada como ausente no consolidado].</passo>
      <passo>Analisar interseções e divergências (TEMAS: $TEMAS) e GRAVAR (Write) o relatório COMPLETO
             em $WORKSPACE/$NUMERO-precedentes-consolidado.md — abrindo com
             "# Relatório Consolidado de Precedentes", com a classificação por hierarquia vinculante
             (RG > RR > IRDR > Súmula), fechando com "Consolidação realizada com base nas pesquisas
             disponíveis.", em português COM acentos.</passo>
      <passo>Responder APENAS: "consolidado OK | $NUMERO-precedentes-consolidado.md" — NÃO imprimir o documento.</passo>
      <restricoes>NUNCA inventar precedentes ausentes dos relatórios; NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Validar: Bash: python scripts/verificar_pesquisa.py "$WORKSPACE" --etapa consolidado
      (exit 1 → contingência etapa_invalida; 2ª falha → PARAR e reportar).
      4. Fechamento EXIT-CODED do trilho (com o subconjunto que ficou OK):
         Bash: python scripts/verificar_pesquisa.py "$WORKSPACE" --etapas <subconjunto-ok>,consolidado --gate
         (ex.: --etapas bnp,cjf,julia,consolidado --gate; fonte INDISPONÍVEL fica FORA do
         subconjunto. Exit 1 → algo regrediu; PARAR e reportar.)
      5. Re-rodar o merge de fontes (agora com os parciais novos do trilho):
         Bash: python scripts/merge_fontes.py "$WORKSPACE" --id "$NUMERO"
         (exit 1 não-fatal — contingência fontes_rejeitadas.)
    </acao_orquestrador>
    <transicao>ROTA contém "probatica" → Etapa 2.7. Senão → Etapa 3.</transicao>
  </etapa>

  <etapa numero="2.7" nome="Trilho probático (condicional) — SÓ SE 'probatica' na ROTA" modo="paralelo">
    <retomada>O trilho tem retomada PRÓPRIA, pelo gate do pipeline-probatica:
      Bash: python scripts/verificar_probatica.py "$WORKSPACE" --etapas inventario,pearl,haack,fbd,consolidado
      → a linha PENDENTES é o plano DO TRILHO. Nada pendente → pular direto ao fechamento (passo 4).</retomada>
    <acao_orquestrador>
      $FATOS = as linhas "FATO:" lidas na Etapa 2.5 (focos probatórios injetados nos envelopes).
      1. Inventário [se "inventario" pendente] — Task (opus):
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE INVENTARIADOR. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/analise/inventariador-probatica.md — sua capacidade; siga fielmente.</passo>
      <passo>Read: $WORKSPACE/processo.txt (integral; em blocos se extenso). Fazer MÚLTIPLAS PASSAGENS
             conforme a estratégia multi-pass do agente (Pass 1 indexação → Pass 2 catalogação):
             provas podem estar em QUALQUER parte do processo.</passo>
      <passo>Catalogar TODAS as provas com ZERO VALORAÇÃO (descrever, nunca avaliar), com atenção
             especial aos FOCOS da triagem: $FATOS — e GRAVAR (Write) o documento COMPLETO em
             $WORKSPACE/$NUMERO-inventario.md — abrindo com "# INVENTÁRIO PROBATÓRIO", fechando com
             "É o que satisfaz inventariar do acervo probatório.", em português COM acentos.</passo>
      <passo>Responder APENAS: "inventario OK | $NUMERO-inventario.md" — NÃO imprimir o documento.</passo>
      <restricoes>Apenas catalogação descritiva (sem juízo de força/credibilidade); NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Validar: Bash: python scripts/verificar_probatica.py "$WORKSPACE" --etapa inventario
      (exit 1 → contingência etapa_invalida; máx 2 tentativas).
      2. Tríplice metodológica em PARALELO (só as pendentes; até 3 Tasks opus no MESMO turno) — exemplo Pearl:
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE ANÁLISE CAUSAL (PEARL). EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/analise/probatica-pearl.md — sua capacidade; siga fielmente.</passo>
      <passo>Read: $WORKSPACE/processo.txt (integral; em blocos se extenso)</passo>
      <passo>Read: $WORKSPACE/$NUMERO-linha-tempo.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-relatorio.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-inventario.md</passo>
      <passo>Aplicar o método do agente com FOCO PRIORITÁRIO nos fatos da triagem: $FATOS — e GRAVAR
             (Write) o documento COMPLETO em $WORKSPACE/$NUMERO-pearl.md — abrindo com
             "# Análise Probatória Causal", fechando com "Análise causal concluída.",
             em português COM acentos.</passo>
      <passo>Responder APENAS: "pearl OK | $NUMERO-pearl.md" — NÃO imprimir o documento.</passo>
      <restricoes>NUNCA confundir correlação com causalidade; NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Variações por análise (mesmo invólucro — mesmas 5 leituras e o mesmo foco $FATOS —, trocando
      agente, arquivo de saída e lembrete metodológico):
      - HAACK → .claude/agents/analise/probatica-haack.md; grava $NUMERO-haack.md;
        abre "# Análise Probatória Foundherentista", fecha "Análise foundherentista concluída.".
        Método: 7 fases; warrant nas 3 dimensões; SEM probabilidades numéricas.
      - FBD → .claude/agents/analise/probatica-fbd.md; grava $NUMERO-probatica-fbd.md;
        abre "## MOVIMENTO 1 — ENQUADRAMENTO", fecha "Análise probatória FBD concluída.".
        Método: 7 movimentos sequenciais; escala ordinal, sem valores numéricos.
      Validar CADA análise:
      Bash: python scripts/verificar_probatica.py "$WORKSPACE" --etapa pearl   (idem haack, fbd)
      (exit 1 → redespachar SÓ a análise reprovada com o motivo do gate anexado; máx 2 tentativas;
      na 2ª falha → PARAR — o consolidador exige as três análises.)
      3. Consolidação [se "consolidado" pendente OU alguma análise da tríplice foi regenerada agora] — Task (opus):
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE CONSOLIDADOR. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/analise/consolidador-probatica.md — sua capacidade; siga fielmente.</passo>
      <passo>Read: $WORKSPACE/$NUMERO-pearl.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-haack.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-probatica-fbd.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-inventario.md</passo>
      <passo>Mapear convergências (fortes e parciais), divergências (metodológicas e factuais),
             lacunas, obscuridades, omissões e contradições, produzir a síntese integrativa e
             GRAVAR (Write) o documento COMPLETO em $WORKSPACE/$NUMERO-probatica-consolidado.md —
             abrindo com "# SÍNTESE PROBATÓRIA CONSOLIDADA", fechando com
             "Síntese probatória consolidada concluída.", em português COM acentos.</passo>
      <passo>Responder APENAS: "consolidado OK | $NUMERO-probatica-consolidado.md" — NÃO imprimir o documento.</passo>
      <restricoes>NUNCA inventar análises ausentes; NUNCA omitir divergências; NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Validar: Bash: python scripts/verificar_probatica.py "$WORKSPACE" --etapa consolidado
      (exit 1 → contingência etapa_invalida; 2ª falha → PARAR e reportar).
      4. Fechamento EXIT-CODED do trilho:
         Bash: python scripts/verificar_probatica.py "$WORKSPACE" --etapas inventario,pearl,haack,fbd,consolidado --gate
         (exit 1 → algo regrediu; PARAR e reportar.)
    </acao_orquestrador>
    <transicao>Gate do trilho 0 → Etapa 3.</transicao>
  </etapa>

  <etapa numero="3" nome="Análise (opus) — insumos condicionais e válvula ESCALAR">
    <retomada>Se "analise" não está em PENDENTES → pular. (Na varredura, análise com fecho ESCALAR aparece como "[ESCALAR] analise" e CONTA como pendente — o tratamento é o do passo 3, não um redespacho cego.)</retomada>
    <acao_orquestrador>
      1. Task (opus) — os passos condicionais entram APENAS se o artefato existir (o trilho correspondente rodou/está válido):
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE ANÁLISE. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/analise/analisador-marmelstein.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-linha-tempo.md (fase processual)</passo>
      <passo>Read: $WORKSPACE/$NUMERO-relatorio.md (fatos, argumentos, pedidos)</passo>
      <passo>[SE o trilho 2.6 rodou/está válido] Read: $WORKSPACE/$NUMERO-precedentes-consolidado.md — dialogue com a pesquisa, não a repita.</passo>
      <passo>[SE o trilho 2.7 rodou/está válido] Read: $WORKSPACE/$NUMERO-probatica-consolidado.md — use a síntese probatória, não refaça a valoração do zero.</passo>
      <passo>Gerar a análise no formato do agente (todas as seções) e GRAVAR (Write) em $WORKSPACE/$NUMERO-analise.md.</passo>
      <passo>Responder APENAS: "analise OK | $NUMERO-analise.md"</passo>
      <restricoes>Identificar a fase e a questão pendente; NUNCA usar TodoWrite; NÃO imprimir o documento.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      2. Validar: Bash: python scripts/verificar_sentenca.py "$WORKSPACE" --etapa analise
         → exit 0: "[OK] analise" → Etapa 4.
         → exit 1: [AUSENTE]/[INVALIDA] → contingência etapa_invalida (máx 2 tentativas).
         → exit 3: "[ESCALAR] analise: <trilhos> — <motivo>" → VÁLVULA ESCALAR (passo 3).
      3. REGRA DA ESCALADA (MÁXIMO 1 ciclo por processo):
         (i) Identificar o(s) trilho(s) pedidos na linha [ESCALAR] (pesquisa e/ou probatica).
             O motivo vem NORMALIZADO pelo gate (minúsculas, sem acentos) — usar como está ao
             anexá-lo nos despachos seguintes.
         (ii) DETECÇÃO PERSISTENTE em disco (sobrevive a /clear): para cada trilho pedido, checar
              se ele JÁ passa no gate dele —
              pesquisa:  Bash: python scripts/verificar_pesquisa.py "$WORKSPACE" --etapas consolidado --gate
              probatica: Bash: python scripts/verificar_probatica.py "$WORKSPACE" --etapas consolidado --gate
              (o consolidado é o PRODUTO final do trilho: só existe válido se o trilho rodou —
              inclusive rodada degradada com fonte INDISPONÍVEL, cujo subconjunto exato não é
              recuperável após /clear).
              Se TODOS os trilhos pedidos já passam → a escalada JÁ FOI HONRADA: redespachar a
              análise DIRETO (mesmo invólucro do passo 1, insumos condicionais incluídos) com a
              marca anexada ao prompt (o token exato [ESCALADA JÁ UTILIZADA] é a exceção do agente):
              [ESCALADA JÁ UTILIZADA] — conclua com os insumos disponíveis, registrando a limitação.
              — SEM re-rodar trilho (contingência escalar_trilho_ja_rodado: comportamento esperado).
         (iii) Senão: rodar o(s) trilho(s) pedido(s) que faltam com a MESMA mecânica das Etapas
              2.6/2.7 (retomada própria, envelopes, gates por etapa, fechamento exit-coded e — no
              caso da pesquisa — re-rodar merge_fontes.py; temas/fatos: os da triagem,
              complementados pelo motivo da linha [ESCALAR]) e redespachar a análise com o insumo
              novo E a mesma marca [ESCALADA JÁ UTILIZADA] (com a instrução do item ii) anexada
              (a marca é o teto do ciclo).
         (iv) Validar de novo: --etapa analise → exit 0 → Etapa 4; exit 3 DE NOVO após redespacho
              com a marca → contingência escalar_segunda_vez: tratar como INVALIDA e PARAR com o
              output do gate.
    </acao_orquestrador>
    <transicao>Gate 0 → Etapa 4.</transicao>
  </etapa>

  <etapa numero="4" nome="Fundamentação (opus) — regime verbatim">
    <retomada>Se "fundamentacao" não está em PENDENTES → NÃO despachar a Task (passo 1). O gate de citações (passo 2b) roda MESMO ASSIM — fundamentação reaproveitada de workspace pré-v3.1 nunca passou pelo regime; se reprovar, ela é REGENERADA (despacho do passo 1 com a lista de [ERRO] anexada).</retomada>
    <acao_orquestrador>
      1. Task (opus) — o orquestrador confere antes com Bash (test -f) quais insumos condicionais existem:
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE REDAÇÃO. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/analise/fundamentador-marmelstein.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-linha-tempo.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-relatorio.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-analise.md ("O Caminho Que Me Parece Mais Justo" dá o direcionamento)</passo>
      <passo>[SE $WORKSPACE/$NUMERO-fontes.json existir] Read: $WORKSPACE/$NUMERO-fontes.json —
             este arquivo é a ÚNICA origem admitida para citar jurisprudência: siga o
             <regime_citacao> do seu prompt (aspas SÓ com cópia EXATA de trecho_verbatim deste
             arquivo ou de trecho dos autos; todo precedente invocado, mesmo parafraseado, deve
             constar dele). Sem o arquivo: NÃO citar jurisprudência entre aspas.</passo>
      <passo>[SE $WORKSPACE/$NUMERO-precedentes-consolidado.md existir] Read: $WORKSPACE/$NUMERO-precedentes-consolidado.md (hierarquia vinculante e recomendações da pesquisa)</passo>
      <passo>Gerar FUNDAMENTAÇÃO + DISPOSITIVO (sucumbência, comando decisório correto) e GRAVAR (Write) em $WORKSPACE/$NUMERO-fundamentacao.md.</passo>
      <passo>Responder APENAS: "fundamentacao OK | $NUMERO-fundamentacao.md"</passo>
      <restricoes>NÃO inventar legislação/precedente/doutrina; doutrina NÃO entra na minuta automatizada; NUNCA usar TodoWrite; NÃO imprimir o documento.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      2. VALIDAÇÃO DUPLA:
         a) Formato: Bash: python scripts/verificar_sentenca.py "$WORKSPACE" --etapa fundamentacao
            (exit 1 → contingência etapa_invalida; máx 2 tentativas).
         b) Citações: Bash: python scripts/verificar_citacoes.py "$WORKSPACE"
            (documento default: $NUMERO-fundamentacao.md; corpus: $NUMERO-fontes.json + processo.txt)
            exit 1 → contingência citacao_sem_lastro: REGENERAR a fundamentação (mesmo invólucro do
            passo 1) com a lista de linhas [ERRO] do gate anexada ao prompt e a instrução: "as
            citações listadas NÃO têm lastro no corpus — substitua cada uma por cópia exata de
            trecho_verbatim do arquivo de fontes (ou dos autos) ou parafraseie SEM aspas"; máx 2
            tentativas; persistindo → PARAR com o output do gate.
    </acao_orquestrador>
    <transicao>Gates a) e b) em 0 → Etapa 5.</transicao>
  </etapa>

  <etapa numero="5" nome="Merge (script, sem LLM)">
    <retomada>Se "sentenca" não está em PENDENTES E as etapas 2 e 4 não rodaram nesta execução → pular. Se relatório OU fundamentação foram regenerados agora, o merge RODA de novo (a sentença antiga está desatualizada).</retomada>
    <acao_orquestrador>
      Bash: python scripts/merge_sentenca.py "$WORKSPACE"
      → concatena, grava e valida $NUMERO-sentenca.md sem passar conteúdo pelo contexto.
      Exit 1 com "entrada inválida" → voltar à etapa apontada (contingência falha_de_entrada).
    </acao_orquestrador>
    <transicao>Exit 0 → Etapa 6.</transicao>
  </etapa>

  <etapa numero="6" nome="Finalização — gate global + citações na sentença">
    <acao_orquestrador>
      1. Gate final: Bash: python scripts/verificar_sentenca.py "$WORKSPACE" --gate
         (agora INCLUI a triagem; exit 1 → algo regrediu; reportar o output e PARAR).
      2. Citações na SENTENÇA (ela herda as citações da fundamentação via merge):
         Bash: python scripts/verificar_citacoes.py "$WORKSPACE" --doc=-sentenca.md
         (forma "--doc=" OBRIGATÓRIA — o valor começa com hífen e o argparse rejeita
         "--doc -sentenca.md" com o valor separado por espaço.)
         Exit 1 → VOLTAR à Etapa 4 (regenerar a fundamentação com a lista de [ERRO] anexada e
         re-mergear na Etapa 5) — MÁXIMO 1 volta; persistindo, PARAR com o output do gate.
      3. Resumo ao usuário:
         - Número do processo e caminho da sentença final ($WORKSPACE/$NUMERO-sentenca.md)
         - ROTA tomada (se direta, citar a linha "JUSTIFICATIVA: ..." impressa pelo --rota) e
           trilhos rodados (2.6/2.7 e eventual escalada da Etapa 3) — se a saída do --rota não
           estiver no contexto (ex.: pulo direto da Etapa 0 para cá), obtê-la por:
           Bash: python scripts/verificar_sentenca.py "$WORKSPACE" --rota
           (nunca lendo a triagem: a justificativa vem da linha JUSTIFICATIVA do script)
         - Fontes: nº de itens válidos em $NUMERO-fontes.json e itens REJEITADOS no merge, se
           houver (do stdout do merge_fontes.py)
         - Artefatos em $WORKSPACE: REAPROVEITADOS da execução anterior × gerados agora
         — Ingestão no Kanban (opcional): python scripts/ingerir_kanban.py "$NUMERO" — move o workspace para data/sentenca/01-por-analisar/ (visível no frontend).
    </acao_orquestrador>
  </etapa>

</fases_pipeline>

<resumo_arquitetura>
PIPELINE SENTENÇA v3.1 — triagem + trilhos condicionais + regime verbatim + gate determinístico + retomada
│
├── 0   Preparação: $WORKSPACE/$NUMERO + verificar_sentenca.py → PENDENTES (o plano; inclui triagem)
├── 1   Linha do tempo   [Task opus]   → $NUMERO-linha-tempo.md
├── 2   Relatório        [Task opus]   → $NUMERO-relatorio.md
├── 2.5 Triagem (SEMPRE) [Task sonnet] → $NUMERO-triagem.md + fontes-triagem.json
│       gate --etapa triagem → merge_fontes.py (SEMPRE, mesmo rota direta) → --rota → ROTA/TEMA/FATO
│       (rota direta imprime também JUSTIFICATIVA — citada no resumo da Etapa 6)
│       TodoWrite dinâmico: todos dos trilhos que a ROTA exigir
├── 2.6 [SE "pesquisa" na ROTA] Trilho de pesquisa no $WORKSPACE ($ID = $NUMERO):
│       pesquisadores em PARALELO [Tasks sonnet] (temas = linhas TEMA) → consolidador → merge_fontes.py
│       retomada/gates: verificar_pesquisa.py --etapas bnp,cjf,julia,consolidado (varredura),
│       --etapa <fonte> (cada), fechamento exit-coded --etapas <subconjunto-ok>,consolidado --gate
│       (STJ/TNU entram no subconjunto só se os MCPs estiverem conectados; sem --gate a varredura
│       de subconjunto SEMPRE sai 0)
├── 2.7 [SE "probatica" na ROTA] Trilho probático no $WORKSPACE:
│       inventariador [opus] → Pearl+Haack+FBD em PARALELO [opus] → consolidador [opus] (fatos em
│       foco = linhas FATO); gates: verificar_probatica.py --etapa ..., fechamento exit-coded
│       --etapas inventario,pearl,haack,fbd,consolidado --gate
├── 3   Análise          [Task opus]   → $NUMERO-analise.md
│       insumos: relatório + linha-tempo (+ precedentes-consolidado se 2.6; + probatica-consolidado se 2.7)
│       gate --etapa analise: 0 → segue | 1 → contingência | 3 (ESCALAR) → detecção persistente em
│       disco (trilho pedido já passa no gate dele? → redespachar com [ESCALADA JÁ UTILIZADA]);
│       senão rodar o trilho pedido e redespachar com o insumo novo — MÁXIMO 1 ciclo; exit 3 de
│       novo após a marca → INVALIDA, PARAR
├── 4   Fundamentação    [Task opus]   → $NUMERO-fundamentacao.md
│       envelope informa $NUMERO-fontes.json (ÚNICA origem para citar jurisprudência — regime_citacao)
│       validação DUPLA: --etapa fundamentacao E verificar_citacoes.py (exit 1 → regenerar com a
│       lista de [ERRO]; máx 2)
├── 5   Merge            [SCRIPT]      → $NUMERO-sentenca.md (merge_sentenca.py; zero contexto)
└── 6   Finalização: --gate + verificar_citacoes.py --doc=-sentenca.md (forma "--doc=" obrigatória;
        exit 1 → voltar à Etapa 4, máx 1 volta) + resumo (rota tomada, trilhos rodados, fontes,
        reaproveitado × gerado)

Princípios: o documento vive no ARQUIVO (nunca na conversa); a validação é do SCRIPT (âncoras
normalizadas — fonte única nos verificar_*.py); PENDENTES é o plano (1ª rodada e retomada são a
mesma operação); a ROTA é lei (trilho só roda se pedido — exceção única: ESCALAR, 1 ciclo);
nenhuma citação sem lastro (fontes.json é a cadeia de custódia e verificar_citacoes.py é o juiz).
Vários processos = pipelines independentes em paralelo.
</resumo_arquitetura>

<checklist_orquestrador>
- [ ] processo.txt existe (test -f) e a varredura da Etapa 0 rodou?
- [ ] Todas as etapas VÁLIDAS foram puladas (nada redespachado)?
- [ ] Triagem validada por gate e rota lida por --rota (nunca lendo o documento)?
- [ ] merge_fontes.py rodou pós-triagem (SEMPRE, mesmo rota direta) e re-rodou após o trilho de pesquisa?
- [ ] ROTA respeitada — nenhum trilho despachado fora da rota; todos os exigidos rodaram ou já estavam válidos?
- [ ] Trilhos fechados EXIT-CODED (--etapas <subconjunto>,consolidado --gate)?
- [ ] Escalada ÚNICA — no máximo 1 ciclo ESCALAR, com detecção persistente em disco antes de re-rodar trilho?
- [ ] Citações verificadas nas etapas 4 (fundamentação) E 6 (--doc=-sentenca.md)?
- [ ] Nenhum documento lido pelo orquestrador (validação só por script)?
- [ ] Subagentes responderam só a linha de status?
- [ ] Merge pelo script (e re-rodado se relatório/fundamentação mudaram)?
- [ ] Gate final --gate retornou 0 antes do resumo?
- [ ] TodoWrite refletiu o reaproveitamento E os todos dinâmicos dos trilhos (Etapa 2.5)?
</checklist_orquestrador>
