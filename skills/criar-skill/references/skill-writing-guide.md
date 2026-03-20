# Guia de Escrita de Skills

> Referência detalhada para o agent brainstormer e para uso direto durante a fase de implementação.
> Carregado sob demanda (progressive disclosure nível 3).

---

## Princípios de CSO (Claude Search Optimization)

### A description é o mecanismo de discovery

A `description` no YAML frontmatter é o que determina se Claude encontra e ativa a skill.
Funciona como SEO para skills: se as keywords não estão lá, a skill não ativa.

### Regras da description

1. **DEVE começar com "Use when..."**
   - Estabelece imediatamente QUANDO ativar
   - Claude usa a description para decidir se carrega o corpo

2. **DEVE listar apenas GATILHOS**
   - Sintomas, cenários, palavras-chave do usuário
   - NUNCA resumir o workflow da skill

3. **NUNCA resumir o workflow**
   - Testes mostram que quando a description resume o workflow,
     Claude segue a description em vez de ler o conteúdo completo
   - Uma description que diz "code review" faz Claude rodar UMA revisão,
     mesmo que a skill defina DUAS

4. **Incluir variações e sinônimos**
   - "criar skill" + "nova skill" + "automatizar" + "skill creator"

### Exemplos

```yaml
# RUIM (resume workflow)
description: "Executes plans by dispatching subagents with code review between tasks"
# → Claude faz UMA revisão porque description diz "code review"

# BOM (apenas gatilhos)
description: "Use when executing implementation plans with independent tasks"
# → Claude lê a skill completa e descobre que são DUAS revisões
```

---

## Tipos de Skill

| Tipo | Característica | TDD? | Template |
|------|---------------|------|----------|
| **Disciplina** | Impõe regras com custo de seguir | SIM | Padrão + racionalizações |
| **Técnica** | Método concreto com passos | SIM | Padrão |
| **Padrão** | Modelo mental para decisão | SIM | Padrão |
| **Referência** | Documentação, sintaxe | NÃO | Padrão ou Fork |

### Como identificar tipo Disciplina

Uma skill é de Disciplina quando:
- Impõe regras que **contradizem** objetivos imediatos
- O agente tem incentivo para **racionalizar** a violação
- Exemplos: TDD ("o prazo não permite"), code review ("é trivial"), testes ("já testei mentalmente")

Skills de Disciplina PRECISAM de:
- Tabela `<racionalizacoes>` com desculpas reais (do teste RED)
- `<red_flags>` com pensamentos que sinalizam tentação
- Cenário de teste com 3+ pressões combinadas

---

## TDD para Skills

### Ciclo RED → GREEN → REFACTOR

| Fase | Objetivo | Resultado |
|------|----------|-----------|
| **RED** | Provar que SEM a skill, agente viola | Documentar falha e racionalização |
| **GREEN** | Provar que COM a skill, agente cumpre | Verificar compliance |
| **REFACTOR** | Fechar brechas sob pressão máxima | Skill blindada |

### Pressões para cenário de teste

| Pressão | Exemplo |
|---------|---------|
| **Tempo** | "Cliente esperando resposta urgente" |
| **Autoridade** | "Tech lead disse para pular esse passo" |
| **Custo afundado** | "Já gastamos 40 min nessa abordagem" |
| **Pragmatismo** | "Funciona no meu ambiente, deploy rápido" |
| **Exaustão** | "12 horas de debug, só quero terminar" |

Combinar **3 ou mais** pressões para cenário eficaz.

### Capturando racionalizações

Na fase RED, capturar VERBATIM:
- Qual opção o agente escolheu
- Qual justificativa deu
- Quais desculpas usou

Essas desculpas viram entradas na tabela `<racionalizacoes>`:

```xml
<racionalizacoes>
  | Desculpa | Por Que Errada | Resposta Correta |
  |----------|----------------|------------------|
  | "[texto exato do agente]" | [explicação] | [correção] |
</racionalizacoes>
```

---

## Isolamento de Contexto (context: fork)

### Quando usar fork

| Característica | Fork? | Motivo |
|----------------|-------|--------|
| Executa scripts Python/Bash | SIM | Output verboso polui contexto |
| Apenas conhecimento/regras | NÃO | Sem execução |
| Processamento de lote | SIM | Muito output acumulado |
| Múltiplas tentativas/retry | SIM | Isolamento de falhas |
| Tarefa rápida (<10 linhas) | NÃO | Overhead desnecessário |

