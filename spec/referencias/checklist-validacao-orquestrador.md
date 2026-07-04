# Checklist de Validação: Orquestrador v2.0

> **Propósito:** Verificar conformidade de orquestradores com o spec v2.0+
>
> **Usar antes de:** Colocar orquestrador em produção
>
> **Changelog v2.0:**
> - Harmonizado com checklist de agents (6 seções ponderadas)
> - Pontuação explícita por item (total: 130 pontos)
> - Threshold de aprovação: 104/130 (80%)
> - Sufixos de correção contextualizados por seção

---

## Instruções de Uso

1. Copie este checklist
2. Marque cada item e some os pontos obtidos
3. Itens CRÍTICOS (seções 1-3) bloqueiam uso - DEVEM ser 100%
4. Itens ALTOS (seções 4, 5, 7, 8) afetam qualidade - corrigir antes de produção
5. Itens MÉDIOS (seção 6) afetam padronização - corrigir quando possível

**Score mínimo para aprovação:** 104/130 (80%)

---

## 1. YAML Frontmatter [CRÍTICO] - 20 pontos

| Item | Pts | Check |
|------|-----|-------|
| Arquivo começa com `---` | 2 | [ ] |
| Campo `description` presente e descritivo | 5 | [ ] |
| Campo `argument-hint` presente e claro | 3 | [ ] |
| Campo `allowed-tools` presente | 3 | [ ] |
| `allowed-tools` usa ESPAÇO (não vírgula) | 2 | [ ] |
| `allowed-tools` inclui TodoWrite | 3 | [ ] |
| Bloco termina com `---` | 2 | [ ] |

**Exemplo correto:**
```yaml
---
description: Pipeline de sentença judicial completa
argument-hint: caminho-do-processo
allowed-tools: Read Task Bash TodoWrite
---
```

**Anti-pattern:**
```markdown
# Orquestrador: Pipeline de Sentença
<!-- Sem YAML frontmatter - CRÍTICO: 0/20 pontos -->
```

---

## 2. Princípio Orquestrador Cego [CRÍTICO] - 30 pontos

| Item | Pts | Check |
|------|-----|-------|
| Prompts inline < 50 linhas E estruturados corretamente | 10 | [ ] |
| Passo 1 SEMPRE é "Read: .claude/agents/[agent].md" | 10 | [ ] |
| Agents em `.claude/agents/[categoria]/` | 5 | [ ] |
| Agents são modulares e reutilizáveis | 5 | [ ] |

**Padrão CORRETO (prompt estruturado ~40 linhas):**
```xml
<prompt_subagente tipo="extrator-linha-tempo">
  ═══════════════════════════════════════════════════════════════════════
  VOCE E UM SUBAGENTE DE EXTRACAO. EXECUTE DIRETAMENTE.
  ═══════════════════════════════════════════════════════════════════════

  <passo numero="1" nome="Ler instrucoes do agent">
    Read: .claude/agents/extracao/linha-tempo-processual.md
    - Este arquivo define sua CAPACIDADE. Siga fielmente.
  </passo>

  <passo numero="2" nome="Ler entrada">
    Read: $WORKSPACE/processo.txt
    - O orquestrador ja substituiu $WORKSPACE pelo caminho real. Leia a entrada por caminho.
  </passo>

  <passo numero="3" nome="Executar tarefa">
    - Extraia cronologia completa do processo
    - Identifique MARCOS PROCESSUAIS
    - Use portugues COM ACENTOS
  </passo>

  <passo numero="4" nome="Gravar o documento">
    Write: $WORKSPACE/$NUMERO-linha-tempo.md
    - GRAVE o documento completo, com os marcadores de inicio/fim.
  </passo>

  <passo numero="5" nome="Responder status">
    - Responder APENAS: "linha-tempo OK | $NUMERO-linha-tempo.md" — NAO imprimir o documento (L5).
  </passo>

  <restricoes>
    - GRAVAR com "# Linha do Tempo Processual" (inicio) e "É o que satisfaz extrair dos autos." (fim)
    - NAO imprimir o documento na resposta — responder so a linha de status
    - NUNCA usar TodoWrite
  </restricoes>
</prompt_subagente>
```

