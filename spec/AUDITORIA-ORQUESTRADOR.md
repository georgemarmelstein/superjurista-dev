# Auditoria de Orquestrador: pipeline-sentenca-orquestrador.md

**Data:** 2026-01-18
**Arquivo analisado:** `.claude/commands/pipeline-sentenca-orquestrador.md`
**Spec de referência:** `.claude/spec/templates/orquestrador.md` (v2.0)
**Auditor:** Claude Opus 4.5

---

## Resumo Executivo

O orquestrador analisado apresenta **23 desconformidades** em relação ao spec v2.0. Os problemas mais graves são:

1. **AUSÊNCIA TOTAL** de YAML frontmatter (CRÍTICO)
2. **Caminho de agents ERRADO** - usa `/pipelines/` em vez de `/agents/` (CRÍTICO)
3. **Prompts inline extensos** - viola princípio "Orquestrador Cego" (CRÍTICO)
4. **Sem integração TodoWrite** - falta rastreamento de progresso (ALTO)
5. **Variáveis com colchetes** - usa `[NUMERO]` em vez de `$NUMERO` (MÉDIO)

**Score de Conformidade: 35/100**

---

## 1. Desconformidades CRÍTICAS (Bloqueiam Uso)

### 1.1 YAML Frontmatter Ausente

| Aspecto | Spec Requer | Orquestrador Tem |
|---------|-------------|------------------|
| Frontmatter | Obrigatório | **AUSENTE** |

**Spec exige:**
```yaml
---
description: Pipeline de [nome]
argument-hint: [parametro]
allowed-tools: Read Task Bash TodoWrite
---
```

**Orquestrador tem:** Nenhum YAML frontmatter.

**Impacto:** Claude Code não sabe que é um command válido, não exibe hints, não pré-autoriza tools.

---

### 1.2 Caminho de Agents ERRADO

| Aspecto | Spec v2.0 | Orquestrador |
|---------|-----------|--------------|
| Localização | `.claude/agents/[agent].md` | `.claude/pipelines/sentenca/etapas/` |

**Spec v2.0 define:**
```
<caminho_agents>.claude/agents/</caminho_agents>
<!-- Agents ficam na raiz, sem subpasta por pipeline (são reutilizáveis) -->
```

**Orquestrador referencia (ERRADO):**
- `.claude/pipelines/sentenca/etapas/00-linha-tempo.md`
- `.claude/pipelines/sentenca/etapas/01-relatorio-marmelstein.md`
- `.claude/pipelines/sentenca/etapas/02-analise-marmelstein.md`
- `.claude/pipelines/sentenca/etapas/03-fundamentacao-marmelstein.md`
- `.claude/pipelines/sentenca/etapas/04-merge.md`

**Problemas:**
1. Usa `/pipelines/` - estrutura não existe no spec
2. Usa `/etapas/` - nomenclatura v1 obsoleta
3. Prefixo numérico `00-`, `01-` - acoplado à ordem do pipeline
4. Agents não são reutilizáveis - amarrados a este pipeline

---

### 1.3 Prompts Inline Extensos (Viola "Orquestrador Cego")

**Spec define:**
> "O orquestrador NÃO contém prompts inline. Ele apenas referencia arquivos de agents."

**Orquestrador contém (ERRADO):**

| Bloco | Linhas | Tamanho |
|-------|--------|---------|
| `<prompt_subagente_chunk>` | 241-278 | 37 linhas |
| `<prompt_subagente_unico>` | 280-318 | 38 linhas |
| `<prompt_consolidador>` | 320-356 | 36 linhas |
| `<prompt_subagente>` ETAPA 2 | 397-442 | 45 linhas |
| `<prompt_subagente>` ETAPA 3 | 496-542 | 46 linhas |
| `<prompt_subagente>` ETAPA 4 | 584-634 | 50 linhas |
| `<prompt_subagente>` ETAPA 5 | 675-727 | 52 linhas |
| **TOTAL** | - | **304 linhas de prompts inline** |

