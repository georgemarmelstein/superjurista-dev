# Orquestrador: criar-skill v3.0

> **Propósito:** Meta-orquestrador para criação de skills com TDD (Test-Driven Development) e CSO (Claude Search Optimization).
>
> **Princípio:** "Se você não viu o agente falhar SEM a skill, você não sabe se a skill ensina a coisa certa."
>
> **Padrão:** RED (teste sem skill) → GREEN (skill mínima) → REFACTOR (fechar brechas)

---
description: |
  Use when creating new skills, automations, or specialized knowledge packages.
  Keywords: criar skill, nova skill, automatizar, conhecimento, TDD skill.
argument-hint: [ideia-geral-da-skill]
allowed-tools: Read Write Skill Task TodoWrite AskUserQuestion
---

<meta_orquestrador>
  <tipo>Criador de Artefatos com TDD</tipo>
  <artefato_alvo>Skill (diretório + SKILL.md + references/)</artefato_alvo>
  <spec_referencia>${CLAUDE_PLUGIN_ROOT}/spec/templates/skill.md</spec_referencia>
  <checklist_referencia>${CLAUDE_PLUGIN_ROOT}/spec/referencias/checklist-validacao-skill.md</checklist_referencia>
  <guia_referencia>docs/2026-01-23-guia-escrita-skills.md</guia_referencia>
</meta_orquestrador>

<variaveis>
  | Variável | Origem | Descrição |
  |----------|--------|-----------|
  | $ARGUMENTS | Usuário | Ideia geral da skill |
  | $NOME | Fase 1 | Nome kebab-case (ex: converter-pdf) |
  | $TIPO | Fase 1 | "conhecimento", "scripts", "híbrida" ou "disciplina" |
  | $USAR_FORK | Fase 0 | true se skill executa scripts verbosos (v2.7) |
  | $CAMINHO | Calculado | `.claude/skills/$NOME/` |
</variaveis>

<contratos_dados>
  | Fase | Entrada | Saída | Validação |
  |------|---------|-------|-----------|
  | 0 | $ARGUMENTS | Variáveis calculadas | $NOME, $TIPO e $USAR_FORK definidos |
  | 1 | Ideia geral | Especificação + cenário de teste | Perguntas respondidas |
  | 2 | Especificação | Campos preenchidos com CSO | Description otimizada, fork avaliado |
  | 3 | Cenário de teste | Resultado RED | Falha documentada |
  | 4 | Skill mínima | Resultado GREEN | Compliance verificado |
  | 5 | Skill refinada | Validação final | Checklist ≥ 96 pts |
</contratos_dados>

---

## Princípios Fundamentais