**Anti-pattern (lógica do agent inline):**
```xml
<!-- ERRADO: Prompt contém a LÓGICA do agent em vez de instruir a LER -->
<prompt_subagente>
  Você é um extrator de cronologia processual especializado em...
  [100+ linhas definindo CAPACIDADE que deveria estar no arquivo do agent]
  [Sem instrução de Read: .claude/agents/...]
</prompt_subagente>
```

**Regras do Orquestrador Cego:**
1. Prompt inline pode ter até ~50 linhas, MAS deve ser ESTRUTURADO
2. Passo 1 OBRIGATÓRIO: `Read: .claude/agents/[agent].md`
3. O prompt NÃO contém a lógica/capacidade do agent (isso fica no arquivo)
4. O prompt INSTRUI: ler agent → ler entradas → executar → salvar

---

## 3. Injeção de Contexto [CRÍTICO] - 20 pontos

| Item | Pts | Check |
|------|-----|-------|
| Etapa 0 recebe $ARGUMENTS do usuário | 5 | [ ] |
| Etapa 0 calcula $WORKSPACE e $NUMERO | 5 | [ ] |
| Variáveis usam padrão $ (não colchetes) | 5 | [ ] |
| Sem paths absolutos hardcoded (C:\Users\...) | 5 | [ ] |

**Padrão de variáveis:**
```xml
<variaveis_injetadas>
  | Variável | Origem | Uso |
  |----------|--------|-----|
  | $ARGUMENTS | Usuário | Entrada original |
  | $NUMERO | Extraída | Prefixo de arquivos |
  | $WORKSPACE | Calculada | Pasta do processo |
</variaveis_injetadas>
```

**Anti-patterns:**
```markdown
<!-- ERRADO: variáveis com colchetes (0/5 pts) -->
<entrada>[CAMINHO_PROCESSO]/processo.txt</entrada>

<!-- ERRADO: path absoluto (0/5 pts) -->
Destino: C:\Users\georg\processos\sentenca\[NUMERO]\
```

---

## 4. Rastreamento e Validação [ALTO] - 15 pontos

| Item | Pts | Check |
|------|-----|-------|
| Tag `<rastreamento_progresso>` presente | 3 | [ ] |
| TodoWrite criado na Etapa 0 com TODAS as etapas | 4 | [ ] |
| Transições atualizam TodoWrite | 3 | [ ] |
| Tag `<sinalizadores_formato>` presente | 3 | [ ] |
| Tag `<sufixos_correcao>` presente | 2 | [ ] |

**Padrão TodoWrite:**
```javascript
TodoWrite([
  {content: "Etapa 0 - Preparação", status: "completed", activeForm: "Preparando"},
  {content: "Etapa 1 - Linha do Tempo", status: "in_progress", activeForm: "Extraindo cronologia"},
  {content: "Etapa 2 - Relatório", status: "pending", activeForm: "Gerando relatório"},
])
```

**Anti-pattern:** Orquestrador sem TodoWrite = usuário não sabe em qual etapa está.

---

## 5. Contratos e Estrutura [ALTO] - 10 pontos

| Item | Pts | Check |
|------|-----|-------|
| `<contratos_dados>` mapeia TODAS as etapas | 4 | [ ] |
| Cada etapa tem `<config>` | 2 | [ ] |
| Cada etapa tem `<acao_orquestrador>` | 2 | [ ] |
| Cada etapa tem `<validacao>` e `<transicao>` | 2 | [ ] |

**Padrão de nomenclatura:**
```
$NUMERO-linha-tempo.md      (não: linha-tempo.md)
$NUMERO-relatorio.md        (não: relatorio.md)
$NUMERO-analise.md          (não: analise.md)
$NUMERO-sentenca.md         (não: minuta.md)
```

