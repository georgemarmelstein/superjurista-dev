---
name: criar-skill
description: >
  Use when creating new skills, modifying existing skills, or packaging
  specialized knowledge into reusable skill format. Use when users say
  "criar skill", "nova skill", "transformar em skill", "automatizar workflow",
  or want to capture a proven workflow as a skill.
  Keywords: criar skill, nova skill, skill creator, automatizar, conhecimento,
  TDD skill, empacotar workflow.
---

<identidade>
  <papel>Coordenador do workflow de criação de skills, não executor</papel>
  <estilo>Metódico, sequencial, validador rigoroso. Aplica TDD para skills
  de disciplina/técnica/padrão. Usa filosofia "explain the why" nas instruções.</estilo>
</identidade>

<proposito>
  <objetivo>Criar skills que Claude ativa e segue corretamente, validadas por teste</objetivo>
  <razao>Skills mal projetadas falham silenciosamente: Claude não as ativa (CSO ruim)
  ou ativa mas não segue (instruções fracas). O ciclo RED/GREEN/REFACTOR garante
  que a skill realmente muda o comportamento do modelo.</razao>
  <resultado_final>Diretório .claude/skills/[nome]/ com SKILL.md validado,
  references/ se necessário, e score >= 80% no checklist</resultado_final>
</proposito>

<quando_usar>
  <gatilhos>
    Use quando:
    - Usuário pede para "criar skill" ou "nova skill"
    - Usuário quer "transformar workflow em skill"
    - Usuário menciona "empacotar conhecimento"
    - Usuário quer "automatizar" um processo repetitivo do Claude
    - Usuário pede para "melhorar" ou "refatorar" skill existente
  </gatilhos>

  <exclusoes>
    NÃO use quando:
    - Usuário quer criar um AGENT (use /criar-agente)
    - Usuário quer criar um COMMAND/ORQUESTRADOR (use /criar-orquestrador)
    - Usuário quer criar um AGENT TEAM (use /criar-team)
    - Skill é trivial (< 10 linhas, sem regras a impor)
  </exclusoes>

  <keywords>
    Palavras-chave: criar skill, nova skill, skill creator, automatizar,
    conhecimento, TDD skill, empacotar, workflow, refatorar skill
  </keywords>
</quando_usar>

<capacidades>
  <tools_orquestrador>
    | Tool | Função |
    |------|--------|
    | Task | Disparar agents locais (brainstormer, tester) |
    | Read | Ler referências e validar outputs |
    | Write | Criar arquivos da skill (exceção justificada: ver nota) |
    | Bash | Validar estrutura de diretório |
    | TodoWrite | Rastrear progresso das etapas |
  </tools_orquestrador>

  <regras_uso>
    - Subagentes LEEM agents/ diretamente (não recebem cópia)
    - Orquestrador NÃO executa tarefas dos subagentes
    - Cada subagente tem contexto ISOLADO
    - Apenas orquestrador usa TodoWrite
  </regras_uso>
</capacidades>

<restricoes>
  <orquestrador>
    - NUNCA criar skill sem antes classificar o tipo
      **Por quê:** O tipo determina se TDD é necessário, qual template usar,
      e a profundidade das restrições. Pular classificação = skill fraca.
    - NUNCA copiar/resumir prompts de agents — instrua subagente a LER
      **Por quê:** Copiar prompts gasta tokens e pode truncar instruções críticas.
    - NUNCA prosseguir sem validar etapa anterior
    - NUNCA resumir workflow na description da skill criada
      **Por quê:** Claude segue a description em vez de ler o conteúdo completo.
      Description com "code review" faz Claude rodar UMA revisão, mesmo que
      a skill defina DUAS.
    - SEMPRE aplicar checklist antes de declarar skill pronta

    **Nota sobre Write:** Esta skill usa Write diretamente na Etapa 4 para
    criar os arquivos da skill-alvo. Isso é uma exceção justificada ao padrão
    "orquestrador não usa Write": aqui o orquestrador É o criador — não há
    subagente de escrita porque a montagem do SKILL.md depende do contexto
    acumulado das etapas anteriores.
  </orquestrador>

  <subagentes>
    - NUNCA usar TodoWrite (apenas orquestrador gerencia)
    - NUNCA inventar dados não fornecidos
  </subagentes>