<principios>

  <tdd_para_skills>
    ### TDD Aplicado a Skills

    | Conceito TDD | Criação de Skill |
    |--------------|------------------|
    | Caso de teste | Cenário de pressão com subagente |
    | Código de produção | Documento SKILL.md |
    | Fase RED | Agente viola regra SEM a skill |
    | Fase GREEN | Agente cumpre COM a skill |
    | Refactor | Fechar brechas mantendo compliance |

    **Lei de Ferro:** NENHUMA SKILL SEM TESTE FALHANDO PRIMEIRO
  </tdd_para_skills>

  <cso_optimization>
    ### CSO - Claude Search Optimization

    A description determina se o Claude encontra e ativa a skill corretamente.

    **Regras da Description:**
    1. DEVE começar com "Use when..."
    2. Descrever apenas GATILHOS (quando usar)
    3. NUNCA resumir o workflow da skill
    4. Incluir palavras-chave de busca

    **Por quê?** Testes mostram que quando a description resume o workflow,
    o Claude segue a description em vez de ler o conteúdo completo.

    ```yaml
    # ❌ RUIM (resume workflow)
    description: "Executes plans by dispatching subagents with code review between tasks"
    # → Claude faz UMA revisão porque description diz "code review"

    # ✅ BOM (apenas gatilhos)
    description: "Use when executing implementation plans with independent tasks"
    # → Claude lê a skill completa e descobre que são DUAS revisões
    ```
  </cso_optimization>

  <tipos_skill>
    ### Tipos de Skill e Necessidade de Teste

    | Tipo | Descrição | Precisa TDD? |
    |------|-----------|--------------|
    | **Disciplina** | Impõe regras, tem custo de compliance | SIM - obrigatório |
    | **Técnica** | Método concreto com passos | SIM - verificar aplicação |
    | **Padrão** | Modelo mental, abordagem | SIM - verificar reconhecimento |
    | **Referência** | Documentação, sintaxe | NÃO - apenas validar recuperação |
  </tipos_skill>

  <isolamento_contexto>
    ### Isolamento de Contexto (v2.7)

    Skills que executam scripts com output verboso devem usar `context: fork`:

    | Característica | Usar fork? | Motivo |
    |----------------|------------|--------|
    | Executa scripts Python/Bash | **SIM** | Output verboso polui contexto |
    | Apenas conhecimento/regras | NÃO | Sem execução |
    | Processamento de lote | **SIM** | Muito output acumulado |
    | Múltiplas tentativas/retry | **SIM** | Isolamento de falhas |
    | Tarefa rápida (<10 linhas) | NÃO | Overhead desnecessário |

    **Campos de Isolamento:**
    ```yaml
    context: fork           # Executa em sub-agente isolado
    agent: general-purpose  # Tipo de agente
    ```

    **Padrão de Skill Imperativa (com fork):**
    - SKILL.md enxuto (<100 linhas)
    - Comandos literais para copiar e executar
    - "REGRA ABSOLUTA: NAO crie codigo novo"
    - Documentação rica em references/
  </isolamento_contexto>

  <eficiencia_tokens>
    ### Eficiência de Tokens

    | Tipo de Skill | Limite |
    |---------------|--------|
    | Workflows frequentes | < 150 palavras |
    | Skills carregadas sempre | < 200 palavras |
    | Outras skills | < 500 palavras |
    | SKILL.md máximo | < 500 linhas |
  </eficiencia_tokens>

</principios>

---

## Fase 0: Inicialização

<instrucoes_fase_0>
  <passo numero="1" nome="Registrar tarefa">
    Usar TodoWrite para registrar as fases:
    - Fase 1: Brainstorming e Design
    - Fase 2: Especificação com CSO
    - Fase 3: Teste RED (sem skill)
    - Fase 4: Implementação GREEN (skill mínima)
    - Fase 5: Validação e REFACTOR
  </passo>

  <passo numero="2" nome="Ler referências">
    Read: ${CLAUDE_PLUGIN_ROOT}/spec/templates/skill.md
    Read: ${CLAUDE_PLUGIN_ROOT}/spec/referencias/checklist-validacao-skill.md
    Read: docs/2026-01-23-guia-escrita-skills.md (se existir)
  </passo>

  <passo numero="3" nome="Classificar tipo">
    Determinar tipo da skill:

    **DISCIPLINA** se:
    - Impõe regras que têm custo de seguir
    - Contradiz objetivos imediatos (ex: "testar antes de commitar")
    - Risco de racionalização ("só desta vez...")

    **TÉCNICA** se:
    - Método concreto com passos definidos
    - Transforma input em output específico

    **PADRÃO** se:
    - Modelo mental para tomada de decisão
    - "Quando usar A vs B"

    **REFERÊNCIA** se:
    - Documentação de API, sintaxe, ferramentas
    - Sem regras a violar
  </passo>

  <passo numero="4" nome="Avaliar necessidade de isolamento (v2.7)">
    Determinar se a skill precisa de `context: fork`:

    **USAR FORK** se:
    - [ ] Executa scripts Python/Bash
    - [ ] Output pode ter mais de 50 linhas
    - [ ] Processamento de lote/múltiplos arquivos
    - [ ] Múltiplas tentativas podem ser necessárias
    - [ ] Queremos evitar poluição de contexto

    **NÃO USAR FORK** se:
    - [ ] Skill é apenas conhecimento/regras
    - [ ] Output é mínimo (<10 linhas)
    - [ ] Tarefa é rápida e simples

    Se USAR FORK:
    - SKILL.md deve ser enxuto (<100 linhas)
    - Comandos literais (copiar e colar)
    - "REGRA ABSOLUTA: NAO crie codigo"
    - Documentação rica vai para references/
  </passo>
</instrucoes_fase_0>

---