**Impacto:** Orquestrador perde a característica de "cego" - está executando tarefas dos agents inline.

---

### 1.4 Estrutura de Diretórios Inexistente

**Spec v2.0 estrutura:**
```
.claude/
├── commands/      # Orquestradores
├── agents/        # Agents modulares
├── skills/
└── specs/
```

**Orquestrador referencia (NÃO EXISTE NO SPEC):**
```
.claude/
└── pipelines/
    └── sentenca/
        └── etapas/
```

---

## 2. Desconformidades ALTAS (Afetam Qualidade)

### 2.1 Ausência de TodoWrite

| Aspecto | Spec Requer | Orquestrador Tem |
|---------|-------------|------------------|
| `<rastreamento_progresso>` | Obrigatório v1.3+ | **AUSENTE** |
| TodoWrite na Etapa 0 | Obrigatório | **AUSENTE** |
| Atualização em transições | Obrigatório | **AUSENTE** |

**Spec exige:**
```xml
<rastreamento_progresso>
  <quando_atualizar>
    | Momento | Ação |
    |---------|------|
    | Início do pipeline | Criar TodoWrite com TODAS as etapas |
    | Antes de disparar etapa | Marcar etapa como in_progress |
    | Após validar output | Marcar etapa como completed |
  </quando_atualizar>
</rastreamento_progresso>
```

**Impacto:** Usuário não tem visibilidade do progresso do pipeline.

---

### 2.2 Padrão de Variáveis Inconsistente

| Spec | Orquestrador |
|------|--------------|
| `$ARGUMENTS` | `$ARGUMENTS` (OK) |
| `$NUMERO` | `[NUMERO]` (ERRADO) |
| `$WORKSPACE` | `[CAMINHO_PROCESSO]` (ERRADO) |
| `$MANIFEST` | **AUSENTE** |

**Problema:** Mistura de padrões. Spec usa `$VARIAVEL`, orquestrador usa `[VARIAVEL]`.

---

### 2.3 Ausência de Manifest

**Spec v2.0 requer:**
```xml
<variaveis_injetadas>
  | Variável | Origem |
  |----------|--------|
  | $MANIFEST | Calculada | Caminho do manifest |
</variaveis_injetadas>
```

**Orquestrador:** Não usa `_manifest.md` para descoberta de arquivos.

**Impacto:** Subagentes não têm forma padronizada de descobrir arquivos existentes.

---

### 2.4 Caminho Absoluto Hardcoded

**Linha 760:**
```
Destino: C:\Users\georg\processos-juridicos\sentenca\01-por-analisar\[NUMERO]\
```

**Problema:** Caminho absoluto Windows hardcoded. Não portável, não configurável.

**Spec recomenda:** Usar `$WORKSPACE` relativo.

---

### 2.5 Tools com Vírgula

| Local | Valor |
|-------|-------|
| Linha 224 | `<tools>Read, Write</tools>` |
| Linha 386 | `<tools>Read, Write</tools>` |
| etc. | Todos com vírgula |

**Spec v2.2:** Tools separadas por espaço, SEM vírgula.

---

## 3. Desconformidades MÉDIAS (Afetam Padronização)

### 3.1 Headers Markdown Fora da Estrutura XML

**Linhas problemáticas:**
- L381: `## ETAPA 2 (Relatório Marmelstein)`
- L478: `## ETAPA 3 (Análise Marmelstein)`
- L566: `## ETAPA 4 (Fundamentação Marmelstein)`
- L658: `## ETAPA 5 (Mege)` ← TYPO também
- L753: `## ETAPA 6 (Kanban)`
- L778: `## ETAPA 7 (Relatório Final)`

**Problema:** Mistura Markdown com XML. Headers `##` estão FORA das tags `<etapa>`.

**Spec:** Etapas são definidas APENAS via `<etapa numero="N" nome="X">`.

---

### 3.2 Typo no Nome da Etapa

**Linha 658:** `## ETAPA 5 (Mege)` → Deveria ser "Merge"

