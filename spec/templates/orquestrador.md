# Template: Orquestrador (Command) v2.1 - Injeção de Contexto

> **Filosofia:** Orquestrador fornece contexto ($ARGUMENTS) aos agents modulares.
>
> **Copie para:** `.claude/commands/[nome-pipeline].md`

---

## Arquitetura de Injeção de Contexto

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ORQUESTRADOR (conhece o contexto)                                          │
│                                                                             │
│  1. Recebe: $ARGUMENTS = "processo-12345"                                   │
│  2. Calcula: WORKSPACE = "workspace/processo-12345"                         │
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
  <papel>Coordenador do pipeline de [nome], não executor</papel>
  <estilo>Metódico, sequencial, validador rigoroso</estilo>
</identidade>

<proposito>
  <objetivo>Transformar [entrada] em [saída] através de [N] etapas controladas</objetivo>
  <razao>[Justificativa do pipeline]</razao>
  <resultado_final>[Descrição do artefato final]</resultado_final>
</proposito>

<capacidades>
  <tools_orquestrador>
    | Tool | Função | Quando Usar |
    |------|--------|-------------|
    | Task | Disparar subagentes | Cada etapa do pipeline |
    | Read | Verificar arquivos | Validação pré/pós etapa |
    | Bash | Operações de sistema | Copiar, mover, criar pastas |
    | TodoWrite | Rastrear progresso | Início e transições de etapa |
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
    - Subagentes LEEM prompts diretamente (não recebem cópia)
    - Orquestrador NÃO executa tarefas dos subagentes
    - Orquestrador NÃO lê o prompt: instrui subagente a ler via Read
    - Cada subagente tem contexto ISOLADO (não vê conversa anterior)
  </regras_uso>
</capacidades>

<restricoes>
  <orquestrador>
    - NUNCA executar etapas em paralelo (exceto quando explícito)
    - NUNCA copiar/resumir prompts — instrua subagente a LER
    - NUNCA prosseguir sem validar etapa anterior
    - NUNCA ignorar sinalizadores de formato ausentes
    - NUNCA tentar mais de 2 vezes a mesma etapa
    - NUNCA criar prompts inline > 50 linhas OU não estruturados
    - NUNCA criar prompt sem "Passo 1: Read: .claude/agents/[agent].md"
    - SEMPRE estruturar prompt: cabeçalho ═══ + passos numerados + restrições
  </orquestrador>

  <subagentes>
    - NUNCA inventar dados não presentes na entrada
    - NUNCA remover acentos do português
    - NUNCA usar markdown no corpo (asteriscos, hashtags)
    - NUNCA usar TodoWrite (apenas orquestrador gerencia progresso)
  </subagentes>
</restricoes>

<contingencias>
  <output_vazio>
    ERRO CRÍTICO: Subagente não salvou arquivo.
    → Verificar se path está correto
    → Regenerar com prompt idêntico
    → Se falhar 2x → PARAR e informar usuário
  </output_vazio>

  <sinalizador_ausente>
    AVISO: Sinalizador não encontrado.
    → Regenerar com SUFIXO DE CORREÇÃO específico
    → Se falhar 2x → PARAR e informar usuário
  </sinalizador_ausente>

  <limite_tentativas>
    | Escopo | Limite |
    |--------|--------|
    | Por etapa | 2 tentativas |
    | Total no pipeline | [N×2] tentativas |
  </limite_tentativas>
</contingencias>

