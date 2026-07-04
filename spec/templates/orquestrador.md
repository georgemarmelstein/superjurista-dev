# Template: Orquestrador (Command) v3.0 - Injeção de Contexto + Gate por Script

> **Filosofia:** Orquestrador fornece contexto ($ARGUMENTS) aos agents modulares.
>
> **Copie para:** `.claude/commands/[nome-pipeline].md`
>
> **O que mudou na v3.0 (o encanamento, não a filosofia):**
> 1. **Saída em disco + status de 1 linha** — o subagente GRAVA o documento (Write) e responde
>    só "etapa OK | arquivo"; NUNCA ecoa o documento inline (L5).
> 2. **Retomada por varredura** — a Etapa 0 roda o gate (`verificar_<sistema>.py`); a linha
>    `PENDENTES:` É o plano; etapa já válida não roda de novo (L13).
> 3. **Validação por script** — âncoras normalizadas (acento/caixa) conferidas por
>    `verificar_<sistema>.py --etapa/--gate`; o orquestrador NUNCA lê o documento para validar (L14).
> 4. **Merge/handoff por script** — conteúdo nunca passa pelo contexto (`merge_<sistema>.py`).
>
> **Andaimes MORTOS (era 200k):** "NUNCA em paralelo" (pipelines de PROCESSOS distintos podem
> rodar em paralelo), "leia em blocos"/chunking defensivo, "/clear entre processos".
> **Filosofia PRESERVADA:** orquestrador cego, injeção de $WORKSPACE, "Passo 1 = Read do agente",
> contratos por tipo, tools mínimas, TodoWrite exclusivo do orquestrador.

---

## Arquitetura de Injeção de Contexto

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ORQUESTRADOR (conhece o contexto)                                          │
│                                                                             │
│  1. Recebe: $ARGUMENTS = "0814624-28.2019.4.05.8100"                        │
│  2. Calcula: WORKSPACE = "data/sentenca/0814624-28.2019.4.05.8100"          │
│  3. Injeta: Passa WORKSPACE para cada subagente                             │
│                                                                             │
│  ┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐ │
│  │    SUBAGENTE 1    │     │    SUBAGENTE 2    │     │    SUBAGENTE N    │ │
│  │  (não sabe path)  │────▶│  (não sabe path)  │────▶│  (não sabe path)  │ │
│  │                   │     │                   │     │                   │ │
│  │  Recebe: WORKSPACE│     │  Recebe: WORKSPACE│     │  Recebe: WORKSPACE│ │
│  │  Lê: agent.md     │     │  Lê: agent.md     │     │  Lê: agent.md     │ │
│  └───────────────────┘     └───────────────────┘     └───────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Princípio:** Agent define CAPACIDADE. Orquestrador injeta CONTEXTO (DISTRIBUIÇÃO DE CONTEXTO VIA PATH).

---

## Template

