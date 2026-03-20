# SPEC v2.10: Agent Teams com Debate Real

> **Versão:** 2.10
> **Data:** 2026-02-07
> **Autor:** SuperJurista Framework
> **Base:** Documentação oficial Claude Code Agent Teams
> **Requer:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS: "1"`
> **Changelog:** Correções baseadas em análise comparativa com doc oficial

---

## Mudança em Relação à v2.8

| Aspecto | v2.8 (Subagents) | v2.10 (Agent Teams) |
|---------|------------------|---------------------|
| Comunicação | Arquivos | Sistema de mensagens direto |
| Debate | Não há | Teammates desafiam uns aos outros (requer instrução) |
| Coordenação | Orquestrador dispara Tasks | Lead spawna teammates |
| Task list | TodoWrite no orquestrador | Task list compartilhada com file locking |
| Feature | Funciona hoje | Requer flag experimental |

---

## Visão Geral

Agent Teams são **sessões Claude Code independentes** que trabalham juntas, coordenadas por um **lead**. Diferente de subagents (que reportam apenas ao caller), teammates podem:

- **Trocar mensagens diretamente** entre si
- **Desafiar** as conclusões uns dos outros (quando instruídos)
- **Convergir** para uma solução através de debate

```
┌──────────────────────────────────────────────────────────────────────┐
│  AGENT TEAMS v2.10                                                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                        ┌─────────┐                                   │
│                        │  LEAD   │                                   │
│                        │(coordena)│                                  │
│                        └────┬────┘                                   │
│               ┌─────────────┼─────────────┐                          │
│               ▼             ▼             ▼                          │
│          ┌────────┐    ┌────────┐    ┌────────┐                      │
│          │TEAMMATE│◄──►│TEAMMATE│◄──►│TEAMMATE│                      │
│          │   A    │    │   B    │    │   C    │                      │
│          └────────┘    └────────┘    └────────┘                      │
│               │             │             │                          │
│               └─────────────┴─────────────┘                          │
│                   MENSAGENS DIRETAS                                  │
│                                                                      │
│          Teammates trocam mensagens, desafiam, convergem             │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Dois Mecanismos Distintos

| Coordenação de TRABALHO | Comunicação de INFORMAÇÃO |
|-------------------------|---------------------------|
| Task list compartilhada | Mensagens diretas |
| pending → in_progress → completed | message (1:1) / broadcast (1:N) |
| `blockedBy` para dependências | Debate, críticas, findings |
| Quem faz o quê | O que descobriram |

---

## Pré-requisitos

### 1. Habilitar Feature Experimental

```json
// ~/.claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### 2. Reiniciar Claude Code

A configuração só tem efeito após reiniciar a sessão.

### 3. (Opcional) Configurar Display Mode

```json
// ~/.claude/settings.json
{
  "teammateMode": "auto"  // "auto" (padrão) | "in-process" | "tmux"
}
```

**Valores:**
- **auto** (padrão): usa split panes se já está em tmux, senão in-process
- **in-process**: todos no mesmo terminal (Shift+Up/Down para navegar)
- **tmux**: split panes (auto-detecta tmux ou iTerm2)

**Para forçar modo em uma sessão:**
```bash
claude --teammate-mode in-process
```

---

## Arquitetura

### Componentes

| Componente | Papel |
|------------|-------|
| **Lead** | Sessão principal que cria o team, spawna teammates, coordena trabalho |
| **Teammates** | Sessões Claude Code independentes com contexto próprio |
| **Task List** | Lista compartilhada de tarefas com file locking para evitar race conditions |
| **Sistema de Mensagens** | Comunicação direta entre agents (message ou broadcast) |

### Armazenamento Local

```
~/.claude/
├── teams/{team-name}/
│   └── config.json      # Configuração do team (members, IDs, tipos)
├── tasks/{team-name}/
│   └── {task-id}.json   # Tasks individuais
└── settings.json        # Feature flag e configurações
```

**Nota:** Estruturas internas podem mudar entre versões. Não dependa de caminhos específicos.

### Contexto dos Teammates

Quando spawnado, um teammate **HERDA**:
- CLAUDE.md do diretório de trabalho
- MCP servers configurados
- Skills disponíveis
- Permissões do lead (ver seção Permissões)

Um teammate **NÃO HERDA**:
- Histórico de conversa do lead
- Contexto específico da sessão do lead

**Importante:** O CLAUDE.md faz trabalho pesado para teammates. Mantenha-o sólido.

---

## Permissões

- Teammates **herdam** as permissões do lead no momento do spawn
- Se o lead usa `--dangerously-skip-permissions`, todos os teammates também usam
- Você **pode** mudar permissões de teammates individuais **após** o spawn
- Você **não pode** definir permissões diferentes no momento do spawn

**Dica:** Pré-aprove operações comuns em suas configurações de permissão antes de spawnar teammates para reduzir interrupções.

---

## Quando Usar Agent Teams

### Casos Ideais

| Cenário | Por que funciona |
|---------|------------------|
| **Pesquisa e revisão** | Múltiplos investigam, depois desafiam achados |
| **Debugging com hipóteses** | Cada um testa teoria diferente, debate qual é correta |
| **Criação com múltiplas perspectivas** | Cada um propõe, outros criticam, convergem |
| **Revisão de código** | Segurança, performance, testes - cada um com lente diferente |
| **Novos módulos/features** | Cada um é dono de uma peça sem pisarem uns nos outros |

### Quando NÃO Usar

| Cenário | Alternativa |
|---------|-------------|
| Tarefas sequenciais | Subagents (v2.8) |
| Mesmo arquivo sendo editado | Subagent único |
| Tarefa simples | Sessão única |
| Muitas dependências | Pipeline sequencial |
| Custo importa muito | Sessão única (teams usam mais tokens) |

---

## Criando um Agent Team

### Via Linguagem Natural

Simplesmente peça ao Claude para criar um team:

```
Crie um agent team com 3 teammates para desenvolver nome e slogan:
- Um focado em VALOR (perspectiva de ofertas)
- Um focado em DISTRIBUIÇÃO (perspectiva de aquisição)
- Um focado em COMUNICAÇÃO (perspectiva criativa)

