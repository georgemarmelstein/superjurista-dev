# Design: Skill Agêntica Robusta (Padrão v2.7+)

**Status:** Documento normativo — padrão alternativo ao design leve
**Versão:** 1.0
**Data:** 2026-03-18

---

## 1. Contexto e Motivação

O framework v2.7 tem dois padrões possíveis para skills que contêm agents internos:

| Aspecto | Design Leve | Design Robusto (este) |
|---------|-------------|----------------------|
| Agents internos | Sem model/color/sinalizadores | Formato v2.0 completo |
| SKILL.md | Conversacional com XML | Orquestrador cego formal |
| Validação | Usuário valida manualmente | Sinalizadores automáticos via grep |
| Contratos | Implícitos | Explícitos com tipos |
| Rastreabilidade | Nenhuma | TodoWrite + arquivos intermediários |
| Compatibilidade | Patterns simplificados | Preserva padrão v2.7 integralmente |

O design robusto é o padrão correto quando a skill executa um pipeline de 3+ etapas sequenciais onde falhas em uma etapa impedem as seguintes.

---

## 2. Estrutura de Diretórios

```
.claude/skills/criar-skill/
├── SKILL.md                     # Orquestrador cego: YAML skill + body orquestrador
├── agents/                      # Agents internos no formato v2.0 COMPLETO
│   ├── spec-brainstormer.md     # Etapa 1: ideia → especificação
│   ├── spec-escritor.md         # Etapa 2: especificação → SKILL.md
│   └── spec-validador.md        # Etapa 3: SKILL.md → relatório de conformidade
└── references/
    └── REFERENCE.md             # Documentação técnica (progressive disclosure)
```

Os agents internos ficam em `agents/` dentro da pasta da skill — não em `.claude/agents/` — porque são especializados para esta skill. Se um agent vier a ser reutilizado em outros pipelines, deve ser promovido para `.claude/agents/[categoria]/`.

---

## 3. Anatomia do SKILL.md

O SKILL.md no design robusto é um híbrido estrutural:

- **YAML frontmatter** segue o padrão de skill (para discovery pelo sistema CSO)
- **Body** segue a anatomia de orquestrador (tags XML do `orquestrador.md`)

### 3.1 YAML Frontmatter

```yaml
---
name: criar-skill
description: >
  Use when creating new skills, automations, or specialized knowledge packages.
  Keywords: criar skill, nova skill, automatizar, conhecimento, TDD skill.
allowed-tools: Read Write Bash Task TodoWrite
---
```

`allowed-tools` inclui `Task` para que o Claude possa disparar agents internos. Sem `Task`, o orquestrador não consegue coordenar subagentes. O campo `context: fork` é incompatível com este padrão — fork isola o contexto e impede o uso de Task.

### 3.2 Tags XML do Body (mapeamento com orquestrador.md)

| Tag | Conteúdo no SKILL.md |
|-----|---------------------|
| `<identidade>` | Papel de coordenador, não executor |
| `<proposito>` | Transformar ideia em SKILL.md validado (score >= 96/120) |
| `<capacidades>` | Task, Read, Bash, TodoWrite — com regras de uso |
| `<restricoes>` | Nunca executar etapas dos agents; zero-read para existência |
| `<contingencias>` | Output vazio → regenerar; sinalizador ausente → sufixo de correção |
| `<contratos_dados>` | Tabela entrada/saída por etapa (ver 3.3) |
| `<rastreamento_progresso>` | TodoWrite exclusivo do orquestrador |
| `<sinalizadores_formato>` | Início/fim obrigatórios por etapa (ver 3.4) |
| `<sufixos_correcao>` | Mensagens padronizadas para retry |
| `<configuracao>` | Variáveis injetadas, agents utilizados, convenção de nomenclatura |
| `<etapas_pipeline>` | Etapa 0 a 4 com prompts de subagente estruturados |
| `<resumo_arquitetura>` | Diagrama do fluxo completo |
| `<checklist_orquestrador>` | Verificação pré-execução |

### 3.3 Contratos de Dados

```xml
<contratos_dados>
  | # | Etapa | Entrada | Saída | Validação |
  |---|-------|---------|-------|-----------|
  | 0 | Preparação | $ARGUMENTS | $NOME, $CAMINHO | Variáveis calculadas; pasta criada |
  | 1 | Brainstorming | $ARGUMENTS (string) | $CAMINHO/spec.md | "# ESPECIFICAÇÃO DA SKILL" + "## Pronto para Escrita" |
  | 2 | Escrita | $CAMINHO/spec.md | $CAMINHO/SKILL.md | "# SKILL GERADA:" + "## Estrutura Criada" |
  | 3 | Validação | $CAMINHO/SKILL.md | $CAMINHO/validacao.md | "# RELATÓRIO DE VALIDAÇÃO" + "## Score Final:" |
  | 4 | Finalização | Todos os arquivos | Resumo ao usuário | Todos os arquivos existem; score extraído |
</contratos_dados>
```

### 3.4 Sinalizadores por Etapa

