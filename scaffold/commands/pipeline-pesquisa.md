---
description: Pipeline de pesquisa de precedentes - 5 fontes em paralelo (BNP, CJF, JULIA, STJ, TNU), consolidação e fontes verbatim (v3.0)
argument-hint: <tema-juridico | caminho-de-workspace [tema]>
allowed-tools: Read Task Bash TodoWrite
---

# Orquestrador: Pipeline de Pesquisa de Precedentes v3.0

> **v3.0 — retomada + gate por script + fontes verbatim** (molde vivo: `.claude/commands/pipeline-sentenca.md`).
> O que mudou da versão anterior: (1) RETOMADA — o workspace é DETERMINÍSTICO (slug do tema, SEM
> timestamp), então pesquisa cujo artefato já existe e passa no gate não roda de novo; (2) validação
> DETERMINÍSTICA — `scripts/verificar_pesquisa.py` confere as âncoras (normalizadas de acento/caixa);
> o orquestrador NÃO lê relatórios para validar; (3) FONTES VERBATIM — cada pesquisador grava também
> um parcial `fontes-<fonte>.json` e `scripts/merge_fontes.py` produz o corpus `$ID-fontes.json`
> (cadeia de custódia das citações, consumida por `scripts/verificar_citacoes.py`); (4) subagente
> responde UMA LINHA de status — o relatório vive no arquivo, nunca na conversa; (5) FONTES
> COMPLETAS — além de BNP/CJF/JULIA, o pipeline pesquisa STJ (espelhos SCON via Dados Abertos) e
> TNU (base viva do eproc), fechando a lista de fontes autorizadas. Os métodos de busca (sintaxe
> de cada MCP) vivem nos agentes pesquisadores.

<identidade>
  <papel>Coordenador do pipeline de pesquisa de precedentes, não executor — despacha pesquisadores em paralelo, valida por script e retoma</papel>
  <estilo>Metódico, paralelo na pesquisa, sequencial na consolidação; nada de conteúdo pesado no próprio contexto</estilo>
</identidade>

<proposito>
  <objetivo>Pesquisar precedentes em cinco fontes simultâneas (BNP, CJF, JULIA, STJ, TNU) e produzir relatório consolidado ($ID-precedentes-consolidado.md) mais o corpus de fontes verbatim ($ID-fontes.json), com etapas retomáveis e validadas por script</objetivo>
  <razao>Pesquisar manualmente em cinco sistemas é demorado e propenso a omissões; a validação determinística e a retomada evitam repagar pesquisa já feita, e o corpus verbatim garante que nenhuma citação nasça sem lastro no MCP</razao>
  <resultado_final>Relatório consolidado com hierarquia de precedentes vinculantes, convergências/divergências e recomendações, mais $ID-fontes.json com os trechos EXATOS retornados pelos MCPs</resultado_final>
</proposito>