### Padrão imperativo (skill com fork)

```yaml
---
name: nome-skill
description: Use when [gatilhos]. Keywords: [palavras].
context: fork
agent: general-purpose
allowed-tools: Bash Read Write
---

REGRA ABSOLUTA: Execute os scripts existentes. NAO crie codigo novo.

## Scripts Disponíveis
| Script | Comando |
|--------|---------|
| [nome] | `python .claude/skills/$NOME/scripts/[script].py` |

## Retorno Esperado
Retorne APENAS: status, caminhos, estatísticas.
NAO inclua: output completo dos scripts, logs detalhados.
```

---

## Progressive Disclosure

```
Nível 1: METADATA (~100 tokens)
└─ Carregado no STARTUP
└─ Campos: name, description

Nível 2: SKILL.md (<5000 tokens recomendado)
└─ Carregado quando ATIVADO
└─ Instruções principais, exemplos essenciais

Nível 3: references/ (sob demanda)
└─ Carregado quando NECESSÁRIO
└─ Documentação técnica detalhada
```

### Regra do SKILL.md < 500 linhas

Se ultrapassar:
1. Mover conhecimento de domínio para `references/`
2. Mover exemplos extensos para `references/exemplos.md`
3. Manter apenas instruções essenciais no SKILL.md
4. Referenciar: "Para detalhes, veja references/X.md"

---

## Estilo de Escrita

### Filosofia "Explain the Why"

Em vez de apenas imperativos, explique o raciocínio:

```xml
<!-- ANTES (imperativo puro) -->
<restricoes>
  - NUNCA resumir workflow na description
</restricoes>

<!-- DEPOIS (com explain the why) -->
<restricoes>
  - NUNCA resumir workflow na description
    **Por quê:** Testes mostram que Claude segue a description em vez
    de ler o conteúdo completo. Description com "code review" faz
    Claude rodar UMA revisão, mesmo que a skill defina DUAS.
</restricoes>
```

**Por que isso importa:** Modelos de linguagem são inteligentes.
Quando entendem o MOTIVO de uma regra, aplicam-na melhor em edge cases
que o criador da skill não previu. Um MUST sem explicação é frágil;
uma regra com raciocínio é robusta.

### Quando usar imperativo puro vs "explain the why"

| Situação | Estilo |
|----------|--------|
| Restrição de segurança (credenciais, secrets) | Imperativo puro |
| Restrição de design (sinalizadores, formato) | "Explain the why" |
| Instrução de processo (passos de workflow) | "Explain the why" |
| Convenção trivial (kebab-case) | Imperativo puro |

---

## Anti-Patterns

| Anti-Padrão | Problema | Correção |
|-------------|----------|----------|
| Description resume workflow | Claude segue description, não lê skill | Usar apenas gatilhos |
| Skill sem teste RED | Não sabe se ensina certo | Testar antes de escrever |
| Pressão única no teste | Muito fácil de passar | Combinar 3+ pressões |
| Racionalizações genéricas | Não fecha brechas reais | Usar texto verbatim do teste |
| SKILL.md > 500 linhas | Muito contexto | Mover para references/ |
| Labels vagos | "Processar" não diz nada | Usar verbos específicos |
| Script sem fork | Output verboso polui contexto | Adicionar context: fork |
| Fork com instruções ricas | Modelo se perde | Usar padrão imperativo |
| MUST/NEVER sem explicação | Regra frágil em edge cases | Adicionar "Por quê" |

---

## Checklist Rápido de Qualidade

```
CSO:
[ ] Description começa com "Use when..."
[ ] Description lista GATILHOS, não workflow
[ ] Keywords incluídas (sintomas, erros, sinônimos)
[ ] Tag <quando_usar> com gatilhos e exclusões

TDD (se não for referência):
[ ] Fase RED executada (falha documentada)
[ ] Fase GREEN executada (compliance verificado)
[ ] Cenário com 3+ pressões combinadas
[ ] Racionalizações capturadas verbatim

Estrutura:
[ ] .claude/skills/[name]/SKILL.md
[ ] Nome pasta = campo name do YAML
[ ] SKILL.md < 500 linhas
[ ] Progressive disclosure (references/ se necessário)

Conteúdo:
[ ] <proposito> com objetivo + razão
[ ] <instrucoes> com passos numerados
[ ] <restricoes> com "explain the why"
[ ] ZERO caminhos hardcoded
[ ] ZERO credenciais
```