**Estrutura de etapa obrigatória:**
```xml
<etapa numero="N" nome="Nome">
  <config>
    <modelo>sonnet</modelo>
    <tools>Read Write</tools>
    <agent>.claude/agents/categoria/agent.md</agent>
    <entrada>$WORKSPACE/entrada.txt</entrada>
    <saida>$WORKSPACE/$NUMERO-saida.md</saida>
  </config>
  <acao_orquestrador>...</acao_orquestrador>
  <validacao>...</validacao>
  <transicao>...</transicao>
</etapa>
```

---

## 6. Tags Obrigatórias e Boas Práticas [MÉDIO] - 5 pontos

| Item | Pts | Check |
|------|-----|-------|
| `<identidade>`, `<proposito>`, `<capacidades>` presentes | 2 | [ ] |
| `<restricoes>` e `<contingencias>` presentes | 1 | [ ] |
| `<resumo_arquitetura>` com diagrama ASCII | 1 | [ ] |
| `<configuracao>` com `<agents_utilizados>` | 1 | [ ] |

**Diagrama ASCII obrigatório:**
```
FLUXO DE DADOS:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   $ARGUMENTS │────▶│  ORQUESTRADOR│────▶│  SUBAGENTES  │
│  (usuário)   │     │  (calcula    │     │  (recebem    │
│              │     │   $WORKSPACE)│     │   caminhos   │
│              │     │              │     │   prontos)   │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Agents utilizados:**
```xml
<agents_utilizados>
  | Agent | Capacidade | Arquivo |
  |-------|------------|---------|
  | linha-tempo-processual | Extrai cronologia | .claude/agents/extracao/linha-tempo-processual.md |
  | relator-marmelstein | Gera relatório | .claude/agents/extracao/relator-marmelstein.md |