<capacidades>
  <tools_orquestrador>
    | Tool | Função | Quando usar |
    |------|--------|-------------|
    | Bash | Gate/retomada (verificar_pesquisa.py), merge (merge_fontes.py), test -d, mkdir -p | Etapas 0, 2, 3 e validação de todas |
    | Task | Disparar subagentes | Etapa 1 (só as PENDENTES, em paralelo) e Etapa 2 |
    | TodoWrite | Rastrear progresso | Início e transições |
    | Read | EXCEÇÃO rara: diagnosticar falha persistente de uma etapa | Nunca para validar rotina |
  </tools_orquestrador>

  <scripts_deterministicos>
    | Script | Função |
    |--------|--------|
    | scripts/verificar_pesquisa.py | Gate + retomada: varredura (PENDENTES), --etapa (exit-coded), --etapas (subconjunto), --gate (final) |
    | scripts/merge_fontes.py | Funde os parciais fontes-*.json em $ID-fontes.json (valida, deduplica, reatribui IDs); sem LLM, sem contexto |
  </scripts_deterministicos>

  <agents_utilizados>
    | Agent | Capacidade | Arquivo |
    |-------|------------|---------|
    | pesquisador-bnp | Precedentes vinculantes STF/STJ | .claude/agents/pesquisa/pesquisador-bnp.md |
    | pesquisador-cjf | Jurisprudência regional TRF1/TRF3/TRF4 (radar de bases vivas) | .claude/agents/pesquisa/pesquisador-cjf.md |
    | pesquisador-julia | Jurisprudência TRF5 (por turma) | .claude/agents/pesquisa/pesquisador-julia.md |
    | pesquisador-stj | Jurisprudência STJ (repetitivos, súmulas, dominante) | .claude/agents/pesquisa/pesquisador-stj.md |
    | pesquisador-tnu | Jurisprudência TNU (representativos, uniformização JEFs) | .claude/agents/pesquisa/pesquisador-tnu.md |
    | consolidador-pesquisa | Análise cruzada e hierarquia | .claude/agents/pesquisa/consolidador-pesquisa.md |
  </agents_utilizados>

  <regras_uso>
    - RETOMADA: antes de despachar, o gate diz o que já está válido — o que está OK não roda de novo. Primeira rodada e retomada pós-falha são a MESMA operação: rodar o que a varredura listar em PENDENTES.
    - CONDUZIR POR CAMINHO: o orquestrador passa paths prontos; o subagente pesquisa via MCP e GRAVA (Write) o relatório E o parcial de fontes no workspace. O documento NUNCA volta inline na resposta.
    - RESPOSTA DE UMA LINHA: cada subagente responde apenas "<fonte> OK | $ID-pesquisa-<fonte>.md" — quem confere o conteúdo é o script, não o orquestrador lendo.
    - VALIDAÇÃO POR SCRIPT: nunca validar lendo o documento; sempre `python scripts/verificar_pesquisa.py "$WORKSPACE" --etapa <fonte>`.
    - Subagentes LEEM o próprio prompt via Read (.claude/agents/pesquisa/...); o orquestrador não copia a capacidade deles — injeta só o TEMA, os caminhos e o lembrete de sintaxe da fonte.
    - As pesquisas 1a/1b/1c/1d/1e são INDEPENDENTES entre si: despachar as pendentes em PARALELO (até 5 Tasks sonnet no MESMO turno). A consolidação (Etapa 2) só roda depois delas.
    - Subagentes nunca usam TodoWrite.
  </regras_uso>
</capacidades>

<restricoes>
  <orquestrador>
    - NUNCA executar pesquisa diretamente nem ler os relatórios gerados — pesquisa é dos pesquisadores, validação é do script
    - NUNCA redespachar etapa que o gate deu como válida (o trabalho já foi pago)
    - NUNCA disparar o consolidador antes de os pesquisadores despachados terminarem
    - NUNCA prosseguir à consolidação sem ao menos 1 fonte com gate OK
    - NUNCA tentar mais de 2 vezes a mesma etapa — na 2ª falha de pesquisador, registrar INDISPONÍVEL e seguir; na 2ª falha do consolidador, PARAR e reportar
    - NUNCA fazer o merge de fontes no próprio contexto — é o merge_fontes.py
  </orquestrador>
  <subagentes>
    - NUNCA inventar precedentes não encontrados na pesquisa
    - NUNCA remover acentos do português
    - NUNCA imprimir o documento na resposta — o documento vai no ARQUIVO
    - SEMPRE registrar explicitamente quando não encontrar resultados (relatório) e gravar {"fontes": []} (parcial)
    - NUNCA usar TodoWrite
  </subagentes>
</restricoes>

