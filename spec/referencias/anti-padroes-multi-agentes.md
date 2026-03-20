# 7 Anti-Padrões de Sistemas Multi-Agentes

> **Propósito:** Checklist de verificação contra anti-padrões comuns.
>
> **Fonte:** Pesquisa de Arquiteturas Multi-Agentes Hierárquicas (Jan 2026)
>
> **Estatística:** 60-80% dos sistemas multi-agentes falham. 79% dos problemas
> originam-se de especificação e coordenação, não de implementação técnica.

---

## Resumo dos Anti-Padrões

| # | Anti-Padrão | Detecção Rápida |
|---|-------------|-----------------|
| 1 | Ambiguidade de Papel | Agent é "assistente inteligente" genérico |
| 2 | Prompt Emaranhado | Prompt único tenta fazer tudo |
| 3 | Cascata de Erros | Sem validação entre etapas |
| 4 | Memory Mismanagement | Contexto sem estrutura |
| 5 | Complexidade Prematura | Multi-agente para problema simples |
| 6 | Câmara de Eco | Sem diversidade de perspectivas |
| 7 | Falha de Protocolo | Handoffs sem schema estruturado |

---

## 1. Ambiguidade de Papel (Role Ambiguity)

### Sintomas
- Cada agent é "assistente inteligente" capaz de tudo
- Impossível saber qual agent é responsável quando algo falha
- Não há accountability, debugging é puro chute

### Verificação
```
[ ] Agent tem papel claramente definido e DISTINTO de outros?
[ ] Fronteiras funcionais são claras?
[ ] Ferramentas são escopadas ao papel?
```

### Exemplo de Violação
```yaml
# ERRADO
name: smart-assistant
description: "Helps with everything"
tools: Read Write Edit Bash Task WebSearch WebFetch
```

### Correção
```yaml
# CERTO
name: database-migration-specialist
description: "Handles ONLY database schema migrations"
tools: Read Bash  # Only for migration commands
```

---

## 2. Prompt Emaranhado (Prompt Entanglement)

### Sintomas
- Tentar colocar toda instrução em um único prompt enorme
- Prompt inchado, confuso, propenso a erros de interpretação
- Agent não sabe priorizar entre instruções conflitantes

### Verificação
```
[ ] Prompt principal tem menos de 500 linhas?
[ ] Conhecimento extenso está em references/?
[ ] Instruções são separadas em passos claros?
```

### Exemplo de Violação
```markdown
# ERRADO: Prompt de 2000 linhas com tudo junto
Você é um especialista que...
[50 páginas de instruções, regras, exemplos, edge cases]
```

### Correção
```markdown
# CERTO: Separação de concerns
SKILL.md → Instruções principais (<200 linhas)
references/conhecimento-dominio.md → Conhecimento extenso
references/exemplos.md → Exemplos detalhados
```

---

## 3. Cascata de Erros (Error Cascade)

### Sintomas
- Erro pequeno no início se propaga e amplifica
- Uma única alucinação espalha pelo sistema
- Sem pontos de verificação intermediários

### Verificação
```
[ ] Há validação/sinalizadores entre etapas?
[ ] Orquestrador verifica saída antes de passar adiante?
[ ] Há circuit breakers para interromper propagação?
```

### Exemplo de Violação
```markdown
# ERRADO: Encadeamento cego
Task(agent1) → Task(agent2) → Task(agent3) → Task(agent4)
# Se agent1 alucina, todo o resto falha
```

### Correção
```markdown
# CERTO: Validação entre etapas
Task(agent1) → VALIDAR_SINALIZADOR → Task(agent2) → VALIDAR → ...

# Se sinalizador ausente ou formato errado:
# - Interromper pipeline
# - Alertar usuário
# - NÃO continuar com input inválido
```

---

## 4. Memory Mismanagement

### Sintomas
- Agentes armazenam contexto demais
- Compartilham memória sem estrutura
- Operam em sessões desatualizadas
- Alucinações por memória stale

### Verificação
```
[ ] Cada agent tem escopo de contexto claro?
[ ] Estado compartilhado usa chaves únicas?
[ ] Sessões são limpas entre execuções?
```

### Exemplo de Violação
```python
# ERRADO: Estado compartilhado sem estrutura
global_state["data"] = agent1_output  # Sobrescreve
global_state["data"] = agent2_output  # Race condition!
```

### Correção
```python
# CERTO: Chaves únicas, namespace por agent
session.state["agent1_analise_resultado"] = agent1_output
session.state["agent2_pesquisa_resultado"] = agent2_output
# Chaves descritivas, sem colisão
```