## Fase 1: Brainstorming e Design

<config_fase_1>
  <objetivo>Refinar ideia e planejar cenário de teste</objetivo>
  <ferramenta>Skill tool com skill="brainstorming"</ferramenta>
  <criterio_saida>Especificação clara + cenário de teste definido</criterio_saida>
</config_fase_1>

<perguntas_skill>
  ### Identidade e Propósito
  1. Qual o NOME da skill? (kebab-case)
  2. O que essa skill FAZ? (verbo de ação)
  3. Que VALOR ela entrega ao usuário?
  4. Qual o DOMÍNIO de conhecimento?

  ### Tipo e Necessidade de TDD
  5. É skill de DISCIPLINA (impõe regras com custo)?
  6. É skill de TÉCNICA (método com passos)?
  7. É skill de PADRÃO (modelo mental)?
  8. É skill de REFERÊNCIA (documentação)?
  9. Precisa de teste TDD? (disciplina/técnica/padrão = SIM)

  ### CSO - Gatilhos de Ativação
  10. Quais SINTOMAS/ERROS devem ativar essa skill?
  11. Quais PALAVRAS-CHAVE o usuário pode usar?
  12. Quais SINÔNIMOS devem ser cobertos?
  13. Quais COMANDOS/FERRAMENTAS estão relacionados?
  14. Quando ela NÃO deve ser usada?

  ### Cenário de Teste (se tipo ≠ referência)
  15. Qual cenário de PRESSÃO testará a skill?
  16. Quais PRESSÕES combinar? (tempo, autoridade, custo, pragmatismo)
  17. Qual comportamento ESPERADO sem a skill? (falha)
  18. Qual comportamento ESPERADO com a skill? (compliance)

  ### Estrutura
  19. O SKILL.md ficará com menos de 500 linhas?
  20. O que vai para references/?
  21. O que vai para scripts/?

  ### Isolamento de Contexto (v2.7)
  22. A skill executa scripts com output verboso?
  23. Precisa de `context: fork` para isolamento?
  24. Se fork, deve usar padrão imperativo (comandos literais)?
  25. Onde ficará a documentação rica (references/)?
</perguntas_skill>

<instrucoes_fase_1>
  <passo numero="1" nome="Ativar brainstorming">
    Usar Skill tool: skill="brainstorming"
    Focar nas perguntas acima.
  </passo>

  <passo numero="2" nome="Definir cenário de teste">
    Se $TIPO ∈ {disciplina, técnica, padrão}:

    Criar cenário de pressão combinando:
    - [ ] Pressão de TEMPO ("cliente esperando")
    - [ ] Pressão de AUTORIDADE ("tech lead disse para pular")
    - [ ] Pressão de CUSTO AFUNDADO ("já gastamos 40 tokens")
    - [ ] Pressão PRAGMÁTICA ("funciona no meu ambiente")
    - [ ] Pressão de EXAUSTÃO ("12 horas de debug")

    Formato do cenário:
    ```
    CONTEXTO: [situação específica com arquivos reais]
    PRESSÕES: [lista das pressões aplicadas]
    PERGUNTA: "Você precisa escolher entre:
      A) [Opção que viola a regra]
      B) [Opção que segue a regra]
      C) [Opção intermediária]
      O que você faz?"
    ESPERADO SEM SKILL: Escolhe A (viola)
    ESPERADO COM SKILL: Escolhe B (cumpre)
    ```
  </passo>

  <passo numero="3" nome="Confirmar especificação">
    Apresentar resumo:
    - Nome: $NOME
    - Tipo: $TIPO
    - Gatilhos: [lista]
    - Cenário de teste: [resumo]
    → Aguardar confirmação.
  </passo>
</instrucoes_fase_1>

---

## Fase 2: Especificação com CSO

