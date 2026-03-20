# Template: Skill Agêntica v1.0

> **Filosofia:** Skill agêntica = pacote self-contained que orquestra agents locais.
> Combina a autonomia de uma skill (discovery via CSO, ativação via Skill tool)
> com a capacidade de orquestração de um command (despacho de subagentes via Task tool).
>
> **Quando usar:** Quando o workflow é complexo demais para uma skill passiva,
> mas específico demais para justificar um command global + agents reutilizáveis.
>
> **Copie para:** `.claude/skills/[nome-skill]/SKILL.md`

---

## Comparação com Outros Padrões

```
┌──────────────────────────────────────────────────────────────────────┐
│                    TAXONOMIA DE ARTEFATOS                            │
│                                                                      │
│  SKILL PASSIVA          SKILL AGÊNTICA          COMMAND              │
│  (conhecimento)         (orquestrador)          (pipeline)           │
│                                                                      │
│  .claude/skills/X/      .claude/skills/X/       .claude/commands/    │
│  ├── SKILL.md           ├── SKILL.md            └── pipeline.md     │
│  └── references/        ├── agents/                                  │
│                         │   ├── agent-1.md      .claude/agents/      │
│                         │   └── agent-2.md      ├── agent-1.md       │
│                         └── references/         └── agent-2.md       │
│                                                                      │
│  Discovery: CSO         Discovery: CSO          Discovery: /comando  │
│  Invocação: Skill tool  Invocação: Skill tool   Invocação: /comando  │
│  Agents: nenhum         Agents: LOCAIS          Agents: GLOBAIS      │
│  Orquestração: inline   Orquestração: Task      Orquestração: Task   │
│  Contexto: compartilhado Contexto: principal    Contexto: principal   │
│  Self-contained: sim    Self-contained: SIM      Self-contained: não  │
└──────────────────────────────────────────────────────────────────────┘
```

| Aspecto | Skill Passiva | Skill Agêntica | Command |
|---------|---------------|----------------|---------|
| Agents | Nenhum | Locais (dentro da skill) | Globais (`.claude/agents/`) |
| Portabilidade | Alta | Alta (tudo no diretório) | Baixa (depende de agents/) |
| Complexidade | Simples | Média | Alta |
| Reutilização dos agents | N/A | Dentro da skill | Por qualquer command |
| Caso de uso | Conhecimento, scripts | Workflows multi-etapa self-contained | Pipelines determinísticos |

---

## Estrutura de Diretórios

```
.claude/skills/[nome-skill]/
├── SKILL.md              # Orquestrador (workflow multi-etapa com XML tags)
├── agents/               # Agents LOCAIS (escopo da skill)
│   ├── [agent-1].md      # Formato leve (sem model/color)
│   └── [agent-2].md
├── references/           # Documentação detalhada (progressive disclosure)
│   └── [referencia].md
└── scripts/              # Scripts executáveis (se necessário)
    └── [script].py
```

---

## Formato do SKILL.md (Orquestrador)

O SKILL.md de uma skill agêntica combina:
- **YAML frontmatter** com CSO (como skill passiva)
- **XML tags de orquestração** (adaptadas do template de command)
- **Filosofia "explain the why"** em restrições e instruções

### Diferenças em relação ao command

| Aspecto | Command | SKILL.md Agêntico |
|---------|---------|-------------------|
| YAML | description, argument-hint, allowed-tools | name, description (CSO) |
| Discovery | /comando | CSO keywords + Skill tool |
| Agents | `.claude/agents/[agent].md` | `agents/[agent].md` (local) |
| `<configuracao>` | `<caminho_agents>.claude/agents/</caminho_agents>` | `<caminho_agents>agents/</caminho_agents>` |
| $WORKSPACE | Calculado via $ARGUMENTS | Definido conforme contexto da skill |

### Template