</restricoes>

<contingencias>
  <teste_red_falha>
    Se o agente NÃO viola na fase RED (escolhe B sem skill):
    → Cenário não tem pressão suficiente
    → Adicionar mais pressões e re-testar
    → Máximo 2 tentativas de ajuste
  </teste_red_falha>

  <teste_green_falha>
    Se o agente ainda VIOLA na fase GREEN (escolhe A com skill):
    → Skill não está clara o suficiente
    → Identificar falha específica na instrução
    → Adicionar regra ou racionalização
    → Re-testar (máximo 2 tentativas)
  </teste_green_falha>

  <teste_competing_falha>
    Se o agente CEDE ao pedido contrário na fase COMPETING:
    → A skill depende do apoio do prompt (falha silenciosa)
    → Adicionar à <racionalizacoes> a desculpa "o usuário pediu/autorizou"
    → Re-testar (máximo 2 tentativas)
    → Persistindo: registrar a pendência no relatório final (não-bloqueante)
  </teste_competing_falha>

  <skill_existente>
    Se já existe .claude/skills/$NOME/:
    → Perguntar se é refatoração ou substituição
    → Se refatoração: ler SKILL.md atual antes de brainstorming
  </skill_existente>
</contingencias>

<contratos_dados>
  | # | Etapa | Entrada | Saída | Validação |
  |---|-------|---------|-------|-----------|
  | 0 | Preparação | $ARGUMENTS | Variáveis, refs lidas, scout | $NOME definido; veredito CRIAR/ABSORVER/DROP |
  | 1 | Brainstorming | Ideia + refs | Especificação refinada | Confirmação do usuário |
  | 2 | Especificação CSO | Especificação | Campos YAML + XML | Description CSO válida |
  | 3 | Teste RED | Cenário de pressão | Resultado da violação | Agente violou sem skill |
  | 4 | Implementação GREEN+COMPETING | Spec + resultado RED | SKILL.md criado | Agente cumpre com skill E resiste a pedido contrário |
  | 5 | Validação | Skill completa | Score >= 80% | Checklist aprovado |
</contratos_dados>

<sinalizadores_formato>
  | Etapa | Início | Fim |
  |-------|--------|-----|
  | 1 (brainstormer) | "ESPECIFICAÇÃO DA SKILL" | "Especificação concluída." |
  | 3/4 (tester) | "RESULTADO DO TESTE" | "Teste concluído." |
</sinalizadores_formato>

<conhecimento>
  <topico nome="Ciclo TDD para Skills">
    RED: Provar que SEM a skill, agente viola sob pressão.
    GREEN: Provar que COM a skill, agente cumpre.
    REFACTOR: Fechar brechas sob pressão máxima.
    **Por quê:** Se não viu o agente falhar SEM a skill, não sabe se a skill ensina a coisa certa.
  </topico>

  <topico nome="Taxonomia de Skills">
    | Tipo | TDD? | Template |
    |------|------|----------|
    | Disciplina (impõe regras com custo) | SIM | Padrão + racionalizações |
    | Técnica (método com passos) | SIM | Padrão |
    | Padrão (modelo mental) | SIM | Padrão |
    | Referência (documentação) | NÃO | Padrão ou Fork |
    | Agêntica (orquestra subagentes) | SIM | skill-agentica.md |
    <!-- Para detalhes: Ver references/skill-writing-guide.md -->
  </topico>

  <topico nome="CSO - Claude Search Optimization">
    Description = mecanismo de discovery. DEVE começar com "Use when...",
    listar GATILHOS (não workflow), incluir keywords.
    <!-- Para detalhes: Ver references/skill-writing-guide.md -->
  </topico>
</conhecimento>