<instrucoes_fase_2>

  <passo numero="1" nome="Construir description otimizada">
    A description DEVE:

    1. Começar com "Use when..."
    2. Listar GATILHOS (sintomas, cenários)
    3. Incluir PALAVRAS-CHAVE
    4. NÃO resumir o workflow

    Template:
    ```yaml
    description: >
      Use when [GATILHO 1], [GATILHO 2], or [GATILHO 3] -
      [benefício em uma frase].
      Keywords: [palavra1], [palavra2], [palavra3].
    ```

    Exemplo:
    ```yaml
    description: >
      Use when tests have race conditions, timing dependencies, or
      inconsistent pass/fail behavior - replaces arbitrary timeouts
      with condition polling. Keywords: flaky test, timeout, race condition.
    ```
  </passo>

  <passo numero="1b" nome="Definir isolamento (v2.7)">
    Se a skill executa scripts com output verboso:

    ```yaml
    # Campos de isolamento
    context: fork           # Executa em sub-agente isolado
    agent: general-purpose  # Tipo de agente (general-purpose, Explore, Plan)
    allowed-tools: Bash Read Write
    ```

    **Quando usar fork:**
    - [ ] Skill executa scripts Python/Bash
    - [ ] Output pode ter mais de 50 linhas
    - [ ] Processamento de lote/múltiplos arquivos
    - [ ] Múltiplas tentativas podem ser necessárias

    **Se usar fork, aplicar padrão imperativo:**
    - SKILL.md enxuto (<100 linhas)
    - Comandos literais (copiar e colar)
    - "REGRA ABSOLUTA: NAO crie codigo novo"
    - Documentação rica em references/
  </passo>

  <passo numero="2" nome="Definir identidade">
    ```xml
    <identidade>
      <papel>[Especialista em domínio]</papel>
      <dominio>[Área de conhecimento]</dominio>
      <estilo>[Técnico/Didático/Analítico]</estilo>
    </identidade>
    ```
  </passo>

  <passo numero="3" nome="Definir propósito">
    ```xml
    <proposito>
      <objetivo>[O QUE a skill faz]</objetivo>
      <razao>[POR QUE isso é valioso]</razao>
      <resultado>[O QUE o usuário obtém]</resultado>
    </proposito>
    ```

    NÃO mencionar pipelines ou contextos específicos.
  </passo>

  <passo numero="4" nome="Definir quando_usar com CSO">
    ```xml
    <quando_usar>
      <gatilhos>
        Use quando:
        - [Sintoma/erro específico]
        - [Cenário de uso]
        - [Palavra-chave que usuário menciona]
      </gatilhos>

      <exclusoes>
        NÃO use quando:
        - [Cenário onde não se aplica]
        - [Alternativa mais apropriada]
      </exclusoes>

      <keywords>
        Palavras-chave: [termo1], [termo2], [sinônimo1], [erro1]
      </keywords>
    </quando_usar>
    ```
  </passo>

  <passo numero="5" nome="Definir instruções">
    ```xml
    <instrucoes>
      <passo numero="1" nome="[Nome descritivo]">
        [Instrução clara e específica]
      </passo>
      <passo numero="2" nome="[Nome descritivo]">
        [Instrução clara e específica]
      </passo>
    </instrucoes>
    ```
  </passo>

  <passo numero="6" nome="Definir restrições com red_flags">
    Para skills de DISCIPLINA, incluir:

    ```xml
    <restricoes>
      <nunca>
        - [Comportamento proibido 1]
        - [Comportamento proibido 2]
      </nunca>

      <sempre>
        - [Comportamento obrigatório 1]
        - [Comportamento obrigatório 2]
      </sempre>

      <red_flags>
        Se você está pensando:
        - "Só desta vez..."
        - "O contexto é diferente..."
        - "Já sei que funciona..."

        PARE. Isso é exatamente quando a skill é mais necessária.
      </red_flags>
    </restricoes>
    ```
  </passo>

  <passo numero="7" nome="Criar tabela de racionalizações (se disciplina)">
    Para skills de DISCIPLINA:

    ```xml
    <racionalizacoes>
      | Desculpa Comum | Por Que Está Errada | Resposta Correta |
      |----------------|---------------------|------------------|
      | "Já testei mentalmente" | Testes mentais não encontram bugs | Executar teste real |
      | "É só uma mudança pequena" | Mudanças pequenas causam bugs | Seguir o processo |
      | "O prazo não permite" | Bugs causam mais atraso | Renegociar prazo |
    </racionalizacoes>
    ```
  </passo>

</instrucoes_fase_2>

---

## Fase 3: Teste RED (sem skill)