Peça que debatam entre si e desafiem as propostas uns dos outros,
como um debate científico. O objetivo é convergir para a melhor opção.
```

### Claude Pode Propor um Team

Se Claude determinar que sua tarefa se beneficiaria de trabalho paralelo, ele pode **sugerir** criar um team. Você confirma antes de prosseguir.

### Especificar Modelo por Teammate

Para economizar tokens, use modelos mais leves:

```
Crie um team com 4 teammates para refatorar esses módulos em paralelo.
Use Sonnet para cada teammate.
```

### O que o Lead faz automaticamente:

1. Cria o team com task list compartilhada
2. Spawna cada teammate com prompt específico
3. Teammates trabalham e trocam mensagens
4. Lead sintetiza resultados quando convergem
5. Limpa o team ao finalizar

---

## Tamanho Ideal de Tasks

| Muito pequena | Muito grande | Ideal |
|---------------|--------------|-------|
| Overhead de coordenação maior que benefício | Teammates trabalham muito tempo sem check-in | Unidades auto-contidas com entregável claro |

**Recomendação:** 5-6 tasks por teammate mantém todos produtivos e permite reatribuição se alguém travar.

Se o lead não está criando tasks suficientes:
```
Divida o trabalho em peças menores
```

---

## Padrões de Implementação

### Pattern 1: Debate Científico

Ideal para quando há múltiplas hipóteses ou abordagens.

```
Crie um agent team para investigar [problema].
Spawn 3-5 teammates, cada um com uma hipótese diferente.
Peça que tentem REFUTAR as hipóteses uns dos outros,
como um debate científico. Atualize [documento] com
o consenso que emergir.
```

**Por que funciona:** Um único agent tende a encontrar uma explicação plausível e parar. Múltiplos investigadores tentando refutar uns aos outros = teoria sobrevivente é mais provável de ser correta.

### Pattern 2: Revisão Multi-Perspectiva

Ideal para revisão de código, documentos ou estratégias.

```
Crie um agent team para revisar PR #142.
Spawn 3 reviewers:
- Um focado em segurança
- Um focado em performance
- Um focado em cobertura de testes