```xml
<sinalizadores_formato>
  | Etapa | Início Obrigatório | Fim Obrigatório |
  |-------|-------------------|-----------------|
  | 1 | "# ESPECIFICAÇÃO DA SKILL" | "## Pronto para Escrita" |
  | 2 | "# SKILL GERADA:" | "## Estrutura Criada" |
  | 3 | "# RELATÓRIO DE VALIDAÇÃO" | "## Score Final:" |
</sinalizadores_formato>
```

### 3.5 Estrutura do Prompt de Subagente

Cada etapa usa `<prompt_subagente>` com a estrutura exata do template:

```xml
<prompt_subagente tipo="BRAINSTORMER">
  ═══════════════════════════════════════════════════════════════════════
  VOCÊ É UM SUBAGENTE DE ESPECIFICAÇÃO. EXECUTE DIRETAMENTE.
  ═══════════════════════════════════════════════════════════════════════

  <passo numero="1" nome="Ler instruções do agent">
    Read: .claude/skills/criar-skill/agents/spec-brainstormer.md
    → Este arquivo define sua CAPACIDADE. Siga fielmente.
  </passo>

  <passo numero="2" nome="Processar ideia">
    A ideia de skill é: [VALOR DE $ARGUMENTS SUBSTITUÍDO AQUI]
    → Expanda, questione, defina o escopo.
  </passo>

  <passo numero="3" nome="Salvar especificação">
    Write: [VALOR DE $CAMINHO SUBSTITUÍDO AQUI]/spec.md
  </passo>

  <restricoes>
    - DEVE começar com "# ESPECIFICAÇÃO DA SKILL"
    - DEVE terminar com "## Pronto para Escrita"
    - Use português COM ACENTOS
    - NUNCA usar TodoWrite
  </restricoes>
</prompt_subagente>
```

O orquestrador substitui `$ARGUMENTS` e `$CAMINHO` pelos valores reais antes de enviar. O subagente recebe caminhos prontos, nunca variáveis.

---

## 4. Anatomia dos Agents Internos (Formato v2.0 Completo)

### 4.1 spec-brainstormer.md

```yaml
---
name: spec-brainstormer
description: Expande uma ideia de skill em especificação completa com tipo, gatilhos CSO e cenário de teste TDD
tools: Read Write
model: sonnet
color: yellow
---
```

**Modelo:** `sonnet` — tarefa operacional de análise.
**Cor:** `yellow` — exploração e investigação.
**Sinalizadores:** Início: `# ESPECIFICAÇÃO DA SKILL` / Fim: `## Pronto para Escrita`

9 tags XML obrigatórias: `<identidade>`, `<capacidade>`, `<contrato>`, `<restricoes>`, `<contingencias>`, `<formato_saida>`, `<sinalizadores>`, `<instrucoes>`, `<exemplos>`

### 4.2 spec-escritor.md

```yaml
---
name: spec-escritor
description: Transforma especificação de skill em SKILL.md completo e conforme com o padrão v2.7
tools: Read Write
model: opus
color: green
---
```

**Modelo:** `opus` — tarefa de redação precisa exigindo conformidade rigorosa.
**Cor:** `green` — construção e design.
**Sinalizadores:** Início: `# SKILL GERADA: [nome]` / Fim: `## Estrutura Criada`

### 4.3 spec-validador.md

```yaml
---
name: spec-validador
description: Aplica checklist de conformidade v2.7 em um SKILL.md e produz relatório com score numérico
tools: Read Write
model: haiku
color: red
---
```

**Modelo:** `haiku` — tarefa operacional de checklist.
**Cor:** `red` — revisão crítica e validação.
**Sinalizadores:** Início: `# RELATÓRIO DE VALIDAÇÃO` / Fim: `## Score Final: N/120`

---

## 5. Fluxo de Execução Completo

```
SKILL.md ativado → Claude age como orquestrador cego
│
├── ETAPA 0: PREPARAÇÃO
│   ├── Extrai $NOME de $ARGUMENTS (kebab-case)
│   ├── Calcula $CAMINHO = ".claude/skills/$NOME"
│   ├── Bash: test -d "$CAMINHO" (NUNCA Read para verificar existência)
│   ├── Bash: mkdir -p $CAMINHO $CAMINHO/references
│   └── TodoWrite: 5 etapas criadas
│
├── ETAPA 1: BRAINSTORMING [Task → spec-brainstormer.md]
│   ├── Orquestrador NUNCA lê a ideia — passa como string no prompt
│   ├── Task: prompt ═══ + 3 passos (Read agent, processar, Write spec.md)
│   ├── Bash: test -f $CAMINHO/spec.md
│   ├── Bash: grep "# ESPECIFICAÇÃO DA SKILL" $CAMINHO/spec.md
│   ├── Bash: grep "## Pronto para Escrita" $CAMINHO/spec.md
│   └── Se falha 2x → PARAR
│
├── ETAPA 2: ESCRITA [Task → spec-escritor.md]
│   ├── Orquestrador NUNCA lê spec.md — passa CAMINHO para subagente
│   ├── Task: prompt ═══ + 3 passos (Read agent, Read spec.md, Write SKILL.md)
│   ├── Bash: test -f $CAMINHO/SKILL.md
│   ├── Bash: grep "# SKILL GERADA:" $CAMINHO/SKILL.md
│   ├── Bash: grep "## Estrutura Criada" $CAMINHO/SKILL.md
│   └── Se falha 2x → PARAR
│
├── ETAPA 3: VALIDAÇÃO [Task → spec-validador.md]
│   ├── Task: prompt ═══ + 3 passos (Read agent, Read SKILL.md, Write validacao.md)
│   ├── Bash: test -f $CAMINHO/validacao.md
│   ├── Bash: grep "# RELATÓRIO DE VALIDAÇÃO" $CAMINHO/validacao.md
│   ├── Bash: grep "## Score Final:" $CAMINHO/validacao.md
│   ├── Extrai score numérico do relatório
│   └── Se score < 96 → voltar Etapa 2 com feedback (max 2 ciclos)
│
└── ETAPA 4: FINALIZAÇÃO
    ├── TodoWrite: todas → completed
    └── Exibe: $CAMINHO, arquivos gerados, score, próximos passos
```