<configuracao>
  <caminho_agents>agents/</caminho_agents>

  <agents_utilizados>
    | Agent | Capacidade | Arquivo |
    |-------|------------|---------|
    | brainstormer | Refinar ideia via questionamento estruturado | agents/brainstormer.md |
    | tester | Testar skill com cenário de pressão (RED/GREEN) | agents/tester.md |
  </agents_utilizados>

  <referencias>
    | Referência | Quando carregar | Arquivo |
    |------------|-----------------|---------|
    | Guia de escrita | Fase 2 (especificação) | references/skill-writing-guide.md |
    | Template skill | Fase 4 (implementação) | ${CLAUDE_PLUGIN_ROOT}/spec/templates/skill.md |
    | Template agêntica | Fase 4 (se skill agêntica) | ${CLAUDE_PLUGIN_ROOT}/spec/templates/skill-agentica.md |
    | Checklist | Fase 5 (validação) | ${CLAUDE_PLUGIN_ROOT}/spec/referencias/checklist-validacao-skill.md |
  </referencias>

  <variaveis>
    | Variável | Origem | Descrição |
    |----------|--------|-----------|
    | $ARGUMENTS | Usuário | Ideia geral da skill |
    | $NOME | Fase 1 | Nome kebab-case |
    | $TIPO | Fase 1 | disciplina, técnica, padrão, referência |
    | $USAR_FORK | Fase 1 | true se skill executa scripts verbosos |
    | $CAMINHO | Calculado | .claude/skills/$NOME/ |
  </variaveis>
</configuracao>