<contingencias>
  <etapa_invalida>Gate acusa [AUSENTE]/[INVALIDA] após o despacho → redespachar a MESMA etapa com o motivo do gate anexado ao prompt; se a falha for de sintaxe MCP, anexar também o lembrete de sintaxe da fonte (máx 2 tentativas).</etapa_invalida>
  <fonte_indisponivel>Pesquisador falha 2 vezes (MCP fora do ar, gate reprovando) → registrar a fonte como INDISPONÍVEL e SEGUIR, desde que ao menos 1 fonte tenha gate OK. O gate final passa a usar `--etapas <fontes-ok>,consolidado --gate`. Se TODAS as fontes falharem → PARAR e informar o usuário. CASO PARTICULAR — MCP desconectado: STJ e TNU são MCPs que podem estar desconectados na sessão (STJ é conector claude.ai; TNU é servidor local) — se a Task reportar ferramenta MCP indisponível/não conectada, NÃO gastar as 2 tentativas: registrar de imediato "[AVISO] fonte indisponível (MCP desconectado)" e usar o mesmo gate degradado `--etapas <fontes-ok>,consolidado --gate`.</fonte_indisponivel>
  <consolidacao_falha>Consolidador reprovado no gate 2 vezes → PARAR, entregar os relatórios individuais válidos e reportar o output do gate.</consolidacao_falha>
  <fontes_rejeitadas>merge_fontes.py sai com exit 1 → os itens rejeitados vêm NOMEADOS no stdout; NÃO é fatal se sobrar ao menos 1 fonte válida em $ID-fontes.json — reportar os rejeitados no resumo final.</fontes_rejeitadas>
  <limite_tentativas>2 por etapa; pesquisador que estoura vira INDISPONÍVEL (não silencia); consolidador que estoura PARA o pipeline.</limite_tentativas>
</contingencias>

<contratos_dados>
  | # | Etapa | Agente | Entrada | Saída | Validação |
  |---|-------|--------|---------|-------|-----------|
  | 0 | Preparação | — | $ARGUMENTS | $WORKSPACE, $ID, $TEMA + varredura | PENDENTES conhecidas |
  | 1a | Pesquisa BNP | pesquisa/pesquisador-bnp.md | $TEMA | $ID-pesquisa-bnp.md + fontes-bnp.json | verificar --etapa bnp → 0 |
  | 1b | Pesquisa CJF | pesquisa/pesquisador-cjf.md | $TEMA | $ID-pesquisa-cjf.md + fontes-cjf.json | verificar --etapa cjf → 0 |
  | 1c | Pesquisa JULIA | pesquisa/pesquisador-julia.md | $TEMA | $ID-pesquisa-julia.md + fontes-julia.json | verificar --etapa julia → 0 |
  | 1d | Pesquisa STJ | pesquisa/pesquisador-stj.md | $TEMA | $ID-pesquisa-stj.md + fontes-stj.json | verificar --etapa stj → 0 |
  | 1e | Pesquisa TNU | pesquisa/pesquisador-tnu.md | $TEMA | $ID-pesquisa-tnu.md + fontes-tnu.json | verificar --etapa tnu → 0 |
  | 2 | Consolidação | pesquisa/consolidador-pesquisa.md | relatórios com gate OK | $ID-precedentes-consolidado.md | verificar --etapa consolidado → 0 |
  | 2m | Merge de fontes | — (script) | fontes-*.json | $ID-fontes.json | merge_fontes.py (exit 1 não-fatal se ≥1 fonte válida) |
  | 3 | Finalização | — | tudo | resumo ao usuário | verificar --gate → 0 (ou --etapas <fontes-ok>,consolidado --gate) |

  As âncoras de cada relatório (início/fim/seções) estão CODIFICADAS no verificar_pesquisa.py —
  fonte única; este arquivo não as duplica. O schema do parcial de fontes está na seção
  <saida_fontes> de cada pesquisador — fonte única; o merge_fontes.py valida.
</contratos_dados>