</agents_utilizados>
```

---

## Tabela de Pontuação

| Seção | Severidade | Pontos | Bloqueia? |
|-------|------------|--------|-----------|
| 1. YAML Frontmatter | CRÍTICA | 20 | SIM |
| 2. Orquestrador Cego | CRÍTICA | 30 | SIM |
| 3. Injeção de Contexto | CRÍTICA | 20 | SIM |
| 4. Rastreamento e Validação | ALTA | 15 | Não |
| 5. Contratos e Estrutura | ALTA | 10 | Não |
| 6. Tags e Boas Práticas | MÉDIA | 5 | Não |
| 7. Anti-Padrões Multi-Agentes | ALTA | 15 | Não |
| 8. Padrão v3.0 (Retomada/Gate/Saída) | ALTA | 15 | Não |
| **TOTAL** | - | **130** | - |

---

## Score de Conformidade

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VALIDAÇÃO DO ORQUESTRADOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. YAML Frontmatter (CRÍTICO):              __ / 20
2. Orquestrador Cego (CRÍTICO):             __ / 30
3. Injeção de Contexto (CRÍTICO):           __ / 20
4. Rastreamento e Validação (ALTO):         __ / 15
5. Contratos e Estrutura (ALTO):            __ / 10
6. Tags e Boas Práticas (MÉDIO):            __ / 5
7. Anti-Padrões Multi-Agentes (ALTO):       __ / 15  [NOVO v2.1]
8. Padrão v3.0 - Retomada/Gate/Saída (ALTO):__ / 15  [NOVO v3.0]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:                                      __ / 130

Status: [APROVADO (≥104) | REPROVADO (<104)]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Interpretação:**
- **117-130:** Pronto para produção (90%+)
- **104-116:** Pequenos ajustes necessários (80-89%)
- **91-103:** Ajustes médios necessários (70-79%)
- **<91:** Revisão significativa necessária (<70%)

---

## Sufixos de Correção

### Sufixo YAML (Seção 1)

```
[FALHA NO YAML (Seção 1: __/20 pts).

O orquestrador DEVE ter frontmatter YAML válido:
---
description: Pipeline de [nome] - [o que faz]
argument-hint: [parametro-esperado]
allowed-tools: Read Task Bash TodoWrite
---

Itens faltantes:
- [LISTAR ITENS COM 0 PONTOS]

Corrija e regenere.]
```

### Sufixo Orquestrador Cego (Seção 2)

```
[FALHA NO PRINCÍPIO ORQUESTRADOR CEGO (Seção 2: __/30 pts).

REGRA: Orquestrador INJETA contexto. Agent DEFINE capacidade.

Problemas identificados:
- [LISTAR: PASSO 1 NÃO É "Read: agent.md" / LÓGICA DO AGENT INLINE / PROMPT > 50 LINHAS]

Ação corretiva:
1. Passo 1 DEVE ser: Read: .claude/agents/[categoria]/[agent].md
2. A LÓGICA/CAPACIDADE do agent deve estar no arquivo .md, não inline
3. Prompt inline deve ser ESTRUTURADO: cabeçalho + passos + restrições
4. Prompt inline pode ter até ~50 linhas (não 15), mas ESTRUTURADO

Estrutura obrigatória do prompt:
  ═══════════════════════════════════════════════════════════════════════
  VOCE E UM SUBAGENTE DE [FUNÇÃO]. EXECUTE DIRETAMENTE.
  ═══════════════════════════════════════════════════════════════════════
  <passo numero="1">Read: .claude/agents/[agent].md</passo>  ← OBRIGATÓRIO
  <passo numero="2">Read: $WORKSPACE/[entrada]</passo>
  <passo numero="N">Write: $WORKSPACE/$NUMERO-[saida].md</passo>
  <restricoes>Sinalizadores obrigatórios</restricoes>

Corrija e regenere.]
```

### Sufixo Injeção de Contexto (Seção 3)

```
[FALHA NA INJEÇÃO DE CONTEXTO (Seção 3: __/20 pts).

Problemas identificados:
- [LISTAR: VARIÁVEIS COM [], PATHS ABSOLUTOS, ETC]

Correções necessárias:
- Etapa 0 DEVE calcular $WORKSPACE a partir de $ARGUMENTS
- Usar $ para variáveis: $WORKSPACE, $NUMERO, $ARGUMENTS
- NUNCA usar paths absolutos (C:\Users\...)
- Subagentes recebem caminhos PRONTOS (já substituídos)

Corrija e regenere.]
```

### Sufixo Rastreamento (Seção 4)

```
[FALHA NO RASTREAMENTO (Seção 4: __/15 pts).

Itens faltantes:
- [LISTAR O QUE FALTA]

Regras obrigatórias:
- TodoWrite DEVE ser criado na Etapa 0 com TODAS as etapas
- Cada transição DEVE atualizar TodoWrite
- <sinalizadores_formato> DEVE mapear início/fim de cada etapa
- <sufixos_correcao> DEVE estar presente

Corrija e regenere.]
```

### Sufixo Contratos (Seção 5)

```
[FALHA NOS CONTRATOS E ESTRUTURA (Seção 5: __/10 pts).

Problemas:
- [LISTAR ETAPAS SEM CONFIG, CONTRATOS INCOMPLETOS, ETC]

Cada etapa DEVE ter:
- <config> com modelo, tools, agent, entrada, saída
- <acao_orquestrador> com passos claros
- <validacao> com checklist
- <transicao> com próxima etapa ou condição de parada

<contratos_dados> DEVE mapear TODAS as etapas.

Corrija e regenere.]
```

### Sufixo Acentos

```
[FALHA DE ACENTOS. Use português correto COM acentos: é, á, ã, ç, ô, ê, í, ú.
Documento brasileiro EXIGE acentuação correta. Corrija e regenere.]
```

---

## Exemplo de Auditoria

```markdown
# Auditoria: pipeline-sentenca.md

## 1. YAML Frontmatter [CRÍTICO]
[✓] 2 pts - Arquivo começa com ---
[✓] 5 pts - description presente
[✓] 3 pts - argument-hint presente
[✓] 3 pts - allowed-tools presente
[✓] 2 pts - usa ESPAÇO
[✓] 3 pts - inclui TodoWrite
[✓] 2 pts - termina com ---
Subtotal: 20/20

## 2. Orquestrador Cego [CRÍTICO]
[✓] 10 pts - Prompts inline < 50 linhas E estruturados
[✓] 10 pts - Passo 1 = Read: .claude/agents/[agent].md
[✓] 5 pts - Agents em .claude/agents/
[✓] 5 pts - Agents modulares
Subtotal: 30/30