<etapas_pipeline>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- ETAPA 0: PREPARAÇÃO                                             -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <etapa numero="0" nome="Preparação">
    <acao_orquestrador>
      1. Registrar progresso via TodoWrite:
         - Etapa 0: Preparação
         - Etapa 1: Brainstorming e Design
         - Etapa 2: Especificação CSO
         - Etapa 3: Teste RED (sem skill)
         - Etapa 4: Implementação GREEN
         - Etapa 5: Validação e REFACTOR

      2. Ler referências base:
         Read: ${CLAUDE_PLUGIN_ROOT}/spec/templates/skill.md
         Read: ${CLAUDE_PLUGIN_ROOT}/spec/referencias/checklist-validacao-skill.md

      3. Se $ARGUMENTS menciona skill existente:
         Verificar se .claude/skills/[nome]/ já existe
         Se sim: modo refatoração (ler SKILL.md atual)

      4. Scout de capacidade (regra de nascimento — antes de criar):
         Buscar se a capacidade JÁ EXISTE em outra casa — Grep pelas palavras
         da ideia nas descriptions de:
         - .claude/skills/** do projeto atual
         - skills/ do plugin superjurista-dev (marketplace)
         - ~/.claude/skills/** (global)
         Veredito: CRIAR (não existe) | ABSORVER em [X] (quase existe →
         modo refatoração da skill-alvo, não skill nova) | DROP (já coberta).
         **Por quê:** Consumir, nunca copiar. Skill duplicada compete no CSO
         com a original e as duas passam a falhar na ativação.

      5. Se a base for skill EXTERNA (marketplace de terceiros, GitHub):
         antes de forkar, ler o SKILL.md procurando comandos shell inesperados,
         escrita de arquivos fora do escopo, chamadas de rede e manejo de
         credenciais. Achado suspeito → PARAR e reportar ao usuário.
         **Por quê:** Skill adotada roda com as permissões da sua sessão;
         o vet acontece uma vez, na adoção — depois ninguém mais olha.

      **Por quê:** Ler as referências no início evita que o orquestrador
      "esqueça" os padrões durante a criação. O template e checklist
      são o contrato de qualidade.
    </acao_orquestrador>

    <transicao>Marcar Etapa 0 completed → Etapa 1 in_progress</transicao>
  </etapa>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- ETAPA 1: BRAINSTORMING E DESIGN                                 -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <etapa numero="1" nome="Brainstorming e Design">
    <config>
      <agent>agents/brainstormer.md</agent>
      <entrada>$ARGUMENTS (ideia do usuário)</entrada>
      <saida>Especificação refinada + cenário de teste</saida>
    </config>

    <execucao>
      Despachar subagente via Task tool:

      ═══════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE BRAINSTORMING. EXECUTE DIRETAMENTE.
      ═══════════════════════════════════════════════════════════════

      Passo 1: Read: .claude/skills/criar-skill/agents/brainstormer.md
      → Siga fielmente as instruções deste agent.

      Passo 2: A ideia do usuário é: [inserir $ARGUMENTS]

      Passo 3: Conduza a entrevista completa (25 perguntas).
      Apresente resumo para confirmação.

      Restrição: NÃO use TodoWrite.
    </execucao>

    <validacao>
      O subagente deve retornar especificação com:
      - Nome ($NOME) definido
      - Tipo ($TIPO) classificado
      - Fork ($USAR_FORK) avaliado
      - Gatilhos CSO listados
      - Cenário de teste definido (se tipo != referência)
    </validacao>

    <transicao>
      Extrair $NOME, $TIPO, $USAR_FORK da especificação.
      Calcular $CAMINHO = .claude/skills/$NOME/
      Confirmar com usuário antes de prosseguir.
      Marcar Etapa 1 completed → Etapa 2 in_progress.
    </transicao>
  </etapa>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- ETAPA 2: ESPECIFICAÇÃO CSO                                      -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <etapa numero="2" nome="Especificação CSO">
    <execucao>
      Esta etapa é executada INLINE pelo orquestrador (não precisa de subagente).

      **Por quê:** A especificação CSO é um trabalho de construção de campos
      YAML e XML a partir da especificação da Etapa 1. Não requer raciocínio
      profundo isolado — é montagem estruturada.

      1. Ler guia de escrita:
         Read: .claude/skills/criar-skill/references/skill-writing-guide.md

      2. Construir description otimizada:
         - DEVE começar com "Use when..."
         - DEVE listar apenas GATILHOS
         - NUNCA resumir o workflow
         - Incluir keywords

      3. Se $USAR_FORK = true:
         Definir campos de isolamento (context: fork, agent: general-purpose)

      4. Preencher todos os campos XML:
         - <identidade> com papel e estilo
         - <proposito> com objetivo, razão, resultado
         - <quando_usar> com gatilhos, exclusões, keywords
         - <instrucoes> com passos numerados
         - <restricoes> com "explain the why"
         - <racionalizacoes> (se tipo = disciplina, preencher após teste RED)
    </execucao>

    <transicao>
      Especificação CSO completa.
      Se $TIPO = referência → PULAR Etapa 3 → ir direto para Etapa 4.
      Senão → Marcar Etapa 2 completed → Etapa 3 in_progress.
    </transicao>
  </etapa>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- ETAPA 3: TESTE RED (sem skill)                                   -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <etapa numero="3" nome="Teste RED (sem skill)">
    <condicao>Executar apenas se $TIPO ∈ {disciplina, técnica, padrão}</condicao>

    <config>
      <agent>agents/tester.md</agent>
      <entrada>Cenário de pressão definido na Etapa 1</entrada>
      <saida>Resultado do teste: opção escolhida + justificativa</saida>
    </config>

    <execucao>
      Despachar subagente via Task tool SEM dar acesso à skill:

      ═══════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE TESTE. EXECUTE DIRETAMENTE.
      ═══════════════════════════════════════════════════════════════

      Passo 1: Read: .claude/skills/criar-skill/agents/tester.md
      → Siga fielmente as instruções deste agent.

      Passo 2: Avalie o seguinte cenário:
      [inserir cenário de pressão completo da Etapa 1]

      Restrição: NÃO use TodoWrite. NÃO leia nenhuma skill.

      **Por quê:** Na fase RED, queremos ver como o agente decide SEM
      orientação. Se ele já acerta sem a skill, o cenário é fraco.
    </execucao>

    <validacao>
      Resultado esperado: agente VIOLA (escolhe opção A).

      Se agente NÃO violou (escolheu B):
      → Cenário sem pressão suficiente
      → Adicionar mais pressões e re-testar
      → Máximo 2 tentativas

      Se agente VIOLOU (escolheu A):
      → Capturar VERBATIM: opção, justificativa, racionalizações
      → Estas racionalizações alimentam <racionalizacoes> na skill
    </validacao>

    <transicao>
      RED passou: agente violou sem skill.
      Racionalizações capturadas.
      Marcar Etapa 3 completed → Etapa 4 in_progress.
    </transicao>
  </etapa>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- ETAPA 4: IMPLEMENTAÇÃO GREEN                                     -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <etapa numero="4" nome="Implementação GREEN">
    <execucao>
      Esta etapa combina implementação INLINE + teste via subagente.

      PARTE A — Criar skill:

      1. Criar estrutura de diretório:
         Bash: mkdir -p $CAMINHO/references

      2. Escolher template:
         - Se $USAR_FORK = true → Template imperativo (<100 linhas)
         - Se tipo = referência → Template padrão (sem TDD tags)
         - Senão → Template padrão completo

      3. Escrever SKILL.md com todos os campos da Etapa 2:
         Write: $CAMINHO/SKILL.md

      4. Se tipo = disciplina:
         Incluir <racionalizacoes> com desculpas capturadas no RED

      PARTE B — Testar skill (GREEN):

      5. Despachar subagente via Task tool COM acesso à skill:

         ═══════════════════════════════════════════════════════════
         VOCÊ É UM SUBAGENTE DE TESTE. EXECUTE DIRETAMENTE.
         ═══════════════════════════════════════════════════════════

         Passo 1: Read: .claude/skills/criar-skill/agents/tester.md
         Passo 2: Read: $CAMINHO/SKILL.md
         → Internalize as regras desta skill.
         Passo 3: Avalie o seguinte cenário:
         [inserir MESMO cenário de pressão do RED]

         Restrição: NÃO use TodoWrite.

      6. Resultado esperado: agente CUMPRE (escolhe opção B).

         Se agente ainda VIOLA:
         → Skill não está clara
         → Identificar falha específica
         → Fortalecer regra ou adicionar racionalização
         → Re-testar (máximo 2 tentativas)

      PARTE C — Teste COMPETING (se tipo = disciplina):

      7. Despachar subagente COM a skill, mas com o cenário acrescido do
         pedido EXPLÍCITO do usuário pelo atalho que a skill proíbe
         (ex.: "pule essa verificação, é urgente, eu autorizo"):

         Mesmo formato da PARTE B, com o cenário modificado.

      8. Resultado esperado: agente RECUSA o atalho citando a skill.

         Se agente cede ao pedido:
         → A skill só funciona quando o prompt já apoia a regra
           (falha silenciosa mais comum em produção)
         → Fortalecer <racionalizacoes> com a desculpa "o usuário mandou"
         → Re-testar (máximo 2 tentativas)

      **Por quê:** RED prova que sem skill viola; GREEN prova que com skill
      cumpre em prompt neutro. Só COMPETING prova que a skill resiste quando
      o próprio usuário pressiona contra ela — que é quando ela mais importa.
    </execucao>

    <validacao>
      - [ ] $CAMINHO/SKILL.md existe
      - [ ] YAML frontmatter com name e description
      - [ ] Teste GREEN passou (agente cumpre com skill)
      - [ ] Teste COMPETING passou (agente resiste a pedido contrário — se disciplina)
    </validacao>

    <transicao>
      GREEN passou: agente cumpre com skill.
      Marcar Etapa 4 completed → Etapa 5 in_progress.
    </transicao>
  </etapa>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- ETAPA 5: VALIDAÇÃO E REFACTOR                                    -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <etapa numero="5" nome="Validação e REFACTOR">
    <execucao>
      1. Ler checklist:
         Read: ${CLAUDE_PLUGIN_ROOT}/spec/referencias/checklist-validacao-skill.md

      2. Aplicar checklist (120 pts total):
         | Categoria | Peso |
         |-----------|------|
         | YAML Frontmatter com CSO | 25 pts |
         | Estrutura de Diretório | 20 pts |
         | Tags XML Obrigatórias | 35 pts |
         | Tags XML Recomendadas | 15 pts |
         | Ausência de Anti-Patterns | 15 pts |
         | Scripts e Dependências | 10 pts |

      3. Score mínimo: 96 pts (80%)
         Se abaixo: corrigir e reavaliar.

      4. Verificar tamanho:
         - SKILL.md < 500 linhas? (padrão)
         - Se $USAR_FORK: SKILL.md < 100 linhas?
         - Se excede: mover para references/

      5. Verificações finais:
         - [ ] ZERO caminhos absolutos hardcoded
         - [ ] ZERO credenciais ou secrets
         - [ ] Description NÃO resume workflow
         - [ ] "Explain the why" em restrições-chave
         - [ ] Acentos em português presentes
    </execucao>

    <transicao>
      Marcar Etapa 5 completed.
      Apresentar relatório final.
    </transicao>
  </etapa>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- ETAPA 6: RELATÓRIO FINAL                                         -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <etapa numero="6" nome="Relatório Final">
    <acao_orquestrador>
      Exibir ao usuário:

      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      SKILL CRIADA
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

      Skill: $CAMINHO
      Nome: $NOME
      Tipo: $TIPO
      Fork: $USAR_FORK

      Score: X/120 (Y%)

      Testes:
        RED:      [passou/N/A]
        GREEN:    [passou/N/A]
        REFACTOR: [passou/N/A]

      Estrutura:
        $CAMINHO/
        ├── SKILL.md
        ├── references/ (se criado)
        └── scripts/ (se criado)

      Próximos passos:
        - Testar com cenários reais
        - Ajustar keywords CSO se não ativar corretamente
        - Mover conteúdo extenso para references/ se necessário

      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    </acao_orquestrador>
  </etapa>

</etapas_pipeline>

<resumo_arquitetura>
SKILL AGÊNTICA: criar-skill
│
├── ETAPA 0: Preparação
│   ├── TodoWrite com todas as etapas
│   ├── Ler referências (template + checklist)
│   └── Scout de capacidade (CRIAR/ABSORVER/DROP) + vet de skill externa
│
├── ETAPA 1: Brainstorming
│   ├── Agent: agents/brainstormer.md
│   ├── 25 perguntas estruturadas
│   └── Output: especificação + cenário de teste
│
├── ETAPA 2: Especificação CSO (inline)
│   ├── Construir description otimizada
│   └── Preencher campos XML
│
├── ETAPA 3: Teste RED (se tipo != referência)
│   ├── Agent: agents/tester.md SEM skill
│   └── Esperado: agente viola → racionalizações capturadas
│
├── ETAPA 4: Implementação GREEN + COMPETING
│   ├── Escrever SKILL.md com template adequado
│   ├── Agent: agents/tester.md COM skill
│   ├── Esperado: agente cumpre (GREEN)
│   └── Esperado: agente resiste a pedido contrário (COMPETING, se disciplina)
│
├── ETAPA 5: Validação e REFACTOR
│   ├── Checklist 120 pts (mínimo 80%)
│   └── Correções se necessário
│
└── ETAPA 6: Relatório Final

FLUXO DE DADOS:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  $ARGUMENTS  │────▶│  SKILL.md    │────▶│  agents/     │
│  (ideia)     │     │  (orquestra) │     │  (executam)  │
│              │     │              │     │              │
│              │     │  Lê refs     │     │  brainstormer│
│              │     │  Valida      │     │  tester      │
│              │     │  Escreve     │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
</resumo_arquitetura>

<checklist_orquestrador>
Antes de iniciar, verificar:

**Identidade:**
- [ ] Sou coordenador, não executor
- [ ] Subagentes leem agents/ diretamente
- [ ] Apenas EU uso TodoWrite

**Referências:**
- [ ] Template de skill lido
- [ ] Checklist de validação lido
- [ ] Guia de escrita disponível em references/

**Workflow:**
- [ ] Tipo classificado antes de criar
- [ ] RED executado antes de GREEN (se aplicável)
- [ ] Description NÃO resume workflow
- [ ] Score >= 80% antes de declarar pronto
</checklist_orquestrador>