Cada um revisa e reporta. Depois sintetize os findings.
```

### Pattern 3: Criação Colaborativa com Crítica

Ideal para brainstorming com qualidade.

```
Crie um agent team para criar [deliverable].
Spawn 3 teammates com perspectivas complementares.
Primeiro, cada um propõe independentemente.
Depois, cada um critica as propostas dos outros.
Por fim, refinam baseado nas críticas.
```

**Importante sobre Debate:** Teammates NÃO debatem automaticamente. Você precisa instruir explicitamente:
- "Tentem refutar as teorias uns dos outros"
- "Critiquem as propostas"
- "Desafiem as conclusões"

---

## Controlando o Team

### Navegar entre Teammates (in-process mode)

| Ação | Comando |
|------|---------|
| Selecionar teammate | Shift+Up/Down |
| Ver sessão do teammate | Enter |
| Interromper turno | Escape |
| Toggle task list | Ctrl+T |

### Mensagens Diretas

Você pode falar diretamente com qualquer teammate:
1. Shift+Up/Down para selecionar
2. Digite a mensagem
3. Enter para enviar

### Delegate Mode

Se o lead começar a fazer tarefas em vez de delegar:

```
Shift+Tab  (para entrar em delegate mode)
```

Isso restringe o lead a apenas coordenar, não implementar.

### Exigir Aprovação de Plano

Para tarefas complexas ou arriscadas:

```
Spawn um teammate para refatorar o módulo de autenticação.
Exija aprovação do plano antes de fazer mudanças.
```

**Fluxo:**
1. Teammate trabalha em **read-only plan mode**
2. Envia **plan approval request** ao lead
3. Lead revisa e **aprova** ou **rejeita com feedback**
4. Se rejeitado: teammate revisa e reenvia
5. Se aprovado: teammate sai do plan mode e implementa

**Influencie o critério do lead:**
```
"Apenas aprove planos que incluam cobertura de testes"
"Rejeite planos que modifiquem o schema do banco"
```

---

## Comunicação entre Teammates

### Tipos de Mensagem

| Tipo | Uso | Custo |
|------|-----|-------|
| **message** | Enviar para 1 teammate específico | Normal |
| **broadcast** | Enviar para TODOS | ⚠️ Escala com tamanho do team |

**Aviso:** Use broadcast com moderação. Custo de tokens escala com número de teammates.

### Fluxo Automático

- Mensagens são entregues automaticamente aos destinatários
- Quando teammate termina, notifica o lead automaticamente
- Lead não precisa fazer polling

### Task List Compartilhada

Estados de task:
- **pending**: Aguardando
- **in_progress**: Sendo trabalhada (com file locking)
- **completed**: Finalizada

Tasks podem ter dependências. Task bloqueada só desbloqueia quando dependência completa.

**Claim de tasks:** File locking previne race conditions quando múltiplos teammates tentam claim simultâneo.

---

## Quality Gates com Hooks

### TeammateIdle Hook

Roda quando teammate está prestes a ficar idle.
Exit code 2 = feedback para continuar trabalhando.

```json
{
  "hooks": {
    "TeammateIdle": [
      {
        "type": "command",
        "command": "python validate_teammate_output.py"
      }
    ]
  }
}
```

### TaskCompleted Hook

Roda quando task está sendo marcada completa.
Exit code 2 = impede completion, envia feedback.

---

## Encerrando o Team

### Shutdown Graceful

```
Peça ao teammate [nome] para encerrar
```

O teammate pode aprovar (sai) ou rejeitar (explica por quê).

### Cleanup Final

```
Limpe o team
```

**IMPORTANTE:**
- Sempre use o lead para cleanup
- Teammates não devem fazer cleanup (contexto pode não resolver corretamente)
- Lead verifica se há teammates ativos antes de cleanup
- Encerre teammates antes de cleanup

---

## Troubleshooting

### Teammates não aparecem

- Em in-process mode, podem estar rodando mas não visíveis. Pressione Shift+Down.
- Verifique se a tarefa era complexa o suficiente para justificar um team.
- Para split panes, verifique se tmux está instalado: `which tmux`
- Para iTerm2, verifique se `it2` CLI está instalado e Python API habilitada.

### Muitos prompts de permissão

Pré-aprove operações comuns nas configurações de permissão antes de spawnar teammates.

### Teammates param em erros

Verifique output via Shift+Up/Down, depois:
- Dê instruções adicionais diretamente, ou
- Spawne um replacement para continuar

### Lead encerra antes de terminar

Diga ao lead:
```
Espere os teammates terminarem antes de prosseguir
```

### Sessões tmux órfãs

```bash
tmux ls
tmux kill-session -t <session-name>
```

---

## Limitações Conhecidas

| Limitação | Workaround |
|-----------|------------|
| Sem resumption de teammates | Após /resume, spawnar novos |
| Task status pode atrasar | Verificar manualmente se stuck |
| Shutdown pode ser lento | Aguardar turno atual terminar |
| 1 team por sessão | Cleanup antes de novo team |
| Sem teams aninhados | Apenas lead gerencia team |
| Lead é fixo | Não há promoção de teammate |
| Permissões no spawn | Todas iguais ao lead; mudar depois |
| Split panes requer tmux/iTerm2 | Usar in-process no Windows/VS Code/Ghostty |

---

## Exemplo Completo: Team Hormozi para Nome/Slogan

### Prompt para o Lead

```
Crie um agent team com 3 teammates para desenvolver nome e slogan
para um curso de sistemas agênticos com Claude Code.

CONTEXTO DO CURSO:
- Público: profissionais de alta performance cognitiva
- Foco: produção epistêmica com múltiplos agentes
- Diferencial: qualidade cognitiva, não só escala