---

## 5. Complexidade Multi-Agente Prematura

### Sintomas
- Framework multi-agente para problema simples
- Overhead significativo sem benefício proporcional
- Sistema underperforma alternativa single-agent

### Verificação
```
[ ] Você testou single-agent primeiro?
[ ] Single-agent realmente falhou?
[ ] Benefício de multi-agente justifica custo?
```

### Exemplo de Violação
```markdown
# ERRADO: Pipeline de 5 agents para tarefa simples
/gerar-saudacao:
  Task(analisador-contexto)
  Task(selecionador-estilo)
  Task(gerador-saudacao)
  Task(revisor-gramatical)
  Task(formatador-final)
# Para gerar "Bom dia, João!"
```

### Correção
```markdown
# CERTO: Começar simples
/gerar-saudacao:
  Gerar saudação diretamente (inline)

# Só adicionar complexidade quando:
# - Single-agent falha consistentemente
# - Requisitos são genuinamente complexos
```

---

## 6. Efeito Câmara de Eco (Echo Chamber)

### Sintomas
- Sistemas multi-agentes mimetizam dinâmicas de grupo humanas
- Agentes alinham com a maioria mesmo quando errada
- Soluções alternativas são suprimidas
- Amplificação de viés

### Verificação
```
[ ] Há agent "advogado do diabo" que questiona?
[ ] Perspectivas diversas são buscadas?
[ ] Consenso não é automático?
```

### Exemplo de Violação
```markdown
# ERRADO: Consenso forçado
Task(analisador1) → conclusão A
Task(analisador2) → vê conclusão A, concorda
Task(analisador3) → vê conclusões, concorda também
# Todos convergem para A, mesmo se errado
```

### Correção
```markdown
# CERTO: Diversidade estruturada
Task(analisador1) → conclusão (isolado)
Task(analisador2) → conclusão (isolado)
Task(advogado-diabo) → busca falhas nas conclusões
Task(consolidador) → sintetiza com pesos
```

---

## 7. Falhas de Protocolo de Comunicação

### Sintomas
- Linguagem natural para comunicação entre agents
- Misinterpretação frequente
- Handoffs falham, contexto se perde
- Agents fazem coisas erradas

### Verificação
```
[ ] Comunicação usa schemas estruturados (JSON, XML)?
[ ] Há validação de inputs em cada agent?
[ ] Protocolos de comunicação são explícitos?
```

### Exemplo de Violação
```markdown
# ERRADO: Comunicação em texto livre
Agent1 retorna: "Achei 3 precedentes relevantes sobre pensão..."
Agent2 tenta parsear: ??? (quanto é "3"? Quais?)
```

### Correção
```json
// CERTO: Schema estruturado
{
  "status": "SUCESSO",
  "total_encontrados": 3,
  "precedentes": [
    {"numero": "RE 1234567", "tese": "...", "aplicabilidade": 0.95},
    ...
  ]
}
```

---

## Checklist de Prevenção Consolidado

### Antes de Deploy

```
CLAREZA DE PAPÉIS
[ ] Cada agent tem papel claramente definido e distinto
[ ] Nenhum prompt tenta fazer "tudo"
[ ] Ferramentas são escopadas ao papel

GESTÃO DE CONTEXTO
[ ] Estratégia de memória está estruturada
[ ] Chaves de estado são únicas e descritivas
[ ] Há limpeza de sessão entre execuções

VALIDAÇÃO E RESILIÊNCIA
[ ] Há validação/sinalizadores entre cada etapa
[ ] Circuit breakers previnem cascatas de erro
[ ] Há logging suficiente para debugging

DIVERSIDADE E REVISÃO
[ ] Há mecanismos para diversidade de perspectivas
[ ] Existe "advogado do diabo" ou revisor crítico
[ ] Consenso não é automático

COMUNICAÇÃO
[ ] Comunicação entre agents usa schemas estruturados
[ ] Inputs são validados antes de processamento
[ ] Protocolos de handoff são explícitos

SIMPLICIDADE
[ ] Você começou simples e adicionou complexidade incrementalmente
[ ] Benefício de multi-agente justifica o custo
[ ] Single-agent foi testado primeiro
```

---

## Referências

- Pesquisa de Arquiteturas Multi-Agentes Hierárquicas (Jan 2026)
- Anthropic - Building Effective Agents (2025)
- Playbook de Criação de Agentes e Subagentes

---

**Versão:** 1.0
**Data:** 2026-01-19