<fases_pipeline>

  <etapa numero="0" nome="Preparação, gate e retomada">
    <acao_orquestrador>
      1. $ARGUMENTS vazio → PARAR: "Informe o tema ou questão jurídica para pesquisa".
      2. Resolver o modo:
         - TRILHO (caminho de pasta de processo existente): se o primeiro token de $ARGUMENTS é um
           diretório (Bash: test -d) → $WORKSPACE = o caminho; $ID = número CNJ no nome da pasta
           (o motor infere; sem CNJ, usa o basename); $TEMA = o restante de $ARGUMENTS — se não
           sobrar tema, PARAR e pedir (a pesquisa precisa de tema).
         - STANDALONE (tema livre): $TEMA = $ARGUMENTS; slug = tema em minúsculas, sem acentos,
           tudo que não for [a-z0-9] vira hífen (hífens colapsados, sem hífen nas pontas);
           $WORKSPACE = data/pesquisa/<slug>; $ID = <slug> (basename). SEM timestamp — mesmo tema
           ⇒ mesmo workspace ⇒ retomada. Bash: mkdir -p "$WORKSPACE" se não existir.
           Ex.: "Pensão por morte homoafetivo" → data/pesquisa/pensao-por-morte-homoafetivo.
      3. Bash: python scripts/verificar_pesquisa.py "$WORKSPACE"
         → a linha "PENDENTES: ..." é o plano de execução. Tudo "(nenhuma)" → pular direto à
         Etapa 3 (a pesquisa já estava completa). Reportar ao usuário o que será PULADO por já
         estar válido.
      4. TodoWrite com as etapas — as já válidas nascem completed:
         [{content: "Etapa 0 - Preparação", status: "completed", activeForm: "Preparando pesquisa"},
          {content: "Etapa 1a - Pesquisa BNP", status: <pendente? "pending" : "completed">, activeForm: "Pesquisando BNP"},
          {content: "Etapa 1b - Pesquisa CJF", ...}, {content: "Etapa 1c - Pesquisa JULIA", ...},
          {content: "Etapa 1d - Pesquisa STJ", ...}, {content: "Etapa 1e - Pesquisa TNU", ...},
          {content: "Etapa 2 - Consolidação e merge de fontes", ...},
          {content: "Etapa 3 - Finalização", status: "pending", activeForm: "Finalizando"}]
    </acao_orquestrador>
    <transicao>Há fonte pendente → Etapa 1. Só "consolidado" pendente → Etapa 2. Nada pendente → Etapa 3.</transicao>
  </etapa>

  <etapa numero="1" nome="Pesquisas em paralelo (sonnet) — SÓ as pendentes" modo="paralelo">
    <retomada>Para cada fonte (bnp, cjf, julia, stj, tnu): se NÃO está em PENDENTES → pular (não despachar). Despachar as pendentes no MESMO turno (até 5 Tasks).</retomada>
    <acao_orquestrador>
      Task (sonnet) para CADA fonte pendente, com o prompt-invólucro (exemplo BNP):
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE PESQUISA. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/pesquisa/pesquisador-bnp.md — sua capacidade; siga fielmente.</passo>
      <passo>Pesquisar via MCP (mcp__bnp-api__buscar_precedentes) o TEMA: $TEMA
             Sintaxe BNP: +termo -termo "frase" (NÃO use E, OU, NAO); priorize Repercussão Geral
             e Repetitivos; transcreva teses EXATAS.</passo>
      <passo>GRAVAR (Write) o relatório COMPLETO em $WORKSPACE/$ID-pesquisa-bnp.md — abrindo com
             "# Pesquisa BNP", fechando com "Pesquisa BNP concluída.", em português COM acentos.</passo>
      <passo>GRAVAR (Write) o parcial $WORKSPACE/fontes-bnp.json no schema da seção saida_fontes do
             seu prompt — trecho_verbatim é cópia EXATA do que o MCP retornou; sem resultados →
             {"fontes": []}.</passo>
      <passo>Responder APENAS: "bnp OK | $ID-pesquisa-bnp.md" — NÃO imprimir o documento.</passo>
      <restricoes>NUNCA inventar precedentes; NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Variações por fonte (mesmo invólucro, trocando agente, arquivos e lembrete de sintaxe):
      - CJF → .claude/agents/pesquisa/pesquisador-cjf.md; $ID-pesquisa-cjf.md; fontes-cjf.json;
        abre "# Pesquisa CJF", fecha "Pesquisa CJF concluída.".
        Sintaxe CJF: E OU NAO ADJ PROX (MAIÚSCULO); pesquise APENAS TRF1, TRF3, TRF4
        (tribunais="TRF1,TRF3,TRF4" — únicas bases vivas do CJF; STF/STJ/TRF5 têm fontes
        próprias); identifique divergências regionais.
      - JULIA → .claude/agents/pesquisa/pesquisador-julia.md; $ID-pesquisa-julia.md; fontes-julia.json;
        abre "# Pesquisa JULIA", fecha "Pesquisa JULIA concluída.".
        Sintaxe JULIA: e ou nao adj prox $ (minúsculo); analise por turma; verifique IRDRs
        vinculantes.
      - STJ → .claude/agents/pesquisa/pesquisador-stj.md; $ID-pesquisa-stj.md; fontes-stj.json;
        abre "# Pesquisa STJ", fecha "Pesquisa STJ concluída.".
        Sintaxe STJ: espaço é E implícito, ou nao "frase" termo* (sem parênteses; caixa/acentos
        ignorados); priorize repetitivos e súmulas; transcreva teses EXATAS.
      - TNU → .claude/agents/pesquisa/pesquisador-tnu.md; $ID-pesquisa-tnu.md; fontes-tnu.json;
        abre "# Pesquisa TNU", fecha "Pesquisa TNU concluída.".
        Sintaxe TNU: e ou nao prox * "frase" (prox SEM número; wildcard em sufixo ou prefixo);
        use somente_precedentes_relevantes para os representativos; foque uniformização/JEFs.
      Aguardar TODAS as Tasks despachadas e validar CADA fonte:
      Bash: python scripts/verificar_pesquisa.py "$WORKSPACE" --etapa bnp   (idem cjf, julia, stj, tnu)
      (exit 1 → contingência etapa_invalida: redespachar SÓ a fonte reprovada com o motivo do gate
      anexado; máx 2 tentativas; na 2ª falha → contingência fonte_indisponivel).
    </acao_orquestrador>
    <transicao>Ao menos 1 fonte com gate 0 → Etapa 2. Todas INDISPONÍVEIS → PARAR.</transicao>
  </etapa>

  <etapa numero="2" nome="Consolidação (sonnet) + merge de fontes (script)">
    <retomada>Se "consolidado" NÃO está em PENDENTES E nenhuma pesquisa foi regenerada nesta execução → pular a Task (o consolidado antigo continua valendo). Se alguma pesquisa foi regenerada agora, o consolidador RODA de novo (o consolidado antigo está desatualizado). O merge de fontes roda SEMPRE (idempotente, sem custo de LLM).</retomada>
    <acao_orquestrador>
      1. Task (sonnet) com o prompt-invólucro:
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE CONSOLIDAÇÃO. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/pesquisa/consolidador-pesquisa.md — sua capacidade; siga fielmente.</passo>
      <passo>Read: [listar aqui APENAS os relatórios com gate OK, ex.:
             $WORKSPACE/$ID-pesquisa-bnp.md, $WORKSPACE/$ID-pesquisa-cjf.md,
             $WORKSPACE/$ID-pesquisa-julia.md, $WORKSPACE/$ID-pesquisa-stj.md,
             $WORKSPACE/$ID-pesquisa-tnu.md — fonte INDISPONÍVEL fica de fora e deve ser
             registrada como ausente no consolidado].</passo>
      <passo>Analisar interseções e divergências (TEMA: $TEMA) e GRAVAR (Write) o relatório
             COMPLETO em $WORKSPACE/$ID-precedentes-consolidado.md — abrindo com
             "# Relatório Consolidado de Precedentes", com a classificação por hierarquia
             vinculante (RG > RR > IRDR > Súmula), fechando com "Consolidação realizada com base
             nas pesquisas disponíveis.", em português COM acentos.</passo>
      <passo>Responder APENAS: "consolidado OK | $ID-precedentes-consolidado.md" — NÃO imprimir o documento.</passo>
      <restricoes>NUNCA inventar precedentes ausentes dos relatórios; NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      2. Validar: Bash: python scripts/verificar_pesquisa.py "$WORKSPACE" --etapa consolidado
         (exit 1 → contingência etapa_invalida; 2ª falha → contingência consolidacao_falha).
      3. Merge de fontes: Bash: python scripts/merge_fontes.py "$WORKSPACE" --id "$ID"
         → produz $ID-fontes.json sem passar conteúdo pelo contexto. Exit 1 = itens rejeitados
         NOMEADOS no stdout; NÃO é fatal se sobrar ≥1 fonte válida — anotar os rejeitados para o
         resumo (contingência fontes_rejeitadas).
    </acao_orquestrador>
    <transicao>Gate consolidado 0 → Etapa 3.</transicao>
  </etapa>

  <etapa numero="3" nome="Finalização">
    <acao_orquestrador>
      1. Gate final:
         - Sem fonte INDISPONÍVEL: Bash: python scripts/verificar_pesquisa.py "$WORKSPACE" --gate
         - Com fonte(s) INDISPONÍVEL(is) após 2 tentativas:
           Bash: python scripts/verificar_pesquisa.py "$WORKSPACE" --etapas <fontes-ok>,consolidado --gate
           (ex.: --etapas bnp,julia,stj,consolidado --gate — TNU indisponível na sessão)
         (exit 1 → algo regrediu; reportar o output e PARAR).
      2. Resumo de 1 tela ao usuário, SEM transcrever conteúdo dos relatórios:
         - Tema e $WORKSPACE
         - Arquivos: $ID-pesquisa-<fonte>.md por fonte (marcando REAPROVEITADO vs gerado agora e
           as fontes INDISPONÍVEIS), $ID-precedentes-consolidado.md (o PRINCIPAL) e $ID-fontes.json
         - Fontes verbatim: nº de itens válidos e itens rejeitados no merge (do stdout do
           merge_fontes.py — ex.: "[FIM] 7 válidas, 1 rejeitada, 0 duplicatas")
    </acao_orquestrador>
  </etapa>