## 3. Injeção de Contexto [CRÍTICO]
[✓] 5 pts - Etapa 0 recebe $ARGUMENTS
[✓] 5 pts - Calcula $WORKSPACE
[✓] 5 pts - Variáveis com $
[✓] 5 pts - Sem paths absolutos
Subtotal: 20/20

## 4. Rastreamento e Validação [ALTO]
[✓] 3 pts - <rastreamento_progresso>
[✓] 4 pts - TodoWrite na Etapa 0
[✓] 3 pts - Transições atualizam
[✓] 3 pts - <sinalizadores_formato>
[✓] 2 pts - <sufixos_correcao>
Subtotal: 15/15

## 5. Contratos e Estrutura [ALTO]
[✓] 4 pts - <contratos_dados>
[✓] 2 pts - Etapas têm <config>
[✓] 2 pts - Etapas têm <acao_orquestrador>
[✓] 2 pts - Etapas têm <validacao>/<transicao>
Subtotal: 10/10

## 6. Tags e Boas Práticas [MÉDIO]
[✓] 2 pts - Tags obrigatórias
[✓] 1 pt - Restrições/contingências
[✓] 1 pt - Diagrama ASCII
[✓] 1 pt - <agents_utilizados>
Subtotal: 5/5

## 7. Prevenção de Anti-Padrões Multi-Agentes [ALTO]
[✓] 15 pts - Sem race conditions, isolamento e menor privilégio corretos
Subtotal: 15/15

## 8. Padrão v3.0 — Retomada, Gate e Saída em Disco [ALTO]
[✓] 5 pts - Gate scripts/verificar_<sistema>.py + Etapa 0 roda a varredura (PENDENTES)
[✓] 5 pts - Cláusula de retomada por etapa + validação por --etapa/--gate (não lê p/ validar)
[✓] 5 pts - Invólucro manda GRAVAR + responder 1 linha + NÃO imprimir o documento
Subtotal: 15/15

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL: 130/130 ✓ APROVADO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 7. Prevenção de Anti-Padrões Multi-Agentes [ALTO] - 15 pontos [NOVO v2.1]

> **Referência:** `.claude/spec/referencias/anti-padroes-multi-agentes.md`
>
> Orquestradores são especialmente vulneráveis a anti-padrões de coordenação.

| Item | Pts | Check |
|------|-----|-------|
| Validação entre TODAS as etapas por GATE POR SCRIPT (verificar --etapa) | 4 | [ ] |
| Fallback/circuit breaker se validação falha | 3 | [ ] |
| Agents têm papéis DISTINTOS (não sobrepostos) | 3 | [ ] |
| Comunicação usa schemas estruturados | 3 | [ ] |
| Complexidade justificada (testou simpler?) | 2 | [ ] |

### 7.1 Validação entre Etapas por Script (CRÍTICO)

A validação é DETERMINÍSTICA e do SCRIPT — o orquestrador NÃO lê o documento para conferir
sinalizadores (L14). O gate normaliza acento/caixa e devolve exit-code.

```markdown
<!-- CORRETO: gate por script (exit 0 = válida) -->
<validacao>
  Bash: python scripts/verificar_<sistema>.py "$WORKSPACE" --etapa relatorio
  - exit 0 → prosseguir
  - exit 1 ([AUSENTE]/[INVALIDA]) → NÃO avançar; redespachar com sufixo_gate (máx 2x)
</validacao>

<!-- ERRADO: validar LENDO o documento (viola L14) -->
<validacao>
  - [ ] Orquestrador lê o arquivo e procura "É o que havia de relevante a relatar."?
</validacao>

<!-- ERRADO: Encadeamento cego -->
Task(agent1) → Task(agent2) → Task(agent3)
<!-- Sem gate entre etapas = cascata de erros -->
```

### 7.2 Circuit Breaker