```markdown
---
description: Pipeline de [nome do pipeline]
argument-hint: [parametro-esperado]
allowed-tools: Read Task Bash TodoWrite
---

<identidade>
  <papel>Coordenador do pipeline de [nome], não executor — despacha, valida por script e retoma</papel>
  <estilo>Metódico, sequencial, validador rigoroso; nada de conteúdo pesado no próprio contexto</estilo>
</identidade>

<proposito>
  <objetivo>Transformar [entrada] em [saída] através de [N] etapas controladas, retomáveis e validadas por script</objetivo>
  <razao>Cada etapa validada de forma determinística; falha no meio não repaga o que já foi feito (retrabalho em opus é o desperdício mais caro)</razao>
  <resultado_final>[Descrição do artefato final]</resultado_final>
</proposito>

<capacidades>
  <tools_orquestrador>
    | Tool | Função | Quando Usar |
    |------|--------|-------------|
    | Bash | Gate/retomada (verificar_<sistema>.py), merge (merge_<sistema>.py), test -f | Etapa 0, validação de todas |
    | Task | Disparar subagentes | Etapas com agente (só as PENDENTES) |
    | TodoWrite | Rastrear progresso | Início e transições de etapa |
    | Read | EXCEÇÃO rara: diagnosticar falha persistente | NUNCA para validar rotina (L14) |
  </tools_orquestrador>

  <tools_subagentes>
    <!--
      PRINCÍPIO DO MÍNIMO PRIVILÉGIO
      ═══════════════════════════════════════════════════════════════════════
      Conceda a cada subagente APENAS as tools necessárias para sua tarefa.
      Menos tools = menos superfície de erro = execução mais focada.
    -->

    <tools_disponiveis>
      | Tool | Função | Quando Usar |
      |------|--------|-------------|
      | Read | Ler arquivos | SEMPRE - ler prompt do agent e entrada |
      | Write | Salvar arquivos | SEMPRE - salvar resultado |
      | Glob | Buscar arquivos por padrão | Quando precisa localizar arquivos (ex: "*.pdf") |
      | Grep | Buscar conteúdo em arquivos | Quando precisa encontrar texto específico |
      | Bash | Executar comandos | Quando precisa de operações de sistema |
      | WebSearch | Pesquisar na web | Quando precisa de informação externa atualizada |
      | WebFetch | Buscar URL específica | Quando precisa ler conteúdo de URL conhecida |
      | MCP tools | Ferramentas especializadas | Quando o domínio exige (ex: `mcp__bnp-api__*`) |
    </tools_disponiveis>

    <tools_proibidas_subagentes>
      | Tool | Razão da Proibição |
      |------|-------------------|
      | TodoWrite | Exclusivo do orquestrador - causa race conditions |
      | Task | Subagentes não disparam outros subagentes |
      | AskUserQuestion | Apenas orquestrador interage com usuário |
    </tools_proibidas_subagentes>

    <orientacao>
      Para cada etapa, defina em `<config><tools>` APENAS as necessárias:
      - Etapa de leitura/escrita simples: `Read Write`
      - Etapa que precisa buscar arquivos: `Read Write Glob`
      - Etapa de pesquisa jurídica: `Read Write mcp__bnp-api__* mcp__cjf-jurisprudencia__*`
    </orientacao>
  </tools_subagentes>

  <regras_uso>
    - RETOMADA (L13): a varredura da Etapa 0 lista PENDENTES — só as pendentes rodam. Primeira rodada e retomada pós-falha são a MESMA operação: rodar o que a varredura listar.
    - CONDUZIR POR CAMINHO: o orquestrador passa paths; o subagente lê a entrada (Read) e GRAVA o documento no arquivo (Write). O documento NUNCA volta inline na resposta (L5).
    - RESPOSTA DE UMA LINHA: cada subagente responde apenas "<etapa> OK | <arquivo>" — quem confere o conteúdo é o script, não o orquestrador lendo.
    - VALIDAÇÃO POR SCRIPT (L14): nunca validar lendo o documento; sempre `python scripts/verificar_<sistema>.py "$WORKSPACE" --etapa <nome>` (exit 0 = válida).
    - Subagentes LEEM o próprio prompt via Read (não recebem cópia); o orquestrador não copia a capacidade deles.
    - Cada subagente tem contexto ISOLADO (não vê conversa anterior).
    - Etapas de UM pipeline são sequenciais ENTRE SI; pipelines de PROCESSOS distintos são independentes e podem rodar em paralelo (não existe "um por vez" entre processos).
  </regras_uso>

  <scripts_deterministicos>
    | Script | Função |
    |--------|--------|
    | scripts/verificar_<sistema>.py | Gate + retomada: varredura (PENDENTES), --etapa (exit-coded), --gate (final) |
    | scripts/merge_<sistema>.py | Merge por script (quando há concatenação pura): sem LLM, sem contexto |
  </scripts_deterministicos>
</capacidades>

<restricoes>
  <orquestrador>
    - As etapas de UM pipeline são sequenciais ENTRE SI (cada uma consome a anterior); pipelines de PROCESSOS distintos são independentes e PODEM rodar em paralelo (um Task de pipeline por processo)
    - NUNCA ler o documento gerado para validar — validação é do script (L14); Read é exceção de diagnóstico, jamais rotina
    - NUNCA redespachar etapa que o gate deu como válida (o trabalho já foi pago — L13)
    - NUNCA copiar/resumir prompts — instrua subagente a LER
    - NUNCA prosseguir com etapa cuja anterior está pendente/inválida
    - NUNCA tentar mais de 2 vezes a mesma etapa — na 2ª falha, PARAR e reportar o output do gate
    - NUNCA criar prompts inline > 50 linhas OU não estruturados
    - NUNCA criar prompt sem "Passo 1: Read: .claude/agents/[agent].md"
    - NUNCA fazer merge no próprio contexto — é o merge_<sistema>.py
    - SEMPRE estruturar prompt: cabeçalho ═══ + passos numerados + restrições
  </orquestrador>

  <subagentes>
    - NUNCA inventar dados não presentes na entrada
    - NUNCA remover acentos do português
    - NUNCA usar markdown no corpo (asteriscos, hashtags)
    - NUNCA imprimir o documento na resposta — o documento vai no ARQUIVO (Write); responder só a linha de status (L5)
    - NUNCA usar TodoWrite (apenas orquestrador gerencia progresso)
  </subagentes>
</restricoes>

<contingencias>
  <etapa_invalida>
    Gate acusa [AUSENTE]/[INVALIDA] após o despacho → redespachar a MESMA etapa com o
    motivo do gate anexado ao prompt (máx 2 tentativas; depois PARAR e reportar o output
    do gate ao usuário).
  </etapa_invalida>

  <falha_de_entrada>
    merge_<sistema>.py (ou o handoff) acusa entrada inválida → o defeito é da etapa
    anterior, não do merge; voltar à etapa apontada.
  </falha_de_entrada>

  <limite_tentativas>
    | Escopo | Limite |
    |--------|--------|
    | Por etapa | 2 tentativas |
    | Total no pipeline | na 2ª falha de uma etapa, o pipeline PARA com o diagnóstico do gate (não silencia) |
  </limite_tentativas>
</contingencias>

<contratos_dados>
  | # | Etapa | Agente/Script | Entrada | Saída | Validação |
  |---|-------|---------------|---------|-------|-----------|
  | 0 | Preparação | — | $ARGUMENTS | $WORKSPACE + PENDENTES | gate varredura (o plano) |
  | 1 | [Nome] | .claude/agents/[cat]/[agent].md | $WORKSPACE/[input] | $WORKSPACE/$NUMERO-[out].md | verificar --etapa <n> → 0 |
  | 2 | [Nome] | .claude/agents/[cat]/[agent].md | [input] | [output] | verificar --etapa <n> → 0 |
  | M | Merge | — (script) | [saídas parciais] | [artefato unificado] | merge_<sistema>.py → 0 |
  | N | Finalização | — | tudo | resumo ao usuário | verificar --gate → 0 |

  As âncoras de início/fim/seções de cada etapa vivem CODIFICADAS no verificar_<sistema>.py
  (fonte única) — este arquivo não as duplica.
</contratos_dados>

<rastreamento_progresso>
  <!--
    CRÍTICO: TodoWrite é EXCLUSIVO do orquestrador.
    Subagentes NÃO devem manipular - causa race conditions.
  -->

  <regra_ouro>
    | Quem | Pode usar TodoWrite? |
    |------|---------------------|
    | Orquestrador (contexto principal) | SIM - gerencia todo o progresso |
    | Subagentes (Task tool) | NÃO - apenas retornam resultado |
  </regra_ouro>

  <quando_atualizar>
    | Momento | Ação |
    |---------|------|
    | Início do pipeline (Etapa 0) | Criar TodoWrite com TODAS as etapas — as já válidas no gate NASCEM `completed` (retomada) |
    | Antes de disparar etapa PENDENTE | Marcar etapa como in_progress |
    | Após validar output pelo gate (--etapa → 0) | Marcar etapa como completed |
    | Se falhar 2x | PARAR e reportar o output do gate |
  </quando_atualizar>

  <formato_todowrite>
    ```javascript
    // As já válidas na varredura da Etapa 0 nascem "completed" (retomada — L13)
    TodoWrite([
      {content: "Etapa 0 - Preparação", status: "completed", activeForm: "Preparando"},
      {content: "Etapa 1 - [Nome]", status: <pendente? "pending" : "completed">, activeForm: "[Verbo]ando"},
      {content: "Etapa 2 - [Nome]", status: <pendente? "pending" : "completed">, activeForm: "[Verbo]ando"},
      {content: "Etapa N - Finalização", status: "pending", activeForm: "Finalizando"},
    ])
    ```
  </formato_todowrite>

  <campos_obrigatorios>
    | Campo | Tipo | Descrição |
    |-------|------|-----------|
    | `content` | string | Descrição da etapa (imperativo) |
    | `status` | enum | pending, in_progress, completed |
    | `activeForm` | string | Gerúndio para exibição durante execução |
  </campos_obrigatorios>
</rastreamento_progresso>

<sinalizadores_formato>
  <!--
    As âncoras de início/fim/seções de cada etapa vivem CODIFICADAS no verificar_<sistema>.py
    (fonte única). O orquestrador NÃO as confere lendo o documento — roda o gate por script,
    que normaliza acento/caixa. Esta tabela apenas espelha, para leitura humana, o que o gate exige.
  -->
  | Etapa | Início (âncora do gate) | Fim (âncora do gate) | Conferência |
  |-------|-------------------------|----------------------|-------------|
  | 1 | "[INICIO_1]" | "[FIM_1]" | verificar --etapa <n> → 0 |
  | 2 | "[INICIO_2]" | "[FIM_2]" | verificar --etapa <n> → 0 |
  | 3 | "[INICIO_3]" | "[FIM_3]" | verificar --etapa <n> → 0 |
</sinalizadores_formato>

<sufixos_correcao>
  <sufixo_gate>
    [FALHA NO GATE. O documento gravado não passou em verificar_<sistema>.py --etapa <n>:
    <motivo do gate>. Corrija o ARQUIVO (abra com o marcador de início, feche com o de fim,
    inclua as seções obrigatórias, use acentos) e REGRAVE — não ecoe o conteúdo.]
  </sufixo_gate>

  <sufixo_eco>
    [FALHA DE CONTRATO. Você imprimiu o documento na resposta. GRAVE-o com Write no caminho
    indicado e responda APENAS uma linha de status ("<etapa> OK | <arquivo>"); não ecoe o conteúdo (L5).]
  </sufixo_eco>

  <sufixo_acentos>
    [FALHA DE ACENTOS. Use acentos do português: é, á, ã, ç, ô, ê, í, ú.
    Documento jurídico brasileiro EXIGE acentuação correta.]
  </sufixo_acentos>
</sufixos_correcao>

<configuracao>
  <!--
    PADRÃO DE INJEÇÃO DE CONTEXTO
    ═══════════════════════════════════════════════════════════════════════
    Agents são modulares e NÃO conhecem caminhos específicos.
    Orquestrador INJETA contexto via variáveis calculadas na Etapa 0.
  -->

  <caminho_agents>.claude/agents/</caminho_agents>
  <!-- Agents ficam na raiz, sem subpasta por pipeline (são reutilizáveis) -->

  <variaveis_injetadas>
    | Variável | Origem | Uso |
    |----------|--------|-----|
    | $ARGUMENTS | Usuário | Identificador do processo (ex: "0814624-28.2019.4.05.8100") |
    | $NUMERO | Calculada | Número do processo para prefixo de arquivos |
    | $WORKSPACE | Calculada | Caminho da pasta do processo (ex: "data/sentenca/0814624-28.2019.4.05.8100") |

    O filesystem É o manifesto — não há $MANIFEST/_manifest.md. O que já existe e passa no
    gate É o estado do pipeline; a varredura da Etapa 0 lê esse estado (PENDENTES).
  </variaveis_injetadas>

  <convencao_nomenclatura>
    <!--
      PADRÃO: [NUMERO]-tipo.md
      Facilita busca por arquivos do mesmo processo.
    -->

    | Tipo de Arquivo | Padrão | Exemplo |
    |-----------------|--------|---------|
    | Entrada | `$NUMERO.txt` | `0814624-28.2019.4.05.8100.txt` |
    | Relatório | `$NUMERO-relatorio.md` | `0814624-28.2019.4.05.8100-relatorio.md` |
    | Linha do tempo | `$NUMERO-linha-tempo.md` | `0814624-28.2019.4.05.8100-linha-tempo.md` |
    | Análise | `$NUMERO-analise.md` | `0814624-28.2019.4.05.8100-analise.md` |
    | Fundamentação | `$NUMERO-fundamentacao.md` | `0814624-28.2019.4.05.8100-fundamentacao.md` |
    | Sentença | `$NUMERO-sentenca.md` | `0814624-28.2019.4.05.8100-sentenca.md` |
    | Pesquisa BNP | `$NUMERO-bnp.md` | Em `pesquisa/` |
    | Revisão | `$NUMERO-advogado-diabo.md` | Em `revisao/` |
  </convencao_nomenclatura>

  <agents_utilizados>
    | Agent | Capacidade | Arquivo |
    |-------|------------|---------|
    | [nome-1] | [O que sabe fazer] | .claude/agents/[nome-1].md |
    | [nome-2] | [O que sabe fazer] | .claude/agents/[nome-2].md |
    | [nome-3] | [O que sabe fazer] | .claude/agents/[nome-3].md |
  </agents_utilizados>
</configuracao>

<etapas_pipeline>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- ETAPA 0: PREPARAÇÃO                                             -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <etapa numero="0" nome="Preparação, gate e retomada">
    <!--
      ETAPA CRÍTICA: Calcula variáveis, RODA O GATE (varredura → PENDENTES é o plano) e
      cria o TodoWrite. Subagentes NÃO conhecem $ARGUMENTS - só recebem caminhos prontos.
    -->

    <acao_orquestrador>
      1. **Receber e validar argumento:**
         ```
         $ARGUMENTS = [valor recebido do usuário]
         Se vazio ou inválido → PARAR e pedir ao usuário
         ```

      2. **Calcular variáveis de contexto:**
         ```
         $NUMERO    = $ARGUMENTS (ou extrair o padrão CNJ do nome da pasta)
         $WORKSPACE = "data/<tipo>/$NUMERO"   (ex.: data/sentenca/0814624-28.2019.4.05.8100)
         ```
         (O filesystem é o manifesto — não há $MANIFEST/_manifest.md.)

      3. **Verificar se a ENTRADA do pipeline existe:**
         ```bash
         test -f "$WORKSPACE/[arquivo-de-entrada]"   # ex.: processo.txt
         # Se faltar → PARAR (a entrada do pipeline não existe).
         ```

      4. **Rodar o GATE — varredura (retomada):**
         ```bash
         python scripts/verificar_<sistema>.py "$WORKSPACE"
         ```
         → A linha `PENDENTES: ...` É o plano de execução. Tudo "(nenhuma)" → pular direto à
         Finalização (o pipeline já estava completo). Reportar ao usuário o que será PULADO
         por já estar válido. Primeira rodada e retomada pós-falha são a MESMA operação.

      5. **Criar TodoWrite com todas as etapas** — as já VÁLIDAS na varredura nascem `completed`:
         ```javascript
         TodoWrite([
           {content: "Etapa 0 - Preparação", status: "completed", activeForm: "Preparando"},
           {content: "Etapa 1 - [Nome]", status: <pendente? "pending" : "completed">, activeForm: "[Verbo]ando"},
           {content: "Etapa 2 - [Nome]", status: <pendente? "pending" : "completed">, activeForm: "[Verbo]ando"},
           {content: "Etapa N - Finalização", status: "pending", activeForm: "Finalizando"},
         ])
         ```
    </acao_orquestrador>

    <variaveis_calculadas>
      | Variável | Valor Exemplo | Disponível para |
      |----------|---------------|-----------------|
      | $ARGUMENTS | "0814624-28.2019.4.05.8100" | Apenas Etapa 0 |
      | $NUMERO | "0814624-28.2019.4.05.8100" | Todas as etapas |
      | $WORKSPACE | "data/sentenca/0814624-28.2019.4.05.8100" | Todas as etapas |
    </variaveis_calculadas>

    <criterio_sucesso>
      - [ ] $ARGUMENTS válido; $WORKSPACE e $NUMERO calculados
      - [ ] Arquivo de entrada existe (test -f)
      - [ ] Gate rodou; PENDENTES conhecidas (o plano)
      - [ ] TodoWrite criado — etapas já válidas nascem completed
    </criterio_sucesso>

    <transicao>
      Ir para a PRIMEIRA etapa PENDENTE (na ordem). Se PENDENTES = (nenhuma) → Finalização.
      Se FALHAR → PARAR e informar usuário.
    </transicao>
  </etapa>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- ETAPA 1: [NOME DA ETAPA]                                        -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <etapa numero="1" nome="[Nome da Etapa]">
    <config>
      <modelo>sonnet</modelo>
      <tools>Read Write</tools>
      <agent>.claude/agents/[nome-agent].md</agent>
      <entrada>$WORKSPACE/[arquivo-entrada]</entrada>
      <saida>$WORKSPACE/$NUMERO-[saida].md</saida>
      <slug>[slug-etapa]</slug>
    </config>

    <retomada>Se "[slug-etapa]" NÃO está em PENDENTES (varredura da Etapa 0) → PULAR (não despachar; o trabalho já foi pago).</retomada>

    <acao_orquestrador>
      1. **Montar prompt-invólucro com variáveis já substituídas** (ver abaixo)
      2. Disparar Task tool com o prompt montado (só se a etapa está em PENDENTES)
      3. Aguardar a linha de status do subagente
      4. **Validar por SCRIPT:** `python scripts/verificar_<sistema>.py "$WORKSPACE" --etapa [slug-etapa]` (exit 0 = válida)
      5. Atualizar TodoWrite (etapa atual → completed)
    </acao_orquestrador>

    <!--
      PADRÃO DE INJEÇÃO
      ═══════════════════════════════════════════════════════════════════════
      O orquestrador SUBSTITUI as variáveis $WORKSPACE antes de enviar.

      Exemplo: Se $WORKSPACE = "data/sentenca/0814624-28.2019.4.05.8100"
      O subagente recebe: "Read: data/sentenca/0814624-28.2019.4.05.8100/relatorio.md"
      O subagente NÃO recebe: "Read: $WORKSPACE/relatorio.md"
    -->

    <prompt_subagente tipo="[FUNÇÃO]">

      <cabecalho>
        ═══════════════════════════════════════════════════════════════════════
        VOCÊ É UM SUBAGENTE DE [FUNÇÃO]. EXECUTE DIRETAMENTE.
        ═══════════════════════════════════════════════════════════════════════
      </cabecalho>

      <identidade>
        <papel>Você é um [papel específico].</papel>
      </identidade>

      <proposito>
        <objetivo>[Objetivo desta etapa].</objetivo>
      </proposito>

      <execucao>
        <passo numero="1" nome="Ler instruções do agent">
          Read: .claude/agents/[nome-agent].md
          → Este arquivo define sua CAPACIDADE. Siga fielmente.
        </passo>

        <passo numero="2" nome="Ler entrada">
          Read: $WORKSPACE/[arquivo-entrada]
          → O orquestrador já substituiu $WORKSPACE pelo caminho real. Leia a entrada por caminho.
        </passo>

        <passo numero="3" nome="Executar tarefa">
          → Aplique sua capacidade à entrada lida
          → Use português COM ACENTOS
        </passo>

        <passo numero="4" nome="Gravar o documento">
          Write: $WORKSPACE/$NUMERO-[saida].md
          → GRAVE o documento COMPLETO, com os marcadores de início/fim e as seções obrigatórias.
          → O orquestrador já substituiu $WORKSPACE pelo caminho real.
        </passo>

        <passo numero="5" nome="Responder status">
          → Responder APENAS: "[slug-etapa] OK | $NUMERO-[saida].md" — NÃO imprimir o documento.
        </passo>
      </execucao>

      <restricoes>
        - GRAVAR o documento com "[SINALIZADOR_INICIO]" e "[SINALIZADOR_FIM]" (âncoras do gate)
        - NÃO imprimir o documento na resposta — responder só a linha de status (L5)
        - SEM asteriscos, SEM hashtags
        - NUNCA usar TodoWrite (apenas orquestrador gerencia)
      </restricoes>

    </prompt_subagente>

    <validacao>
      Bash: `python scripts/verificar_<sistema>.py "$WORKSPACE" --etapa [slug-etapa]`
      | Exit-code | Significado | Ação |
      |-----------|-------------|------|
      | 0 | [OK] etapa válida | Prosseguir |
      | 1 | [AUSENTE]/[INVALIDA] | REGENERAR com sufixo_gate (o motivo do gate anexado) — máx 2x |
      O orquestrador NÃO lê o documento para validar (L14).
    </validacao>

    <criterio_sucesso>
      - [ ] Subagente respondeu só a linha de status (documento NÃO ecoado)
      - [ ] Gate --etapa [slug-etapa] retornou 0
    </criterio_sucesso>

    <transicao>
      Se gate 0 → próxima etapa PENDENTE
      Se FALHAR 2x → PARAR e reportar o output do gate
    </transicao>
  </etapa>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- ETAPA M: MERGE (script, sem LLM) — quando há concatenação pura    -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <etapa numero="M" nome="Merge (script, sem LLM)">
    <!--
      Só quando o artefato final é concatenação/validação de saídas parciais (ex.:
      relatório + fundamentação → sentença). Merge PURO é determinístico: um SCRIPT
      concatena/valida sem passar o conteúdo pelo contexto do orquestrador.
      Quando houver JUÍZO EDITORIAL (não só concatenar), use um subagente de merge.
    -->
    <retomada>Se "[slug-merge]" NÃO está em PENDENTES E nenhuma entrada do merge rodou nesta execução → PULAR. Se uma entrada foi regenerada agora, o merge RODA de novo (o artefato antigo está desatualizado).</retomada>
    <acao_orquestrador>
      Bash: `python scripts/merge_<sistema>.py "$WORKSPACE"`
      → concatena, grava e valida o artefato unificado sem passar conteúdo pelo contexto.
      Exit 1 com "entrada inválida" → voltar à etapa apontada (contingência falha_de_entrada).
    </acao_orquestrador>
    <transicao>Exit 0 → Finalização.</transicao>
  </etapa>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- ETAPA N: FINALIZAÇÃO                                            -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <etapa numero="N" nome="Finalização">
    <acao_orquestrador>
      1. **Gate final:** `python scripts/verificar_<sistema>.py "$WORKSPACE" --gate`
         (exit 1 → algo regrediu; reportar o output e PARAR).
      2. Exibir ao usuário:

      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      PIPELINE [NOME] - Concluído
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

      Entrada: [entrada original]

      Arquivos (marcar REAPROVEITADO da execução anterior vs gerado agora):
        ✓ [arquivo-1] (ETAPA 1)
        ✓ [arquivo-2] (ETAPA 2)
        ✓ [arquivo-final] (ETAPA M — merge)

      Localização: [caminho completo]

      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    </acao_orquestrador>
  </etapa>

</etapas_pipeline>

<gate_do_pipeline>
  <!--
    Todo pipeline gerado acompanha scripts/verificar_<sistema>.py, que importa o motor
    genérico scripts/verificar_pipeline.py e declara só a tabela ETAPAS (âncoras). É esse
    gate que faz a retomada (varredura → PENDENTES), a validação (--etapa) e o portão final (--gate).
  -->
  ```python
  import os, sys
  sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
  from verificar_pipeline import rodar_cli   # motor genérico (scripts/verificar_pipeline.py)

  ETAPAS = {
      # etapa: (sufixo_do_arquivo, inicio, fim, contem[], minimo_chars)
      "[slug-etapa-1]": ("-[slug1].md", "[âncora de início]", "[âncora de fim]",
                         ["[seção obrigatória]"], 500),
      # `fim` pode ser tupla p/ fim alternativo: ("juiz federal", "juíza federal", ...)
  }

  if __name__ == "__main__":
      rodar_cli(ETAPAS, titulo="<nome-sistema>")
  ```

  **Calibragem das âncoras (crítico):** as âncoras de `ETAPAS` DEVEM casar com os
  `<sinalizadores>` reais dos agentes que geram cada arquivo. Havendo artefato real em
  `data/`, confira `head`/`tail` dele e ajuste antes de fixar. O motor normaliza acento/caixa
  dos dois lados, então escreva as âncoras com acentos naturais.
</gate_do_pipeline>

<resumo_arquitetura>
PIPELINE [NOME] v3.0 — por caminho + gate determinístico + retomada
│
├── ETAPA 0: Preparação, gate e retomada
│   ├── Recebe: $ARGUMENTS do usuário
│   ├── Calcula: $WORKSPACE = "data/<tipo>/$NUMERO"
│   ├── test -f entrada; roda verificar_<sistema>.py → PENDENTES (o plano)
│   └── TodoWrite: etapas já válidas nascem completed
│
├── ETAPA 1: [Nome]  [Task] ─┐
├── ETAPA 2: [Nome]  [Task]  │ cada uma: PULA se válida (retomada);
├── ETAPA 3: [Nome]  [Task] ─┘ GRAVA arquivo; responde 1 linha; gate --etapa valida
│
├── ETAPA M: Merge  [SCRIPT]  → merge_<sistema>.py (zero contexto)  (quando aplicável)
│
└── ETAPA N: Finalização: verificar_<sistema>.py --gate + resumo (REAPROVEITADO vs gerado)

Princípios v3.0: o documento vive no ARQUIVO (nunca na conversa — L5); a validação é do
SCRIPT (âncoras com acento/caixa normalizados — fonte única em verificar_<sistema>.py — L14);
PENDENTES é o plano (1ª rodada e retomada são a mesma operação — L13). Vários processos =
pipelines independentes em paralelo.

FLUXO DE DADOS:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   $ARGUMENTS │────▶│  ORQUESTRADOR│────▶│  SUBAGENTES  │
│  (usuário)   │     │  (calcula    │     │  (recebem    │
│              │     │   $WORKSPACE, │     │   caminhos;  │
│              │     │   roda gate) │     │   gravam)    │
└──────────────┘     └──────────────┘     └──────────────┘
</resumo_arquitetura>

<checklist_orquestrador>
Antes de iniciar, verificar:

**Arquitetura:**
- [ ] Identidade: Sou coordenador, não executor — despacho, valido por script e retomo
- [ ] Propósito: Transformar [entrada] em [saída], retomável e validado por script
- [ ] Capacidades: Bash (gate/merge), Task, TodoWrite; Read só como exceção de diagnóstico

**Injeção de Contexto:**
- [ ] $ARGUMENTS recebido na Etapa 0; $WORKSPACE = "data/<tipo>/$NUMERO"?
- [ ] Subagentes recebem caminhos PRONTOS, não variáveis?
- [ ] Agents são modulares (sem caminhos hardcoded)?

**Retomada e Validação (v3.0):**
- [ ] Etapa 0 roda o gate → PENDENTES é o plano; etapas válidas nascem completed?
- [ ] Cada etapa tem cláusula <retomada> (pula se não está em PENDENTES)?
- [ ] Validação por SCRIPT (verificar_<sistema>.py --etapa), nunca lendo o documento (L14)?
- [ ] Subagente GRAVA o documento e responde só 1 linha; nada ecoado inline (L5)?
- [ ] Merge puro por script (merge_<sistema>.py); Finalização com --gate?
- [ ] Circuit breaker: máx 2 tentativas por etapa, depois PARAR com o output do gate?

**Rastreamento:**
- [ ] TodoWrite criado na Etapa 0 com todas as etapas (válidas já completed)?
- [ ] Atualizado a cada transição; subagentes NUNCA usam TodoWrite?
</checklist_orquestrador>
```