```markdown
---
name: [nome-da-skill]
description: >
  Use when [GATILHO 1], [GATILHO 2], or [GATILHO 3].
  Keywords: [palavra1], [palavra2], [palavra3].
---

<identidade>
  <papel>[Coordenador do workflow de X], não executor</papel>
  <estilo>Metódico, sequencial, validador rigoroso</estilo>
</identidade>

<proposito>
  <objetivo>[O QUE a skill faz]</objetivo>
  <razao>[POR QUE isso é valioso]</razao>
  <resultado_final>[O QUE o usuário obtém]</resultado_final>
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

<capacidades>
  <tools_orquestrador>
    | Tool | Função |
    |------|--------|
    | Task | Disparar subagentes |
    | Read | Verificar outputs |
    | Bash | Validar sinalizadores |
    | TodoWrite | Rastrear progresso |
  </tools_orquestrador>

  <regras_uso>
    - Subagentes LEEM agents/ diretamente (não recebem cópia)
    - Orquestrador NÃO executa tarefas dos subagentes
    - Cada subagente tem contexto ISOLADO
  </regras_uso>
</capacidades>

<restricoes>
  <orquestrador>
    - NUNCA copiar/resumir prompts de agents — instrua subagente a LER
      **Por quê:** Copiar prompts gasta tokens e pode truncar instruções.
    - NUNCA prosseguir sem validar etapa anterior
      **Por quê:** Sem validação, erros se propagam e corrompem etapas seguintes.
    - NUNCA tentar mais de 2 vezes a mesma etapa
  </orquestrador>
</restricoes>

<contingencias>
  <output_vazio>REGENERAR (máx 2 tentativas)</output_vazio>
  <sinalizador_ausente>REGENERAR com sufixo de correção</sinalizador_ausente>
</contingencias>

<contratos_dados>
  | # | Etapa | Entrada | Saída | Validação |
  |---|-------|---------|-------|-----------|
  | 0 | Preparação | $ARGUMENTS | Variáveis | Definidas |
  | 1 | [Nome] | [input] | [output] | Sinalizadores |
  | 2 | [Nome] | [input] | [output] | Sinalizadores |
</contratos_dados>

<sinalizadores_formato>
  | Etapa | Início | Fim |
  |-------|--------|-----|
  | 1 | "[INICIO_1]" | "[FIM_1]" |
  | 2 | "[INICIO_2]" | "[FIM_2]" |
</sinalizadores_formato>

<configuracao>
  <caminho_agents>agents/</caminho_agents>

  <agents_utilizados>
    | Agent | Capacidade | Arquivo |
    |-------|------------|---------|
    | [agent-1] | [O que faz] | agents/[agent-1].md |
    | [agent-2] | [O que faz] | agents/[agent-2].md |
  </agents_utilizados>
</configuracao>

<etapas_pipeline>

  <etapa numero="0" nome="Preparação">
    <acao_orquestrador>
      1. Registrar progresso via TodoWrite
      2. Ler referências se necessário
      3. Definir variáveis de contexto
    </acao_orquestrador>
  </etapa>

  <etapa numero="1" nome="[Nome]">
    <config>
      <agent>agents/[agent-1].md</agent>
      <entrada>[descrição da entrada]</entrada>
      <saida>[descrição da saída]</saida>
    </config>

    <execucao>
      Despachar subagente que:
      1. Leia agents/[agent-1].md para suas instruções
      2. Receba o contexto necessário
      3. Produza output com sinalizadores

      **Por quê:** Isolar cada etapa em subagente mantém contexto limpo
      e permite validação independente de cada artefato.
    </execucao>

    <validacao>
      1. Arquivo existe?
      2. Sinalizador de início presente?
      3. Sinalizador de fim presente?
    </validacao>
  </etapa>

</etapas_pipeline>

<resumo_arquitetura>
  [Diagrama ASCII do fluxo]
</resumo_arquitetura>

<checklist_orquestrador>
  - [ ] Sou coordenador, não executor
  - [ ] Subagentes leem agents/ diretamente
  - [ ] Cada etapa validada antes de prosseguir
  - [ ] TodoWrite rastreia todas as etapas
</checklist_orquestrador>
```

---

## Formato dos Agents Locais

Agents locais seguem o formato v2.0 **simplificado**:
- Sem `model` (skill decide na hora do despacho)
- Sem `color` (não exibidos independentemente)
- `<sinalizadores>` **opcionais** (se a skill valida, são úteis)
- **"Explain the why"** recomendado em `<instrucoes>` e `<restricoes>`