<instrucoes_fase_3>
  <condicao>Executar apenas se $TIPO ∈ {disciplina, técnica, padrão}</condicao>

  <passo numero="1" nome="Preparar cenário de teste">
    Usar o cenário definido na Fase 1.
    Garantir que combina múltiplas pressões.
  </passo>

  <passo numero="2" nome="Executar teste SEM a skill">
    Usar Task tool com subagente que NÃO tem a skill:

    ```
    Task(
      subagent_type="general-purpose",
      prompt="[Cenário de pressão definido]"
    )
    ```

    Observar: O agente escolheu opção A (viola)?
  </passo>

  <passo numero="3" nome="Documentar falha e racionalização">
    Capturar VERBATIM:
    - Qual opção o agente escolheu
    - Qual justificativa deu
    - Quais racionalizações usou

    ```
    RESULTADO RED:
    - Opção escolhida: A (viola)
    - Justificativa: "[texto exato do agente]"
    - Racionalização: "[desculpa usada]"
    ```
  </passo>

  <passo numero="4" nome="Validar fase RED">
    Se agente NÃO violou (escolheu B):
    - O cenário não tem pressão suficiente
    - Adicionar mais pressões e re-testar

    Se agente VIOLOU (escolheu A):
    - RED passou ✓
    - Prosseguir para GREEN
  </passo>
</instrucoes_fase_3>

---

## Fase 4: Implementação GREEN (skill mínima)

<instrucoes_fase_4>
  <passo numero="1" nome="Criar estrutura de diretório">
    ```
    .claude/skills/$NOME/
    ├── SKILL.md
    ├── references/    (se necessário)
    └── scripts/       (se necessário)
    ```
  </passo>

  <passo numero="2" nome="Gerar SKILL.md mínimo">
    Escrever skill MÍNIMA que endereça apenas as falhas observadas no RED.

    **ESCOLHA O TEMPLATE APROPRIADO:**

    ### Template A: Skill com Isolamento (context: fork)

    Use quando a skill executa scripts com output verboso:

    ```markdown
    ---
    name: $NOME
    description: >
      Use when [GATILHOS]. Keywords: [palavras-chave].
    context: fork
    agent: general-purpose
    allowed-tools: Bash Read Write
    ---

    # $NOME

    REGRA ABSOLUTA: Execute os scripts existentes. NAO crie codigo novo.

    ## Scripts Disponiveis

    | Script | Comando |
    |--------|---------|
    | [nome] | `python .claude/skills/$NOME/scripts/[script].py` |

    ## Comandos Prontos

    ### [Tarefa 1]
    ```bash
    python .claude/skills/$NOME/scripts/[script].py --arg valor
    ```

    ## Retorno Esperado

    Retorne APENAS:
    - Status (sucesso/erro)
    - Caminhos gerados
    - Estatisticas

    NAO inclua:
    - Output completo dos scripts
    - Logs detalhados

    ## Documentacao

    Para detalhes: references/documentacao-completa.md
    ```

    ### Template B: Skill Padrão (sem fork)

    Use para skills de conhecimento, disciplina ou referência:

    ```markdown
    ---
    name: $NOME
    description: >
      Use when [GATILHOS]. Keywords: [palavras-chave].
    ---

    <identidade>
      <papel>[Papel]</papel>
      <dominio>[Domínio]</dominio>
      <estilo>[Estilo]</estilo>
    </identidade>

    <proposito>
      <objetivo>[O que faz]</objetivo>
      <razao>[Por que é valioso]</razao>
      <resultado>[O que usuário obtém]</resultado>
    </proposito>

    <quando_usar>
      <gatilhos>
        Use quando:
        - [Gatilho 1]
        - [Gatilho 2]
      </gatilhos>

      <exclusoes>
        NÃO use quando:
        - [Exclusão 1]
      </exclusoes>

      <keywords>
        Palavras-chave: [termo1], [termo2]
      </keywords>
    </quando_usar>

    <instrucoes>
      <passo numero="1" nome="[Nome]">
        [Instrução]
      </passo>
    </instrucoes>

    <conhecimento> <!-- OU <scripts> -->
      [Conteúdo]
    </conhecimento>

    <restricoes>
      <nunca>
        - [Proibição]
      </nunca>

      <sempre>
        - [Obrigação]
      </sempre>

      <red_flags>
        Se você está pensando:
        - "Só desta vez..."
        PARE. Isso é quando a skill é mais necessária.
      </red_flags>
    </restricoes>

    <racionalizacoes> <!-- Se tipo = disciplina -->
      | Desculpa | Por Que Errada | Resposta Correta |
      |----------|----------------|------------------|
      | "[Desculpa do RED]" | [Explicação] | [Correção] |
    </racionalizacoes>

    <exemplos>
      <exemplo tipo="uso_correto">
        [Demonstração]
      </exemplo>
    </exemplos>
    ```
  </passo>

  <passo numero="3" nome="Executar teste COM a skill">
    Usar Task tool com subagente que TEM a skill:

    ```
    Task(
      subagent_type="general-purpose",
      prompt="
        Leia a skill: .claude/skills/$NOME/SKILL.md

        [Mesmo cenário de pressão do RED]
      "
    )
    ```

    Observar: O agente escolheu opção B (cumpre)?
  </passo>

  <passo numero="4" nome="Validar fase GREEN">
    Se agente ainda VIOLA (escolheu A):
    - Skill não está clara o suficiente
    - Identificar o que faltou
    - Adicionar regra específica
    - Re-testar

    Se agente CUMPRE (escolheu B):
    - GREEN passou ✓
    - Verificar se cita seções da skill como justificativa
    - Prosseguir para REFACTOR
  </passo>