---

## Guia de Preenchimento

### YAML Frontmatter

| Campo | Obrigatório | Descrição |
|-------|-------------|-----------|
| `description` | Sim | Uma linha descrevendo o pipeline |
| `argument-hint` | Sim | Parâmetro esperado (ex: numero-processo) |
| `allowed-tools` | Sim | Sempre: `Read Task Bash TodoWrite` (sem vírgulas) |

### Tags XML Obrigatórias

| Tag | Descrição |
|-----|-----------|
| `<identidade>` | Define papel de coordenador |
| `<proposito>` | Objetivo do pipeline |
| `<capacidades>` | Tools e regras de uso |
| `<restricoes>` | O que NÃO pode fazer |
| `<contingencias>` | Tratamento de erros |
| `<contratos_dados>` | Tabela entrada/saída (com validação por gate) |
| `<rastreamento_progresso>` | Padrão TodoWrite para rastrear etapas (válidas nascem completed) |
| `<sinalizadores_formato>` | Espelha as âncoras do gate (fonte única no verificar_<sistema>.py) |
| `<sufixos_correcao>` | Mensagens para retry (sufixo_gate, sufixo_eco) |
| `<configuracao>` | Variáveis injetadas e agents utilizados |
| `<etapas_pipeline>` | Definição de cada etapa (com <retomada>) |
| `<gate_do_pipeline>` | Esqueleto do verificar_<sistema>.py (importa o motor, declara ETAPAS) |
| `<resumo_arquitetura>` | Visão geral do fluxo com injeção de contexto + gate/retomada |
| `<checklist_orquestrador>` | Verificação pré-execução |