**Regra Zero-Read:** O SKILL.md nunca usa Read para verificar existência de arquivos. Toda verificação é via `Bash: test -f` ou `test -d`.

---

## 6. Prós e Contras Comparados ao Design Leve

| Dimensão | Design Leve | Design Robusto |
|----------|-------------|----------------|
| Conformidade v2.7 | Patterns simplificados | Preserva padrão integralmente |
| Custo de criação | Baixo (~150 linhas total) | Alto (~500 linhas: 3 agents + SKILL.md) |
| Manutenção | Simples: 1 arquivo | Complexa: 4 arquivos interdependentes |
| Validação | Manual: usuário verifica | Automática: grep nos sinalizadores |
| Depuração | Difícil: sem sinalização clara | Fácil: orquestrador identifica etapa falha |
| Confiabilidade | Variável: sem contratos formais | Alta: contratos explícitos + retry automático |
| Rastreabilidade | Nenhuma | Completa: TodoWrite + arquivos intermediários |
| Reusabilidade dos agents | Acoplados à skill | Promovíveis para `.claude/agents/[categoria]/` |
| Paralelismo futuro | Não se aplica | Possível em etapas independentes (Agent Teams) |
| Curva de aprendizado | Baixa: similar a skill padrão | Alta: requer domínio do framework v2.7 |

---

## 7. Quando Usar Cada Padrão

### Usar Design Leve quando:

- A skill executa 1-2 etapas simples sem dependências fortes
- Falhas são facilmente detectáveis pelo usuário
- O tempo de implementação é crítico
- Os agents internos são específicos desta skill e não serão reutilizados
- A skill é experimental ou protótipo em desenvolvimento

### Usar Design Robusto quando:

- A skill executa 3+ etapas com dependências sequenciais
- Falhas em uma etapa impedem ou corrompem as etapas seguintes
- Os outputs intermediários têm valor próprio (precisam ser preservados)
- Os agents internos têm capacidade genérica reutilizável
- A skill é crítica para produção e sua falha tem consequências
- Rastreabilidade e auditabilidade são requisitos

### Regra de Decisão Rápida

```
Pergunta 1: O usuário detecta facilmente falhas parciais da skill?
  Não → Design Robusto necessário

Pergunta 2: Existem 3+ etapas com dependências sequenciais?
  Sim → Design Robusto recomendado

Pergunta 3: Os agents internos têm valor fora desta skill específica?
  Sim → Design Robusto (para futura promoção a .claude/agents/)

Se nenhuma das anteriores: Design Leve é suficiente.
```

---

## 8. Tensão Arquitetural Crítica

Uma tensão estrutural existe entre o sistema de skills e o sistema de orquestradores.

**O problema central:** Skills são carregadas no contexto compartilhado via discovery CSO. Orquestradores (commands) têm acesso nativo ao Task tool. O Task tool é semanticamente associado a commands, não a skills.

**A resolução:** O campo `allowed-tools` do SKILL.md inclui `Task`. A skill não "tem" o Task tool de forma autônoma — ela instrui o Claude (no contexto principal) a usar o Task tool que ele já possui.

**Implicação prática:** O design robusto funciona apenas quando ativado em um contexto onde o Claude tem acesso ao Task tool. Dentro de um subagente isolado via `context: fork` ou via Task, o Task tool não está disponível.

**Diferença de invocação:**
- Command: invocado explicitamente via `/criar-skill`; Task é ferramenta nativa
- Skill robusta: ativada via CSO ou Skill tool; usa Task do contexto principal

---

## 9. Referências

- `.claude/spec/templates/agent.md` — Template v2.0 de agent
- `.claude/spec/templates/orquestrador.md` — Template v2.1 de orquestrador
- `.claude/spec/templates/skill.md` — Template de skill
- `.claude/commands/pipeline-sentenca.md` — Exemplo canônico de orquestrador cego
- `.claude/commands/criar-skill.md` — Command atual (v3.0 com TDD e CSO)
- `.claude/spec/README.md` — Documentação completa do framework v2.7