</instrucoes_fase_4>

---

## Fase 5: Validação e REFACTOR

<instrucoes_fase_5>
  <passo numero="1" nome="Teste sob pressão máxima">
    Criar cenário com TODAS as pressões combinadas:
    - Tempo + Autoridade + Custo + Pragmatismo + Exaustão

    Re-executar teste COM a skill.
  </passo>

  <passo numero="2" nome="Identificar brechas">
    Se agente racionaliza violação mesmo com skill:

    1. Capturar exatamente a desculpa
    2. Adicionar negação explícita em `<nunca>`
    3. Adicionar entrada na tabela `<racionalizacoes>`
    4. Adicionar red flag em `<red_flags>`
    5. Re-testar
  </passo>

  <passo numero="3" nome="Verificar tamanho e isolamento">
    **Tamanho:**
    - SKILL.md < 500 linhas? (skill padrão)
    - Se $USAR_FORK: SKILL.md < 100 linhas?
    - Se não, mover para references/

    **Isolamento (se $USAR_FORK = true):**
    - [ ] context: fork presente?
    - [ ] agent: general-purpose presente?
    - [ ] "REGRA ABSOLUTA: NAO crie codigo" presente?
    - [ ] Comandos são literais (copiar e colar)?
    - [ ] Retorno define o que incluir/não incluir?
    - [ ] Documentação rica em references/?
  </passo>

  <passo numero="4" nome="Aplicar checklist">
    Read: ${CLAUDE_PLUGIN_ROOT}/spec/referencias/checklist-validacao-skill.md

    Validar (120 pts total):
    1. YAML Frontmatter com CSO (25 pts)
    2. Estrutura de Diretório (20 pts)
    3. Tags XML Obrigatórias (35 pts)
    4. Tags XML Recomendadas (15 pts)
    5. Ausência de Anti-Patterns (15 pts)
    6. Scripts e Dependências (10 pts)

    Score mínimo: 96 pts (80%)
  </passo>

  <passo numero="5" nome="Verificar indicadores de skill blindada">
    A skill está "à prova de balas" quando:
    - [ ] Agente escolhe opção correta sob pressão máxima
    - [ ] Agente cita seções específicas da skill
    - [ ] Agente reconhece tentação mas segue regras
    - [ ] Tabela de racionalizações cobre desculpas observadas
  </passo>

  <passo numero="6" nome="Reportar resultado">
    Apresentar:
    - Skill criada: $CAMINHO
    - Tipo: $TIPO
    - Score: X/120 (Y%)
    - Testes: RED ✓ GREEN ✓ REFACTOR ✓
    - Estrutura de diretório
    - Próximos passos
  </passo>
</instrucoes_fase_5>

---

## Checklist Resumido