### Subtags de `<etapa>`

| Tag | Descrição |
|-----|-----------|
| `<config>` | Modelo, tools, agent, entrada, saída e `<slug>` (com $WORKSPACE) |
| `<retomada>` | Pula a etapa se o slug NÃO está em PENDENTES (L13) |
| `<acao_orquestrador>` | O que o orquestrador faz |
| `<prompt_subagente>` | Prompt com variáveis já substituídas (grava + responde 1 linha) |
| `<validacao>` | Bash: verificar_<sistema>.py --etapa (exit-coded), nunca por leitura |
| `<criterio_sucesso>` | Checklist de conclusão |
| `<transicao>` | Próxima etapa PENDENTE ou condição de parada |

### Diferença v1 → v2

| Aspecto | v1 (Acoplado) | v2 (Injeção de Contexto) |
|---------|---------------|--------------------------|
| Caminhos | Hardcoded no prompt | $WORKSPACE injetado |
| Etapa 0 | Extrai variáveis | Calcula $WORKSPACE |
| Agents | Por pipeline | Modulares (reutilizáveis) |
| Subagentes | Sabem caminhos | Recebem caminhos prontos |

### Estrutura Obrigatória de Prompt Inline

Todo prompt inline DEVE seguir esta estrutura (< 50 linhas E estruturado):