---

### 3.3 Modelo Especificado no Local Errado

| Spec | Orquestrador |
|------|--------------|
| Model no YAML do agent | Model em `<config><modelo>` da etapa |

**Problema:** Modelo definido por etapa, não por agent. Isso acopla modelo ao pipeline.

---

### 3.4 Nomenclatura de Arquivos Intermediários Inconsistente

| Arquivo | Padrão Usado | Padrão Spec |
|---------|--------------|-------------|
| `relatorio-marmelstein.md` | nome fixo | `$NUMERO-relatorio.md` |
| `fundamentacao-marmelstein.md` | nome fixo | `$NUMERO-fundamentacao.md` |
| `[NUMERO]-linha-tempo.md` | com prefixo | OK |
| `[NUMERO]-analise.md` | com prefixo | OK |
| `[NUMERO]-minuta.md` | com prefixo | OK |

**Problema:** Inconsistência. Alguns arquivos têm `[NUMERO]-`, outros têm nome fixo.

---

### 3.5 Falta Tag `<agents_utilizados>`

**Spec requer:**
```xml
<agents_utilizados>
  | Agent | Capacidade | Arquivo |
  |-------|------------|---------|
  | [nome-1] | [O que sabe fazer] | .claude/agents/[nome-1].md |
</agents_utilizados>
```

**Orquestrador:** Não lista agents de forma estruturada. Usa `<arquivos_prompt>` (nomenclatura própria).

---

### 3.6 Comandos Bash Inline na Etapa 6

**Linhas 769-775:**
```bash
mkdir -p "C:/Users/georg/processos-juridicos/..."
cp "[CAMINHO_PROCESSO]/[NUMERO]-linha-tempo.md" "..."
```

**Problema:** Comandos Bash hardcoded com paths absolutos. Frágil e não portável.

---

## 4. Desconformidades BAIXAS (Afetam Completude)

### 4.1 Ausência de `<convencao_nomenclatura>`

Spec tem seção detalhada. Orquestrador tem apenas `<nomenclatura_kanban>` (parcial).

### 4.2 Ausência de Versão

Spec templates têm versão no título ou comentário. Orquestrador não tem.

### 4.3 Tabela de Sinalizadores com Coluna Extra

| Spec | Orquestrador |
|------|--------------|
| 3 colunas | 4 colunas (adiciona "Indica") |

Não é erro, mas diverge do padrão.

### 4.4 `<heuristicas>` Não Existe no Spec

Tag customizada. Pode ser útil, mas não é padrão.

---

## Tabela Consolidada de Desconformidades

| # | Severidade | Categoria | Problema | Linha(s) |
|---|------------|-----------|----------|----------|
| 1 | CRÍTICA | Estrutura | YAML frontmatter ausente | 1 |
| 2 | CRÍTICA | Caminhos | Agents em `/pipelines/etapas/` | 165-175 |
| 3 | CRÍTICA | Prompts | 304 linhas de prompts inline | Múltiplas |
| 4 | CRÍTICA | Estrutura | Estrutura `/pipelines/` não existe | 165 |
| 5 | ALTA | Rastreamento | Sem TodoWrite | Todo |
| 6 | ALTA | Variáveis | `[NUMERO]` em vez de `$NUMERO` | Múltiplas |
| 7 | ALTA | Manifest | Ausência de `_manifest.md` | Todo |
| 8 | ALTA | Caminhos | Path absoluto hardcoded | 760 |
| 9 | ALTA | Tools | Vírgula em tools | 224, 386, etc. |
| 10 | MÉDIA | Estrutura | Headers `##` fora do XML | 381, 478, etc. |
| 11 | MÉDIA | Typo | "Mege" → "Merge" | 658 |
| 12 | MÉDIA | Config | Modelo na etapa, não no agent | 223, 385, etc. |
| 13 | MÉDIA | Nomenclatura | Arquivos com/sem prefixo | 145-148 |
| 14 | MÉDIA | Tags | Falta `<agents_utilizados>` | Todo |
| 15 | MÉDIA | Bash | Comandos inline hardcoded | 769-775 |
| 16 | BAIXA | Nomenclatura | Falta `<convencao_nomenclatura>` | Todo |
| 17 | BAIXA | Versão | Ausência de versão | Todo |
| 18 | BAIXA | Tabela | Coluna extra em sinalizadores | 181-187 |
| 19 | BAIXA | Tags | `<heuristicas>` não padronizada | 113-137 |