</fases_pipeline>

<resumo_arquitetura>
PIPELINE PESQUISA v3.0 — workspace determinístico + gate por script + retomada + fontes verbatim
│
├── 0 Preparação: $WORKSPACE/$ID/$TEMA + verificar_pesquisa.py → PENDENTES (o plano)
│     standalone: data/pesquisa/<slug-do-tema> (sem timestamp)  |  trilho: pasta do processo
├── 1 Pesquisas em PARALELO (só as pendentes; até 5 Tasks sonnet no mesmo turno)
│   ├── bnp   [Task sonnet] → $ID-pesquisa-bnp.md   + fontes-bnp.json   ─┐ cada uma: pula se
│   ├── cjf   [Task sonnet] → $ID-pesquisa-cjf.md   + fontes-cjf.json    │ válida; grava arquivos;
│   ├── julia [Task sonnet] → $ID-pesquisa-julia.md + fontes-julia.json  │ 1 linha; gate --etapa
│   ├── stj   [Task sonnet] → $ID-pesquisa-stj.md   + fontes-stj.json    │ (MCP desconectado →
│   └── tnu   [Task sonnet] → $ID-pesquisa-tnu.md   + fontes-tnu.json   ─┘  INDISPONÍVEL direto)
├── 2 Consolidação [Task sonnet] → $ID-precedentes-consolidado.md (gate --etapa consolidado)
│     + Merge      [SCRIPT]      → $ID-fontes.json (merge_fontes.py; zero contexto)
└── 3 Finalização: verificar_pesquisa.py --gate (ou --etapas <fontes-ok>,consolidado) + resumo