### Template de Agent Local

```markdown
---
name: [nome-do-agent]
description: [Capacidade em uma linha]
tools: Read Write
---

<identidade>
  <papel>[Quem é este agent]</papel>
  <estilo>[Estilo de execução]</estilo>
</identidade>

<capacidade>
  <habilidade>[O QUE sabe fazer]</habilidade>
  <especializacao>[Em que área]</especializacao>

  **Por que isso importa:** [Explicação do valor que este agent agrega
  ao workflow da skill.]
</capacidade>

<contrato>
  <entrada>
    <tipo>[Tipo de dado]</tipo>
    <formato>[Formato]</formato>
    <requisitos>[O que DEVE conter]</requisitos>
  </entrada>
  <saida>
    <tipo>[Tipo de dado]</tipo>
    <formato>[Formato]</formato>
  </saida>
</contrato>

<restricoes>
  - NUNCA [restrição]
    **Por quê:** [Explicação]
  - SEMPRE [obrigação]
</restricoes>

<contingencias>
  <se_entrada_insuficiente>[Ação]</se_entrada_insuficiente>
</contingencias>

<instrucoes>
  <passo numero="1" nome="[Nome]">
    [Instrução]
    **Por quê:** [Explicação]
  </passo>
</instrucoes>

<formato_saida>
[Template do output]
</formato_saida>
```

### Comparação: Agent Global vs Agent Local

| Campo | Agent Global | Agent Local |
|-------|-------------|-------------|
| `name` | Obrigatório | Obrigatório |
| `description` | Obrigatório | Obrigatório |
| `tools` | Obrigatório | Obrigatório |
| `model` | Obrigatório | **Omitido** (skill decide) |
| `color` | Obrigatório | **Omitido** (não exibido) |
| `<identidade>` | Obrigatório | Obrigatório |
| `<capacidade>` | Obrigatório | Obrigatório |
| `<contrato>` | Obrigatório | Obrigatório |
| `<restricoes>` | Obrigatório | Obrigatório |
| `<contingencias>` | Obrigatório | Obrigatório |
| `<formato_saida>` | Obrigatório | Recomendado |
| `<sinalizadores>` | Obrigatório | **Opcional** |
| `<instrucoes>` | Obrigatório | Obrigatório |
| `<exemplos>` | Recomendado | Recomendado |
| "Explain the why" | Não obrigatório | **Recomendado** |

---

## Checklist de Validação

```
ESTRUTURA:
[ ] SKILL.md em .claude/skills/[name]/SKILL.md
[ ] agents/ com pelo menos 1 agent local
[ ] Nome da pasta = campo name do YAML
[ ] SKILL.md < 500 linhas (use references/ para overflow)

YAML (CSO):
[ ] name em kebab-case
[ ] description começa com "Use when..."
[ ] Keywords incluídas

ORQUESTRAÇÃO:
[ ] <identidade> com papel de coordenador
[ ] <proposito> com objetivo, razão, resultado
[ ] <capacidades> lista tools do orquestrador
[ ] <contratos_dados> mapeia todas as etapas
[ ] <etapas_pipeline> com etapas numeradas
[ ] Cada etapa referencia agent local (agents/X.md)
[ ] <sinalizadores_formato> define validação

AGENTS LOCAIS:
[ ] YAML com name, description, tools
[ ] <identidade>, <capacidade>, <contrato> presentes
[ ] <restricoes> com "explain the why"
[ ] <instrucoes> com passos numerados
[ ] SEM caminhos hardcoded

QUALIDADE:
[ ] "Explain the why" em restrições-chave
[ ] ZERO credenciais ou secrets
[ ] ZERO caminhos absolutos
[ ] Progressive disclosure (references/ para conteúdo extenso)
```

---

## Quando Usar Cada Padrão

| Cenário | Padrão Recomendado |
|---------|-------------------|
| Conhecimento/referência sem workflow | Skill passiva |
| Scripts com output verboso | Skill com `context: fork` |
| Workflow multi-etapa self-contained | **Skill agêntica** |
| Pipeline determinístico com agents reutilizáveis | Command + agents globais |
| Workflow que combina agents globais e locais | Command (usa agents globais) |
