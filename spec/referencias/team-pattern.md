# SPEC v2.8: Padrão de Agent Teams

> **Versão:** 2.8
> **Data:** 2026-02-07
> **Autor:** SuperJurista Framework
> **Base:** Lições do Compilador C Anthropic + Claude Code Agent Teams

---

## Visão Geral

**Agent Teams** são grupos de agents que executam em **paralelo** e comunicam-se via **arquivos de domínio**. Diferente de subagentes sequenciais, teammates trabalham simultaneamente com contexto compartilhado.

```
┌──────────────────────────────────────────────────────────────────────┐
│  AGENT TEAMS vs SUBAGENTES                                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  SUBAGENTES (pipeline sequencial):                                  │
│  Agent A → Agent B → Agent C → Agent D                              │
│  (cada um depende do anterior)                                       │
│                                                                      │
│  AGENT TEAM (execução paralela):                                    │
│  ┌─── Agent A ───┐                                                  │
│  ├─── Agent B ───┼─── Consolidador ─── Agent Downstream            │
│  └─── Agent C ───┘                                                  │
│  (executam simultaneamente, consolidam depois)                       │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Princípios Fundamentais

### 1. Comunicação via Arquivos de Domínio

Agents não compartilham variáveis globais. Toda comunicação é via arquivos estruturados.

```
CORRETO:
Agent A → escreve → arquivo-a.md
Agent B → lê → arquivo-a.md

INCORRETO:
Agent A → global_state["resultado"] → Agent B
```

**Razão:** Arquivos são rastreáveis, debugáveis, persistentes.

### 2. Papéis Distintos sem Sobreposição

Cada teammate tem **expertise única**. Nenhum teammate faz o trabalho de outro.

```
CORRETO:
- pesquisador-bnp: SOMENTE pesquisa no BNP
- pesquisador-cjf: SOMENTE pesquisa no CJF
- verificador-honorarios: SOMENTE verifica honorários

INCORRETO:
- pesquisador-geral: pesquisa em todas as fontes
- verificador-geral: verifica tudo
```

**Razão:** Especialização permite paralelização e debugging preciso.

### 3. Entradas Opcionais no Downstream

Agents downstream devem funcionar **com ou sem** inputs dos teammates.

```xml
<contrato>
  <entrada>
    <requisitos>
      OBRIGATÓRIO: relatorio.md (sempre presente)
      OPCIONAL: $INPUTS/pesquisa-*.md (se disponível, enriquece análise)
    </requisitos>
  </entrada>