```markdown
<!-- CORRETO: Limite de tentativas -->
<contingencia_etapa>
  SE validação falha após 2 tentativas:
  - Interromper pipeline
  - Alertar usuário com contexto do problema
  - NÃO continuar com input inválido
</contingencia_etapa>

<!-- ERRADO: Loop infinito potencial -->
<contingencia>
  SE falha: Tentar novamente até funcionar
</contingencia>
```

### 7.3 Papéis Distintos

```markdown
<!-- CORRETO: Cada agent tem papel único -->
<agents_utilizados>
  | Agent | Papel ÚNICO |
  |-------|-------------|
  | linha-tempo | Extrai cronologia (só cronologia) |
  | relator | Gera relatório (só relatório) |
  | analisador | Analisa juridicamente (só análise) |
</agents_utilizados>

<!-- ERRADO: Papéis sobrepostos -->
<agents>
  | Agent | Papel |
  |-------|-------|
  | analisador1 | Analisa o caso |
  | analisador2 | Também analisa o caso |  <!-- Duplicação! -->
</agents>
```

### 7.4 Comunicação Estruturada

```markdown
<!-- CORRETO: Formato definido -->
<contrato_etapa>
  <entrada>
    <formato>JSON com campos: numero, fatos, questoes</formato>
  </entrada>
  <saida>
    <formato>MD com sinalizadores START/END</formato>
  </saida>
</contrato_etapa>

<!-- ERRADO: Texto livre -->
<contrato>
  Entrada: o que vier
  Saída: o que o agent produzir
</contrato>
```

---

## 8. Padrão v3.0 — Retomada, Gate e Saída em Disco [ALTO] - 15 pontos [NOVO v3.0]

> O encanamento v3.0: retomada por varredura (L13), validação por script (L14) e contrato de
> saída em disco (L5). Substituem os andaimes da era 200k (validação por leitura, chunking defensivo).

| Item | Pts | Check |
|------|-----|-------|
| **RETOMADA:** Etapa 0 roda o gate (verificar_<sistema>.py) → linha `PENDENTES` é o plano | 3 | [ ] |
| **RETOMADA:** cada etapa tem cláusula `<retomada>` (pula se o slug não está em PENDENTES) | 2 | [ ] |
| **VALIDAÇÃO POR SCRIPT:** gate `--etapa` por etapa; orquestrador NÃO lê o documento p/ validar (L14) | 4 | [ ] |
| **VALIDAÇÃO POR SCRIPT:** Finalização com gate `--gate` | 1 | [ ] |
| **SAÍDA EM DISCO:** o invólucro manda GRAVAR (Write) o documento com marcadores | 2 | [ ] |
| **SAÍDA EM DISCO:** o invólucro manda RESPONDER 1 linha ("<slug> OK \| <arquivo>") | 2 | [ ] |
| **SAÍDA EM DISCO:** restrição explícita "NÃO imprimir o documento inline" (L5) | 1 | [ ] |

### 8.1 Retomada por varredura (L13)

```markdown
<!-- CORRETO: Etapa 0 roda o gate; PENDENTES é o plano; etapas válidas nascem completed -->
Bash: python scripts/verificar_<sistema>.py "$WORKSPACE"   → "PENDENTES: relatorio fundamentacao"
<etapa numero="2">
  <retomada>Se "relatorio" NÃO está em PENDENTES → PULAR (o trabalho já foi pago).</retomada>
</etapa>

<!-- ERRADO: reexecutar tudo do zero a cada rodada (retrabalho em opus é o desperdício mais caro) -->
```

### 8.2 Contrato de saída em disco (L5)

```markdown
<!-- CORRETO: grava + responde 1 linha -->
<passo numero="4" nome="Gravar">Write: $WORKSPACE/$NUMERO-relatorio.md</passo>
<passo numero="5" nome="Status">Responder APENAS: "relatorio OK | $NUMERO-relatorio.md" — NÃO imprimir o documento.</passo>

<!-- ERRADO: devolver o documento inteiro inline entre sinalizadores (era 200k) -->
```

---

## Anti-Patterns Comuns (Resumo)