```
═══════════════════════════════════════════════════════════════════════
VOCÊ É UM SUBAGENTE DE [FUNÇÃO]. EXECUTE DIRETAMENTE.
═══════════════════════════════════════════════════════════════════════

<passo numero="1" nome="Ler instruções">
  Read: .claude/agents/[nome-agent].md         ← SEMPRE primeiro passo
</passo>

<passo numero="2" nome="Ler entrada">
  Read: $WORKSPACE/[arquivo-entrada]           ← Caminho já substituído; leia por caminho
</passo>

<passo numero="3" nome="Executar tarefa">
  → Instruções específicas
  → Use português COM ACENTOS
</passo>

<passo numero="4" nome="Gravar o documento">
  Write: $WORKSPACE/$NUMERO-[saida].md         ← GRAVA o documento completo, com marcadores
</passo>

<passo numero="5" nome="Responder status">
  → Responder APENAS: "[slug-etapa] OK | $NUMERO-[saida].md" — NÃO imprimir o documento (L5)
</passo>

<restricoes>
  - GRAVAR com "[SINALIZADOR_INICIO]" e "[SINALIZADOR_FIM]" (âncoras do gate)
  - NÃO imprimir o documento na resposta — responder só a linha de status
  - SEM asteriscos, SEM hashtags
</restricoes>
```