Princípios: o documento vive no ARQUIVO (nunca na conversa); a validação é do SCRIPT (âncoras com
acentos normalizados — fonte única em verificar_pesquisa.py); PENDENTES é o plano (1ª rodada e
retomada são a mesma operação); fonte que falha 2x vira INDISPONÍVEL e não trava o pipeline;
nenhuma citação sem lastro — o trecho_verbatim é cópia exata do MCP e o merge é determinístico.
</resumo_arquitetura>

<checklist_orquestrador>
- [ ] $WORKSPACE/$ID/$TEMA resolvidos e a varredura da Etapa 0 rodou?
- [ ] Todas as etapas VÁLIDAS foram puladas (nada redespachado)?
- [ ] Pesquisas pendentes despachadas em PARALELO no mesmo turno?
- [ ] Nenhum relatório lido pelo orquestrador (validação só por script)?
- [ ] Subagentes responderam só a linha de status?
- [ ] Consolidador recebeu SÓ os relatórios com gate OK (e re-rodou se alguma pesquisa mudou)?
- [ ] Fonte com MCP desconectado (STJ/TNU) virou INDISPONÍVEL direto ("[AVISO] fonte indisponível", sem redespacho) e entrou no gate degradado?
- [ ] merge_fontes.py rodou e os rejeitados (se houver) foram anotados para o resumo?
- [ ] Gate final (--gate ou --etapas <fontes-ok>,consolidado --gate) retornou 0 antes do resumo?
- [ ] TodoWrite refletiu o reaproveitamento (etapas puladas nascem completed)?
</checklist_orquestrador>