TEAMMATES:
1. HORMOZI-OFFERS: Especialista em valor e posicionamento
   - Avalia pelo critério: "Por que alguém pagaria por isso?"
   - Foco em dream outcome e diferenciação

2. HORMOZI-LEADS: Especialista em aquisição e distribuição
   - Avalia pelo critério: "Isso escala? É compartilhável?"
   - Foco em viralidade, SEO, canais

3. HORMOZI-CONTENT: Especialista em comunicação e criatividade
   - Avalia pelo critério: "Isso captura atenção? Emociona?"
   - Foco em hooks, ritmo, storytelling

PROCESSO:
1. Cada teammate propõe 5 nomes com slogans
2. Cada um LÊ as propostas dos outros e CRITICA
3. Debate: desafiem as propostas, apontem falhas
4. Convergência: qual nome sobrevive ao escrutínio?
5. Lead sintetiza a recomendação final

O objetivo é que o DEBATE entre perspectivas diferentes
produza uma recomendação mais robusta do que cada um sozinho.
```

### O que deve acontecer:

1. Lead spawna 3 teammates
2. Cada um recebe seu prompt de especialização
3. Produzem propostas independentes
4. Trocam mensagens criticando uns aos outros
5. Refinam baseado nas críticas
6. Lead identifica convergência
7. Sintetiza recomendação final

---

## Checklist de Conformidade v2.10

| # | Item | Pts |
|---|------|-----|
| 1 | Feature experimental habilitada | 10 |
| 2 | Teammates têm perspectivas DISTINTAS | 15 |
| 3 | Prompt inclui instrução EXPLÍCITA para debater | 15 |
| 4 | Lead coordena, não executa (delegate mode se necessário) | 10 |
| 5 | Task list usada para coordenação de TRABALHO | 10 |
| 6 | Mensagens usadas para comunicação de INFORMAÇÃO | 10 |
| 7 | Lead espera teammates terminarem | 10 |
| 8 | Cleanup executado pelo lead | 5 |
| 9 | Síntese final reflete debate | 10 |
| 10 | CLAUDE.md sólido para teammates herdarem | 5 |
|   | **TOTAL** | **100** |

**Score mínimo exigido:** 80 pontos (80%)

---

## Comparação: v2.8 vs v2.10

| Critério | v2.8 (Subagents) | v2.10 (Agent Teams) |
|----------|------------------|---------------------|
| Setup | Nenhum | Requer flag experimental |
| Complexidade | Baixa | Média |
| Tokens | Menor | Maior (cada teammate = instância separada) |
| Debate real | Não | Sim (com instrução explícita) |
| Comunicação entre agents | Via arquivos | Via mensagens diretas |
| Melhor para | Tarefas paralelas independentes | Tarefas que requerem debate |
| Rastreabilidade | Arquivos persistem | Mensagens na sessão |
| Contexto | Compartilha com main | Cada um isolado |

### Quando usar cada um:

- **v2.8**: Pesquisas paralelas, verificações independentes, pipeline com consolidação, custo importa
- **v2.10**: Brainstorming criativo, debate de hipóteses, revisão com desafio mútuo

---

## Referências

### Documentação Oficial
- https://code.claude.com/docs/en/agent-teams

### Citações-Chave

> "Teammates message each other directly"

> "Multiple teammates can investigate different aspects of a problem
> simultaneously, then share and challenge each other's findings"

> "Have them talk to each other to try to disprove each other's theories,
> like a scientific debate"

> "Agent teams add coordination overhead and use significantly more tokens
> than a single session. They work best when teammates can operate independently."

---

## Changelog

### v2.10 (2026-02-07)
- **Corrigido:** Adicionado `"auto"` como valor padrão de teammateMode
- **Corrigido:** Sintaxe do comando `--teammate-mode`
- **Corrigido:** Removida referência a estrutura interna de inbox
- **Adicionado:** Seção de Permissões
- **Adicionado:** Seção de Plan Approval
- **Adicionado:** Seção de Troubleshooting
- **Adicionado:** Especificar modelo por teammate
- **Adicionado:** Tamanho ideal de tasks (5-6 por teammate)
- **Adicionado:** Claude pode propor team automaticamente
- **Adicionado:** Contexto herdado vs não herdado
- **Adicionado:** Warning sobre custo de broadcast
- **Clarificado:** Debate requer instrução explícita
- **Clarificado:** Separação entre tasks (trabalho) e mensagens (informação)

### v2.9 (2026-02-07)
- Versão inicial baseada em documentação e vídeos

---

**Framework:** Super Jurista
**Versão:** 2.10
**Data:** 2026-02-07