**Critérios de estrutura correta:**
| # | Critério | Obrigatório |
|---|----------|-------------|
| 1 | Cabeçalho com ═══ e "EXECUTE DIRETAMENTE" | Sim |
| 2 | Passo 1 = Read: .claude/agents/[agent].md | Sim |
| 3 | Passos numerados com `<passo numero="N">` | Sim |
| 4 | Passo de saída GRAVA (Write) o documento com marcadores | Sim |
| 5 | Passo final responde 1 linha ("<slug> OK | <arquivo>") — NÃO imprime o documento (L5) | Sim |
| 6 | Seção `<restricoes>` com sinalizadores e "NÃO imprimir inline" | Sim |
| 7 | Tamanho < 50 linhas | Sim |

### Checklist de Validação

```
YAML e Estrutura:
[ ] YAML frontmatter completo (allowed-tools sem vírgulas)?
[ ] <identidade> define papel de coordenador?
[ ] <proposito> tem objetivo, razão e resultado final?
[ ] <capacidades> inclui TodoWrite na tabela do orquestrador?

Injeção de Contexto:
[ ] <configuracao> define <variaveis_injetadas>?
[ ] <configuracao> lista agents reutilizáveis (sem subpasta)?
[ ] Etapa 0 calcula $WORKSPACE a partir de $ARGUMENTS?
[ ] Prompts usam $WORKSPACE (substituído antes de enviar)?
[ ] Agents não têm caminhos hardcoded?

Estrutura de Prompts Inline:
[ ] Prompts inline < 50 linhas E estruturados corretamente?
[ ] Cabeçalho com ═══ e "EXECUTE DIRETAMENTE"?
[ ] Passo 1 SEMPRE é "Read: .claude/agents/[agent].md"?
[ ] Passos numerados com <passo numero="N">?
[ ] Passo de saída GRAVA o documento e passo final responde 1 linha (não ecoa — L5)?
[ ] Seção <restricoes> com sinalizadores e "NÃO imprimir inline"?

Retomada e Validação (v3.0):
[ ] Etapa 0 roda o gate (verificar_<sistema>.py) → PENDENTES é o plano?
[ ] Cada etapa tem cláusula <retomada> (pula se não está em PENDENTES — L13)?
[ ] Validação por SCRIPT (--etapa/--gate), nunca por leitura do documento (L14)?
[ ] <gate_do_pipeline> com o esqueleto do verificar_<sistema>.py?
[ ] Merge puro por script (merge_<sistema>.py); Finalização com --gate?
[ ] <restricoes> proíbe subagentes de usar TodoWrite e de ecoar o documento?
[ ] <contingencias> trata etapa_invalida e falha_de_entrada (circuit breaker 2x)?
[ ] <contratos_dados> mapeia todas as etapas com validação por gate?
[ ] <sufixos_correcao> prontos (sufixo_gate, sufixo_eco)?

Rastreamento:
[ ] Etapa 0 cria TodoWrite (etapas já válidas nascem completed)?
[ ] Cada transição atualiza TodoWrite?
[ ] <resumo_arquitetura> mostra fluxo de injeção + gate/retomada?
```