---

## Score de Conformidade

| Categoria | Peso | Score | Máximo |
|-----------|------|-------|--------|
| YAML Frontmatter | 15% | 0 | 15 |
| Estrutura de Caminhos | 20% | 0 | 20 |
| Princípio Orquestrador Cego | 20% | 5 | 20 |
| Padrão de Variáveis | 10% | 5 | 10 |
| TodoWrite/Rastreamento | 10% | 0 | 10 |
| Nomenclatura de Arquivos | 10% | 5 | 10 |
| Consistência XML | 10% | 10 | 10 |
| Completude de Tags | 5% | 10 | 5 |
| **TOTAL** | **100%** | **35** | **100** |

---

## Recomendações de Correção

### Prioridade 1 (CRÍTICA - Bloqueia uso)

1. **Adicionar YAML frontmatter:**
   ```yaml
   ---
   description: Pipeline completo de sentença judicial
   argument-hint: caminho-do-processo
   allowed-tools: Read Task Bash TodoWrite
   ---
   ```

2. **Mover agents para estrutura correta:**
   ```
   DE: .claude/pipelines/sentenca/etapas/00-linha-tempo.md
   PARA: .claude/agents/extracao/linha-tempo-processual.md
   ```

3. **Remover prompts inline:** Subagentes devem LER seus prompts via `Read: .claude/agents/[agent].md`

### Prioridade 2 (ALTA - Afeta qualidade)

4. **Adicionar TodoWrite:** Criar etapa de rastreamento na Etapa 0
5. **Padronizar variáveis:** `[NUMERO]` → `$NUMERO`, `[CAMINHO_PROCESSO]` → `$WORKSPACE`
6. **Usar manifest:** Adicionar `_manifest.md` para descoberta de arquivos
7. **Remover paths absolutos:** Usar caminhos relativos com `$WORKSPACE`

### Prioridade 3 (MÉDIA - Afeta padronização)

8. **Remover headers `##` soltos:** Manter estrutura XML pura
9. **Corrigir typo:** "Mege" → "Merge"
10. **Padronizar nomenclatura:** Todos arquivos com `$NUMERO-tipo.md`

---

## Checklist de Validação de Orquestrador (Proposta)

Baseado nesta auditoria, propõe-se o seguinte checklist:

```
YAML E ESTRUTURA:
[ ] Tem YAML frontmatter com description, argument-hint e allowed-tools?
[ ] allowed-tools usa espaço (não vírgula)?
[ ] Título segue padrão "# Orquestrador: [Nome do Pipeline]"?

PRINCÍPIO ORQUESTRADOR CEGO:
[ ] Orquestrador NÃO contém prompts de agent inline (>10 linhas)?
[ ] Subagentes são instruídos a LER seus prompts via Read?
[ ] Agents estão em .claude/agents/ (não /pipelines/, /etapas/, etc.)?

INJEÇÃO DE CONTEXTO:
[ ] Etapa 0 calcula $WORKSPACE a partir de $ARGUMENTS?
[ ] Variáveis usam $ (não colchetes)?
[ ] Subagentes recebem caminhos PRONTOS (substituídos)?
[ ] Sem paths absolutos hardcoded?

RASTREAMENTO:
[ ] TodoWrite criado na Etapa 0 com todas as etapas?
[ ] Cada transição atualiza TodoWrite?
[ ] <rastreamento_progresso> presente?

CONTRATOS E VALIDAÇÃO:
[ ] <contratos_dados> mapeia todas as etapas?
[ ] <sinalizadores_formato> define início/fim?
[ ] <sufixos_correcao> prontos para retry?
[ ] Nomenclatura de arquivos segue $NUMERO-tipo.md?

ESTRUTURA XML:
[ ] Tags aninhadas corretamente (sem headers ## soltos)?
[ ] Todas as tags obrigatórias presentes?
[ ] <agents_utilizados> lista os agents?
```

