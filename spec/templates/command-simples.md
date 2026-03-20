# Template: Command Simples v1.0

> **Diferença:** Commands simples NÃO são orquestradores de pipeline.
> Executam uma tarefa direta sem múltiplas etapas coordenadas.
>
> **Copie para:** `.claude/commands/[nome-comando].md`

---

## Quando Usar Command Simples vs Orquestrador

| Critério | Command Simples | Orquestrador |
|----------|-----------------|--------------|
| **Etapas** | 1-2 etapas diretas | 3+ etapas coordenadas |
| **Subagentes** | Nenhum ou 1 | Múltiplos via Task tool |
| **Validação** | Mínima | Sinalizadores entre etapas |
| **TodoWrite** | Opcional | Obrigatório |
| **Exemplo** | `/baixar-pje`, `/fork-terminal` | `/pipeline-sentenca` |

---

## Template

```markdown
---
description: [Descrição curta do que o comando faz]
argument-hint: [parametro-esperado]
allowed-tools: [tools necessárias - Read Bash Write etc]
---

# Command: [Nome do Comando]

<identidade>
  <papel>[O que este comando faz]</papel>
</identidade>

<proposito>
  <objetivo>[Objetivo principal]</objetivo>
  <resultado_final>[O que o usuário obtém ao final]</resultado_final>
</proposito>

<restricoes>
  - NUNCA [restrição importante]
  - SEMPRE [obrigação importante]
</restricoes>

<contingencias>
  <se_falhar>[O que fazer se der erro]</se_falhar>
</contingencias>

<instrucoes>
  <passo numero="1" nome="[Nome do passo]">
    [Descrição do que fazer]
  </passo>

  <passo numero="2" nome="[Nome do passo]">
    [Descrição do que fazer]
  </passo>

  <!-- Máximo recomendado: 3-4 passos -->
</instrucoes>

<finalizacao>
  Exibir ao usuário:
  - [O que foi feito]
  - [Onde encontrar o resultado]
</finalizacao>
```

---

## Exemplos de Commands Simples

### Exemplo 1: Ativador de Skill

```markdown
---
description: Consultor de implementação - ajuda a decidir qual artefato criar
argument-hint: (nenhum)
allowed-tools: Read
---

# Command: Consultor de Implementação

<identidade>
  <papel>Ativador da skill consultor-implementacao</papel>
</identidade>

<proposito>
  <objetivo>Ajudar o usuário a decidir entre Script, Skill, Agent ou Workflow</objetivo>
  <resultado_final>Recomendação fundamentada do tipo de artefato a criar</resultado_final>
</proposito>

<instrucoes>
  <passo numero="1" nome="Carregar skill">
    Read: .claude/skills/consultor-implementacao/SKILL.md
    → Seguir as instruções da skill carregada
  </passo>
</instrucoes>
```

### Exemplo 2: Utilitário de Sistema

```markdown
---
description: Abre múltiplas abas no Windows Terminal para execução paralela
argument-hint: quantidade-de-abas
allowed-tools: Bash
---

# Command: Fork Terminal

<identidade>
  <papel>Paralelizador de sessões Claude Code</papel>
</identidade>

<proposito>
  <objetivo>Abrir N abas do Windows Terminal para trabalho paralelo</objetivo>
  <resultado_final>N abas abertas com Claude Code pronto para uso</resultado_final>
</proposito>

<restricoes>
  - NUNCA abrir mais de 10 abas (limite de recursos)
  - SEMPRE usar Windows Terminal (não CMD ou PowerShell puro)
</restricoes>

<contingencias>
  <se_nao_windows>
    Informar que este comando só funciona no Windows Terminal
  </se_nao_windows>
</contingencias>

<instrucoes>
  <passo numero="1" nome="Validar argumento">
    Se $ARGUMENTS vazio ou > 10 → pedir quantidade válida
  </passo>

  <passo numero="2" nome="Executar script">
    Bash: wt -w 0 nt -d . -- claude [repetir N vezes]
  </passo>
</instrucoes>

<finalizacao>
  Informar: "Abertas [N] abas no Windows Terminal."
</finalizacao>
```

---

## Checklist de Validação

```
YAML:
[ ] description clara e concisa?
[ ] argument-hint indica o que espera?
[ ] allowed-tools lista apenas o necessário?

Estrutura:
[ ] Máximo 4 passos em <instrucoes>?
[ ] Não usa Task tool (ou usa no máximo 1)?
[ ] Não tem <contratos_dados> complexos?
[ ] Não tem <sinalizadores_formato>?

Diferenciação:
[ ] Realmente não precisa ser um orquestrador?
[ ] Não coordena múltiplos subagentes?
```

---

## Quando Promover para Orquestrador

Se durante o uso você perceber que o command precisa de:
- 3+ etapas com validação entre elas
- Múltiplos subagentes especializados
- Rastreamento de progresso via TodoWrite
- Sinalizadores de formato obrigatórios

...então promova para orquestrador usando o template `orquestrador.md`.

---

**Template:** Command Simples
**Versão:** 1.0
**Data:** 2026-01-20