</contrato>
```

**Razão:** Graceful degradation - pipeline não quebra se um teammate falhar.

### 4. Verificadores Quase Perfeitos

Antes de prosseguir, validar que outputs existem e têm sinalizadores corretos.

```
VALIDAÇÃO:
1. Arquivo existe? (ls $INPUTS/*.md)
2. Sinalizador início presente? (grep "^# Relatório")
3. Sinalizador fim presente? (grep "concluída.$")
```

**Razão:** Erros precoces são mais baratos que cascatas de falhas.

---

## Anatomia de um Agent Team

### Estrutura de Diretórios

```
data/sentenca/<numero>/
├── processo.txt              # Entrada original
├── _team_manifest.md         # Registro compartilhado do time
├── <numero>-linha-tempo.md   # Etapas sequenciais
├── <numero>-relatorio.md
├── <numero>-analise.md       # Recebe inputs opcionais de pesquisa
├── <numero>-fundamentacao.md # Recebe inputs opcionais de verificação
├── <numero>-sentenca.md      # Output final
│
└── inputs/                   # Pasta para outputs dos teams
    ├── pesquisa-bnp.md       # TEAM Pesquisa
    ├── pesquisa-cjf.md
    ├── pesquisa-julia.md
    ├── verificacao-honorarios.md  # TEAM Verificação
    ├── verificacao-calculos.md
    └── verificacao-remessa.md
```

### Team Manifest (_team_manifest.md)

Registro compartilhado que tracking status de cada teammate.

```markdown
# Team Manifest: Processo 0814624-28.2019.4.05.8100

## Metadata
- Pipeline: pipeline-sentenca-team
- Iniciado: 2026-02-07T10:30:00
- Status: em_andamento

## Teams Executados

### TEAM Pesquisa (Etapa 2.5)
| Teammate | Status | Output | Timestamp |
|----------|--------|--------|-----------|
| pesquisador-bnp | concluído | inputs/pesquisa-bnp.md | 10:31:22 |
| pesquisador-cjf | concluído | inputs/pesquisa-cjf.md | 10:31:45 |
| pesquisador-julia | erro | - | 10:32:10 |

### TEAM Verificação (Etapa 3.5)
| Teammate | Status | Output | Timestamp |
|----------|--------|--------|-----------|
| verificador-honorarios | pendente | - | - |
| verificador-calculos | pendente | - | - |
| verificador-remessa | pendente | - | - |

## Artefatos Disponíveis

- [x] processo.txt
- [x] linha-tempo.md
- [x] relatorio.md
- [x] inputs/pesquisa-bnp.md
- [x] inputs/pesquisa-cjf.md
- [ ] inputs/pesquisa-julia.md (falhou)
- [ ] analise.md (pendente)

## Alertas

- pesquisador-julia: MCP não respondeu após 2 tentativas
- Análise prosseguirá com 2/3 pesquisas disponíveis
```

---

## Padrões de Implementação

### Pattern 1: Etapa Paralela no Orquestrador

O orquestrador dispara múltiplas Tasks **no mesmo turno**.

```xml
<etapa numero="2.5" nome="TEAM Pesquisa" modo="paralelo">
  <acao_orquestrador>
    1. Atualizar TodoWrite: TEAM Pesquisa = in_progress

    2. Disparar 3 Tasks NO MESMO TURNO:
       ```
       Task 1: pesquisador-bnp → $INPUTS/pesquisa-bnp.md
       Task 2: pesquisador-cjf → $INPUTS/pesquisa-cjf.md
       Task 3: pesquisador-julia → $INPUTS/pesquisa-julia.md
       ```

    3. Aguardar TODAS concluírem

    4. Validar: ls $INPUTS/pesquisa-*.md

    5. Atualizar _team_manifest.md com status de cada teammate

    6. Atualizar TodoWrite: TEAM Pesquisa = completed
  </acao_orquestrador>

  <validacao>
    | # | Verificação | Se Falhar |
    |---|-------------|-----------|
    | 1 | Pelo menos 1 arquivo existe | PARAR (team inteiro falhou) |
    | 2 | Sinalizadores presentes | AVISO (prosseguir com o que tem) |
  </validacao>
</etapa>
```

### Pattern 2: Leitura Opcional no Agent Downstream

Agent downstream lê manifest para descobrir inputs disponíveis.

```xml
<instrucoes>
  <passo numero="1" nome="Ler entradas obrigatórias">
    Read: $WORKSPACE/relatorio.md
  </passo>

  <passo numero="2" nome="Descobrir inputs opcionais">
    Verificar se existem arquivos em $WORKSPACE/inputs/pesquisa-*.md

    SE existirem:
      Para cada arquivo encontrado:
        - Read: $WORKSPACE/inputs/<arquivo>
        - Extrair precedentes vinculantes
        - Incorporar na análise

    SE NÃO existirem:
      - Registrar: "Análise sem enriquecimento de precedentes"
      - Prosseguir com análise baseada apenas no relatório
  </passo>
</instrucoes>

<contingencias>
  <se_inputs_opcionais_ausentes>
    Análise prossegue normalmente sem precedentes enriquecidos.
    Mencionar no output: "Precedentes não pesquisados nesta execução."
  </se_inputs_opcionais_ausentes>
</contingencias>
```

### Pattern 3: Contrato com Entradas Opcionais

```xml
<contrato>
  <entrada>
    <tipo>Relatório processual + Pesquisas de precedentes</tipo>
    <formato>MD</formato>
    <requisitos>
      OBRIGATÓRIO: $NUMERO-relatorio.md
      OBRIGATÓRIO: $NUMERO-linha-tempo.md
      OPCIONAL: $INPUTS/pesquisa-bnp.md (precedentes vinculantes STF/STJ)
      OPCIONAL: $INPUTS/pesquisa-cjf.md (jurisprudência TRFs)
      OPCIONAL: $INPUTS/pesquisa-julia.md (jurisprudência TRF5)
    </requisitos>
  </entrada>
  <saida>
    <nome>$NUMERO-analise.md</nome>
    <tipo>Análise do caso com precedentes (se disponíveis)</tipo>
    <formato>MD</formato>
  </saida>
</contrato>
```

---

## Quando Usar Agent Teams

| Cenário | Usar Team? | Razão |
|---------|------------|-------|
| Pesquisas em 3+ fontes independentes | **SIM** | Execução paralela 3x mais rápida |
| Verificações independentes (honorários, cálculos, remessa) | **SIM** | Cada verificador é especialista |
| Análises que dependem uma da outra | NÃO | Usar etapas sequenciais |
| Merge/consolidação de outputs | NÃO | Executar diretamente ou consolidador |
| Apenas 1 agent | NÃO | Overhead desnecessário |
| Tasks com dependência de dados | NÃO | Sequencial é mais seguro |

---

## Anti-Patterns a Evitar

### 1. Teammates que se Comunicam Diretamente

```
INCORRETO:
pesquisador-bnp → escreve → arquivo-compartilhado.md
pesquisador-cjf → lê e modifica → arquivo-compartilhado.md
(race condition!)

CORRETO:
pesquisador-bnp → escreve → pesquisa-bnp.md
pesquisador-cjf → escreve → pesquisa-cjf.md
consolidador → lê ambos → precedentes-consolidado.md
```

### 2. Team com 1 Só Teammate

```
INCORRETO:
TEAM Verificação:
  - verificador-geral (faz tudo)

CORRETO:
Etapa sequencial:
  - verificador-completo (executa diretamente)
```

### 3. Outputs sem Sinalizadores

```
INCORRETO:
# Pesquisa de Precedentes
[conteúdo]
(sem marcador de fim)

CORRETO:
# Relatório de Pesquisa BNP
[conteúdo]
Pesquisa concluída.  ← Sinalizador obrigatório
```

### 4. Downstream que Falha sem Inputs Opcionais

```
INCORRETO:
if not existe(pesquisa-bnp.md):
    raise Error("Pesquisa não encontrada")

CORRETO:
if not existe(pesquisa-bnp.md):
    log("Análise sem enriquecimento de BNP")
    prosseguir_normalmente()
```

---

## Checklist de Conformidade

### Para cada Agent Team, verificar:

| # | Item | Pts |
|---|------|-----|
| 1 | Teammates escrevem em arquivos SEPARADOS | 15 |
| 2 | Orquestrador dispara Tasks em paralelo (mesmo turno) | 15 |
| 3 | Agent downstream lê inputs como OPCIONAIS | 15 |
| 4 | Validação de outputs (ao menos existência) | 10 |
| 5 | _team_manifest.md atualizado após cada team | 10 |
| 6 | TodoWrite rastreia team como etapa única | 10 |
| 7 | Sinalizadores em outputs dos teammates | 10 |
| 8 | Contingência se todos teammates falharem | 10 |
| 9 | Nenhum teammate modifica arquivo de outro | 5 |
|   | **TOTAL** | **100** |

**Score mínimo exigido:** 80 pontos (80%)

---

## Referências

### Fonte: Compilador C Anthropic

> "Coordination via the filesystem turned out to be simpler and more reliable
> than direct message passing. Each agent writes to its own files, and the
> orchestrator reads them when coordination is needed."

### Fonte: Claude Code Agent Teams

> "Agent teams work best when teammates have distinct, non-overlapping
> responsibilities. If you find teammates doing similar work, merge them."

### Templates Relacionados

- `.claude/spec/templates/team-manifest.md` - Template do registro compartilhado
- `.claude/spec/templates/orquestrador.md` - Base para orquestradores de teams
- `.claude/spec/templates/agent.md` - Base para teammates

---

**Framework:** Super Jurista
**Versão:** 2.8
**Data:** 2026-02-07