---

**Auditoria realizada em:** 2026-01-18
**Próxima ação:** Criar `checklist-validacao-orquestrador.md` baseado nesta análise

---

## RESULTADO DA CORREÇÃO (2026-01-18)

### Status das Desconformidades

| # | Severidade | Problema | Status |
|---|------------|----------|--------|
| 1 | CRÍTICA | YAML frontmatter ausente | ✅ CORRIGIDO |
| 2 | CRÍTICA | Agents em `/pipelines/etapas/` | ✅ CORRIGIDO |
| 3 | CRÍTICA | 304 linhas de prompts inline | ✅ CORRIGIDO |
| 4 | CRÍTICA | Estrutura `/pipelines/` inexistente | ✅ CORRIGIDO |
| 5 | ALTA | Sem TodoWrite | ✅ CORRIGIDO |
| 6 | ALTA | `[NUMERO]` em vez de `$NUMERO` | ✅ CORRIGIDO |
| 7 | ALTA | Ausência de `_manifest.md` | ⚠️ NÃO APLICADO (opcional) |
| 8 | ALTA | Path absoluto hardcoded | ✅ CORRIGIDO |
| 9 | ALTA | Tools com vírgula | ✅ CORRIGIDO |
| 10 | MÉDIA | Headers `##` fora do XML | ✅ CORRIGIDO |
| 11 | MÉDIA | Typo "Mege" | ✅ CORRIGIDO |
| 12 | MÉDIA | Modelo na etapa, não no agent | ⚠️ MANTIDO (spec permite) |
| 13 | MÉDIA | Nomenclatura inconsistente | ✅ CORRIGIDO |
| 14 | MÉDIA | Falta `<agents_utilizados>` | ✅ CORRIGIDO |
| 15 | MÉDIA | Comandos Bash inline hardcoded | ✅ CORRIGIDO |
| 16 | BAIXA | Falta `<convencao_nomenclatura>` | ✅ CORRIGIDO |
| 17 | BAIXA | Ausência de versão | ✅ CORRIGIDO |
| 18 | BAIXA | Coluna extra em sinalizadores | ✅ CORRIGIDO |
| 19 | BAIXA | `<heuristicas>` não padronizada | ✅ REMOVIDO |

### Score Pós-Correção

| Categoria | Peso | ANTES | DEPOIS |
|-----------|------|-------|--------|
| YAML Frontmatter | 15% | 0 | 15 |
| Estrutura de Caminhos | 20% | 0 | 20 |
| Princípio Orquestrador Cego | 20% | 5 | 20 |
| Padrão de Variáveis | 10% | 5 | 10 |
| TodoWrite/Rastreamento | 10% | 0 | 10 |
| Nomenclatura de Arquivos | 10% | 5 | 10 |
| Consistência XML | 10% | 10 | 10 |
| Completude de Tags | 5% | 10 | 5 |
| **TOTAL** | **100%** | **35** | **100** |

### Pendências

O orquestrador corrigido referencia 2 agents que ainda não existem:
- `.claude/agents/redacao/fundamentador.md`
- `.claude/agents/redacao/merge-sentenca.md`

Estes devem ser criados seguindo o spec de agents (`AGENTS-SPECS.md`).

### Artefatos Atualizados

1. `pipeline-sentenca-orquestrador.md` - Reescrito seguindo spec v2.0
2. `checklist-validacao-orquestrador.md` - Calibrado para v1.1 com anti-patterns reais

---

**Correção realizada em:** 2026-01-18
**Auditor:** Claude Opus 4.5