<contratos_dados>
  | # | Etapa | Entrada | Saída | Validação |
  |---|-------|---------|-------|-----------|
  | 0 | Preparação | $ARGUMENTS | [VARS] | Variáveis extraídas |
  | 1 | [Nome] | [input] | [output] | [sinalizadores] |
  | 2 | [Nome] | [input] | [output] | [sinalizadores] |
  | 3 | [Nome] | [input] | [output] | [sinalizadores] |
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
    | Início do pipeline | Criar TodoWrite com TODAS as etapas (status: pending) |
    | Antes de disparar etapa | Marcar etapa como in_progress |
    | Após validar output | Marcar etapa como completed |
    | Se falhar 2x | Marcar como failed (se suportado) ou manter in_progress |
  </quando_atualizar>

  <formato_todowrite>
    ```javascript
    TodoWrite([
      {content: "Etapa 0 - Preparação", status: "completed", activeForm: "Preparando"},
      {content: "Etapa 1 - [Nome]", status: "in_progress", activeForm: "[Verbo]ando"},
      {content: "Etapa 2 - [Nome]", status: "pending", activeForm: "[Verbo]ando"},
      {content: "Etapa 3 - [Nome]", status: "pending", activeForm: "[Verbo]ando"},
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
  | Etapa | Início Obrigatório | Fim Obrigatório |
  |-------|-------------------|-----------------|
  | 1 | "[INICIO_1]" | "[FIM_1]" |
  | 2 | "[INICIO_2]" | "[FIM_2]" |
  | 3 | "[INICIO_3]" | "[FIM_3]" |
</sinalizadores_formato>

<sufixos_correcao>
  <sufixo_formato>
    [FALHA DE FORMATO. Releia o prompt em .claude/agents/[pipeline]/[agent].md.
    DEVE começar com "[INICIO]". DEVE terminar com "[FIM]".]
  </sufixo_formato>

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
    | $WORKSPACE | Calculada | Caminho completo (ex: "workspace/processo-0814624-28.2019.4.05.8100") |
    | $MANIFEST | Calculada | Caminho do manifest (ex: "$WORKSPACE/_manifest.md") |
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

  <etapa numero="0" nome="Preparação e Injeção de Contexto">
    <!--
      ETAPA CRÍTICA: Calcula variáveis que serão injetadas nos subagentes.
      Subagentes NÃO conhecem $ARGUMENTS - só recebem caminhos prontos.
    -->

    <acao_orquestrador>
      1. **Receber e validar argumento:**
         ```
         $ARGUMENTS = [valor recebido do usuário]
         Se vazio ou inválido → PARAR e pedir ao usuário
         ```

      2. **Calcular variáveis de contexto:**
         ```
         $NUMERO    = $ARGUMENTS (ou extrair número do caminho)
         $WORKSPACE = "workspace/processo-$NUMERO"
         $MANIFEST  = "$WORKSPACE/_manifest.md"
         ```

      3. **Verificar/criar estrutura de workspace:**
         ```bash
         # Criar pasta se não existir
         mkdir -p $WORKSPACE
         mkdir -p $WORKSPACE/fonte
         mkdir -p $WORKSPACE/pesquisa
         mkdir -p $WORKSPACE/revisao

         # Se existir _manifest.md, ler para saber o que já existe
         # Se não existir, criar estrutura inicial
         ```

      4. **Usar convenção de nomenclatura:**
         ```
         # Arquivos de saída seguem: $NUMERO-tipo.md
         # Exemplo: 0814624-28.2019.4.05.8100-relatorio.md
         ```

      5. **Verificar se entrada existe:**
         - Se pipeline precisa de arquivo de entrada, verificar em $WORKSPACE
         - Se não existir, PARAR e informar usuário

      6. **Criar TodoWrite com todas as etapas:**
         ```javascript
         TodoWrite([
           {content: "Etapa 0 - Preparação", status: "in_progress", activeForm: "Preparando"},
           {content: "Etapa 1 - [Nome]", status: "pending", activeForm: "[Verbo]ando"},
           {content: "Etapa 2 - [Nome]", status: "pending", activeForm: "[Verbo]ando"},
           {content: "Etapa N - Finalização", status: "pending", activeForm: "Finalizando"},
         ])
         ```
    </acao_orquestrador>

    <variaveis_calculadas>
      | Variável | Valor Exemplo | Disponível para |
      |----------|---------------|-----------------|
      | $ARGUMENTS | "12345" | Apenas Etapa 0 |
      | $WORKSPACE | "workspace/processo-12345" | Todas as etapas |
      | $MANIFEST | "workspace/processo-12345/_manifest.md" | Todas as etapas |
    </variaveis_calculadas>

    <criterio_sucesso>
      - [ ] $ARGUMENTS válido
      - [ ] $WORKSPACE calculado
      - [ ] Pasta $WORKSPACE existe
      - [ ] Arquivo de entrada existe (se necessário)
      - [ ] TodoWrite criado com todas as etapas
    </criterio_sucesso>

    <transicao>
      1. Marcar Etapa 0 como completed
      2. Marcar Etapa 1 como in_progress
      3. Prosseguir para ETAPA 1
      Se FALHAR → PARAR e informar usuário
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
      <saida>$WORKSPACE/[arquivo-saida]</saida>
    </config>

    <acao_orquestrador>
      1. Verificar se arquivo de entrada existe em $WORKSPACE
      2. **Montar prompt com variáveis injetadas** (ver abaixo)
      3. Disparar Task tool com prompt montado
      4. Aguardar conclusão
      5. Validar output
      6. Atualizar TodoWrite (etapa atual → completed, próxima → in_progress)
    </acao_orquestrador>

    <!--
      PADRÃO DE INJEÇÃO
      ═══════════════════════════════════════════════════════════════════════
      O orquestrador SUBSTITUI as variáveis $WORKSPACE antes de enviar.

      Exemplo: Se $WORKSPACE = "workspace/processo-12345"
      O subagente recebe: "Read: workspace/processo-12345/relatorio.md"
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
          → O orquestrador já substituiu $WORKSPACE pelo caminho real.
          → Leia INTEGRALMENTE.
        </passo>

        <passo numero="3" nome="Executar tarefa">
          → Aplique sua capacidade à entrada lida
          → Use português COM ACENTOS
        </passo>

        <passo numero="4" nome="Salvar">
          Write: $WORKSPACE/[arquivo-saida]
          → O orquestrador já substituiu $WORKSPACE pelo caminho real.
        </passo>
      </execucao>

      <restricoes>
        - DEVE começar com "[SINALIZADOR_INICIO]"
        - DEVE terminar com "[SINALIZADOR_FIM]"
        - SEM asteriscos, SEM hashtags
        - NUNCA usar TodoWrite (apenas orquestrador gerencia)
      </restricoes>

    </prompt_subagente>

    <validacao>
      | # | Verificação | Se Falhar |
      |---|-------------|-----------|
      | 1 | Arquivo existe | ERRO: não salvou |
      | 2 | Tamanho > 0 | ERRO: arquivo vazio |
      | 3 | Sinalizador início | REGENERAR + Sufixo |
      | 4 | Sinalizador fim | REGENERAR + Sufixo |
      | 5 | Contém acentos | REGENERAR + Sufixo |
    </validacao>

    <criterio_sucesso>
      - [ ] Arquivo criado
      - [ ] Sinalizadores presentes
      - [ ] Acentos presentes
    </criterio_sucesso>

    <transicao>
      Se OK → ETAPA 2
      Se FALHAR 2x → PARAR
    </transicao>
  </etapa>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- ETAPA N: FINALIZAÇÃO                                            -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <etapa numero="N" nome="Finalização">
    <acao_orquestrador>
      Exibir ao usuário:

      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      PIPELINE [NOME] - Concluído
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

      Entrada: [entrada original]

      Arquivos gerados:
        ✓ [arquivo-1] (ETAPA 1)
        ✓ [arquivo-2] (ETAPA 2)
        ✓ [arquivo-final] (ETAPA N)

      Localização: [caminho completo]

      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    </acao_orquestrador>
  </etapa>

</etapas_pipeline>

<resumo_arquitetura>
PIPELINE [NOME] - Arquitetura de Injeção de Contexto
│
├── ETAPA 0: Preparação e Injeção
│   ├── Recebe: $ARGUMENTS do usuário
│   ├── Calcula: $WORKSPACE = "workspace/processo-$ARGUMENTS"
│   ├── Cria: Estrutura de pastas se necessário
│   └── Valida: Entrada existe
│
├── ETAPA 1: [Nome]
│   ├── Agent: .claude/agents/[nome-agent].md (capacidade)
│   ├── Entrada: $WORKSPACE/[arquivo] (injetado pelo orquestrador)
│   ├── Saída: $WORKSPACE/[arquivo] (injetado pelo orquestrador)
│   └── Sinalizadores: "[INICIO]" ... "[FIM]"
│
├── ETAPA 2: [Nome]
│   ├── Agent: .claude/agents/[nome-agent].md (capacidade)
│   ├── Entrada: $WORKSPACE/[arquivo] (saída da etapa anterior)
│   ├── Saída: $WORKSPACE/[arquivo]
│   └── Sinalizadores: "[INICIO]" ... "[FIM]"
│
└── ETAPA N: Finalização
    └── Orquestrador exibe resumo com caminhos completos

FLUXO DE DADOS:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   $ARGUMENTS │────▶│  ORQUESTRADOR│────▶│  SUBAGENTES  │
│  (usuário)   │     │  (calcula    │     │  (recebem    │
│              │     │   $WORKSPACE)│     │   caminhos   │
│              │     │              │     │   prontos)   │
└──────────────┘     └──────────────┘     └──────────────┘
</resumo_arquitetura>

<checklist_orquestrador>
Antes de iniciar, verificar:

**Arquitetura:**
- [ ] Identidade: Sou coordenador, não executor
- [ ] Propósito: Transformar [entrada] em [saída]
- [ ] Capacidades: Task, Read, Bash, TodoWrite (não Write direto)

**Injeção de Contexto:**
- [ ] $ARGUMENTS será recebido do usuário na Etapa 0?
- [ ] $WORKSPACE será calculado a partir de $ARGUMENTS?
- [ ] Subagentes recebem caminhos PRONTOS, não variáveis?
- [ ] Agents são modulares (sem caminhos hardcoded)?

**Validação:**
- [ ] Restrições: Sequencial, validar cada etapa, max 2 tentativas
- [ ] Contingências: Sufixos de correção prontos
- [ ] Contratos: Entrada/saída de cada etapa definidos
- [ ] Sinalizadores: Validar início/fim de cada output

**Rastreamento:**
- [ ] TodoWrite criado na Etapa 0 com todas as etapas
- [ ] Atualizado a cada transição (in_progress → completed)
- [ ] Subagentes NUNCA usam TodoWrite
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
| `<contratos_dados>` | Tabela entrada/saída |
| `<rastreamento_progresso>` | Padrão TodoWrite para rastrear etapas |
| `<sinalizadores_formato>` | Validação por etapa |
| `<sufixos_correcao>` | Mensagens para retry |
| `<configuracao>` | Variáveis injetadas e agents utilizados |
| `<etapas_pipeline>` | Definição de cada etapa |
| `<resumo_arquitetura>` | Visão geral do fluxo com injeção de contexto |
| `<checklist_orquestrador>` | Verificação pré-execução |

### Subtags de `<etapa>`

| Tag | Descrição |
|-----|-----------|
| `<config>` | Modelo, tools, agent, entrada e saída (com $WORKSPACE) |
| `<acao_orquestrador>` | O que o orquestrador faz |
| `<prompt_subagente>` | Prompt com variáveis já substituídas |
| `<validacao>` | Regras de validação |
| `<criterio_sucesso>` | Checklist de conclusão |
| `<transicao>` | Próxima etapa ou condição de parada |

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
  Read: $WORKSPACE/[arquivo-entrada]           ← Caminho já substituído
</passo>

<passo numero="3" nome="Executar tarefa">
  → Instruções específicas
  → Use português COM ACENTOS
</passo>

<passo numero="4" nome="Salvar">
  Write: $WORKSPACE/[arquivo-saida]            ← Caminho já substituído
</passo>

<restricoes>
  - DEVE começar com "[SINALIZADOR_INICIO]"
  - DEVE terminar com "[SINALIZADOR_FIM]"
  - SEM asteriscos, SEM hashtags
</restricoes>
```

**Critérios de estrutura correta:**
| # | Critério | Obrigatório |
|---|----------|-------------|
| 1 | Cabeçalho com ═══ e "EXECUTE DIRETAMENTE" | Sim |
| 2 | Passo 1 = Read: .claude/agents/[agent].md | Sim |
| 3 | Passos numerados com `<passo numero="N">` | Sim |
| 4 | Seção `<restricoes>` com sinalizadores | Sim |
| 5 | Tamanho < 50 linhas | Sim |

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
[ ] Seção <restricoes> com sinalizadores obrigatórios?

Validação e Controle:
[ ] <restricoes> proíbe subagentes de usar TodoWrite?
[ ] <contingencias> trata output vazio e sinalizador ausente?
[ ] <contratos_dados> mapeia todas as etapas?
[ ] <sinalizadores_formato> define início/fim de cada etapa?
[ ] <sufixos_correcao> prontos para retry?

Rastreamento:
[ ] Etapa 0 cria TodoWrite com todas as etapas?
[ ] Cada transição atualiza TodoWrite?
[ ] <resumo_arquitetura> mostra fluxo de injeção?
```