| Anti-Pattern | Seção | Pontos Perdidos | Solução |
|--------------|-------|-----------------|---------|
| Sem YAML frontmatter | 1 | 20 | Adicionar bloco `---` |
| Lógica do agent inline (sem Read) | 2 | 20 | Passo 1 = Read: .claude/agents/[agent].md |
| Prompt > 50 linhas OU não estruturado | 2 | 10 | Estruturar: cabeçalho + passos + restrições |
| Variáveis com `[COLCHETES]` | 3 | 5 | Substituir por `$VARIAVEL` |
| Paths absolutos C:\Users\... | 3 | 5 | Usar `$WORKSPACE` |
| Sem TodoWrite | 4 | 7 | Criar na Etapa 0 |
| Sem <contratos_dados> | 5 | 4 | Adicionar tabela |
| Sem diagrama ASCII | 6 | 1 | Criar em <resumo_arquitetura> |
| Encadeamento cego (sem gate por script) | 7 | 4 | Validar entre etapas com verificar --etapa |
| Sem circuit breaker | 7 | 3 | Limite de tentativas |
| Papéis sobrepostos | 7 | 3 | Um papel único por agent |
| Comunicação não estruturada | 7 | 3 | Usar schemas |
| Etapa 0 não roda o gate / pipeline não retomável | 8 | 5 | Varredura na Etapa 0; PENDENTES é o plano; cláusula <retomada> por etapa |
| Orquestrador LÊ o documento para validar (viola L14) | 8 | 5 | Gate por script (--etapa/--gate) |
| Subagente ecoa o documento inline (viola L5) | 8 | 5 | Invólucro manda GRAVAR + responder 1 linha |

---

## Changelog

### v3.0 (2026-07-04)
- ADICIONADO: Seção 8 - Padrão v3.0: Retomada (L13), Gate por script (L14), Saída em disco (L5) (15 pts)
- ATUALIZADO: Score máximo de 115 para 130 pontos; threshold de aprovação 104/130 (80%)
- ATUALIZADO: Seção 7.1 - validação entre etapas agora é por GATE POR SCRIPT (verificar --etapa), não por leitura de sinalizador
- CORRIGIDO: exemplo canônico da Seção 2 - removido "leia em blocos" (chunking defensivo era-200k); passo de saída GRAVA + responde 1 linha
- CORRIGIDO: caminho do diretório de spec para o singular `.claude/spec/` (o plural estava incorreto)

### v2.2 (2026-01-22)
- CORRIGIDO: Seção 2 - Regra de tamanho de prompts inline
  - De "< 15 linhas" para "< 50 linhas E estruturados corretamente"
  - Calibrado com base no pipeline-sentenca.md (padrão de referência ~40 linhas)
- CORRIGIDO: Critério de validação agora é "Passo 1 SEMPRE é Read: agent.md"
- ATUALIZADO: Anti-pattern principal é "lógica do agent inline" (não tamanho)
- ATUALIZADO: Sufixo de correção com estrutura obrigatória do prompt
- ATUALIZADO: Tabela de anti-patterns com novos critérios

### v2.1 (2026-01-19)
- ADICIONADO: Seção 7 - Prevenção de Anti-Padrões Multi-Agentes (15 pts)
  - 7.1 Validação entre etapas (4 pts)
  - 7.2 Circuit breakers (3 pts)
  - 7.3 Papéis distintos (3 pts)
  - 7.4 Comunicação estruturada (3 pts)
  - 7.5 Complexidade justificada (2 pts)
- ATUALIZADO: Score máximo de 100 para 115 pontos
- ATUALIZADO: Threshold de aprovação de 90 para 92 (80%)
- ADICIONADO: Referência a `.claude/spec/referencias/anti-padroes-multi-agentes.md`
- FONTE: Pesquisa de Arquiteturas Multi-Agentes Hierárquicas

### v2.0 (2026-01-18)
- Versão inicial harmonizada com checklist-validacao-agent.md

---

**Checklist versão:** 3.0
**Compatível com spec:** v2.0+ (encanamento v3.0)
**Harmonizado com:** checklist-validacao-agent.md v1.3
**Atualizado em:** 2026-07-04