<checklist_rapido>
  ### CSO (Claude Search Optimization)
  [ ] Description começa com "Use when..."
  [ ] Description lista GATILHOS, não workflow
  [ ] Palavras-chave incluídas (sintomas, erros, sinônimos)
  [ ] Tag <quando_usar> com gatilhos e exclusões

  ### TDD (se não for referência)
  [ ] Fase RED executada (falha documentada)
  [ ] Fase GREEN executada (compliance verificado)
  [ ] Fase REFACTOR executada (brechas fechadas)
  [ ] Cenário de teste com múltiplas pressões

  ### Estrutura
  [ ] Localização: .claude/skills/[name]/SKILL.md
  [ ] Nome pasta = campo name do YAML
  [ ] SKILL.md < 500 linhas
  [ ] Progressive disclosure (references/ se necessário)

  ### Isolamento de Contexto (v2.7)
  [ ] Se executa scripts verbosos, usa context: fork?
  [ ] Se fork, tem agent definido?
  [ ] Se fork, SKILL.md é enxuto (<100 linhas)?
  [ ] Se fork, tem "REGRA ABSOLUTA: NAO crie codigo"?
  [ ] Se fork, documentação rica em references/?
  [ ] Se fork, comandos são literais (copiar e colar)?

  ### Conteúdo
  [ ] Tag <proposito> com objetivo + razão + resultado
  [ ] Tag <instrucoes> com passos numerados
  [ ] Tag <restricoes> com nunca + sempre + red_flags
  [ ] Tag <racionalizacoes> (se tipo = disciplina)
  [ ] ZERO caminhos hardcoded
  [ ] ZERO credenciais
</checklist_rapido>

---

## Anti-Padrões a Evitar

<anti_patterns>
  | Anti-Padrão | Problema | Correção |
  |-------------|----------|----------|
  | Description resume workflow | Claude segue description, não lê skill | Usar apenas gatilhos |
  | Skill sem teste RED | Não sabe se ensina certo | Testar antes de escrever |
  | Pressão única no teste | Muito fácil de passar | Combinar 3+ pressões |
  | Racionalizações genéricas | Não fecha brechas reais | Usar texto verbatim do teste |
  | SKILL.md > 500 linhas | Muito contexto | Mover para references/ |
  | Labels vagos | "Processar" não diz nada | Usar verbos específicos |
  | Script sem fork | Output verboso polui contexto | Adicionar context: fork |
  | Fork sem agent | Erro de execução | Adicionar agent: general-purpose |
  | Fork com instruções ricas | Modelo se perde | Usar padrão imperativo (<100 linhas) |
  | Fork sem regra explícita | Modelo cria código novo | "REGRA ABSOLUTA: NAO crie codigo" |
</anti_patterns>

---

## Diferenças: Skill vs Agent vs Orquestrador

<comparativo>
  | Aspecto | Agent | Skill | Skill (fork) | Orquestrador |
  |---------|-------|-------|--------------|--------------|
  | Localização | `.claude/agents/` | `.claude/skills/[name]/` | `.claude/skills/[name]/` | `.claude/commands/` |
  | Estrutura | Arquivo único | Diretório + SKILL.md | Diretório + SKILL.md enxuto | Arquivo único |
  | Foco | Capacidade atômica | Conhecimento + TDD | Scripts + Isolamento | Coordenação |
  | Discovery | Descrição no frontmatter | CSO otimizado | CSO otimizado | /comando |
  | Teste | Opcional | TDD obrigatório* | Validação de execução | Via subagentes |
  | Tamanho | Sem limite | < 500 linhas | < 100 linhas | Sem limite |
  | Contexto | Isolado (Task) | Compartilhado | Isolado (fork) | Principal |

  *Obrigatório para tipos: disciplina, técnica, padrão. Opcional para referência.

  **Quando usar Skill com fork:**
  - Scripts Python/Bash com output verboso
  - Processamento de lote/múltiplos arquivos
  - Tarefas que podem exigir retry/múltiplas tentativas
</comparativo>

---

## Referências

- [obra/superpowers - writing-skills](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md)
- [Guia de Escrita de Skills](docs/2026-01-23-guia-escrita-skills.md)
- [Agent Skills Spec](https://agentskills.io/specification)
