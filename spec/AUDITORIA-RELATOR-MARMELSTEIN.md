# Auditoria de Agent: relator-marmelstein.md

**Data:** 2026-01-18
**Arquivo analisado:** `.claude/agents/extracao/relator-marmelstein.md`
**Spec de referência:** `.claude/spec/templates/agent.md` (v2.0)
**Checklist aplicado:** `.claude/spec/referencias/checklist-validacao-agent.md` (v1.0)
**Auditor:** Claude Opus 4.5

---

## Resumo Executivo

O agent analisado apresenta **desconformidade severa** com o spec v2.0:

| Categoria | Score | Máximo | % |
|-----------|-------|--------|---|
| YAML Frontmatter | 0 | 30 | 0% |
| Localização | 10 | 10 | 100% |
| Tags Obrigatórias | 0 | 40 | 0% |
| Tags Recomendadas | 8 | 10 | 80% |
| Ausência Anti-Patterns | 0 | 10 | 0% |
| **TOTAL** | **18** | **100** | **18%** |

**Classificação:** REPROVADO (< 60)

**Pontos fortes:**
- Localização correta (subpasta por categoria: `/extracao/`)
- Formato de saída excelente com exemplo completo
- Tags de domínio bem organizadas

**Pontos críticos:**
- AUSÊNCIA TOTAL de YAML frontmatter
- Tags v1 incompatíveis (`<persona>`, `<objetivo>`)
- Caminhos hardcoded (`processo.txt`, `relatorio-marmelstein.md`)
- NÃO é granular - assume entrada específica

---

## 1. Aplicação do Checklist

### 1.1 YAML Frontmatter (0/30)

| Item | Status | Detalhe |
|------|--------|---------|
| Bloco YAML presente | ❌ | Começa com `# ETAPA 01 - RELATÓRIO` |
| Campo `name` | ❌ | Ausente |
| Campo `description` | ❌ | Ausente |
| Campo `tools` | ❌ | Ausente |
| Campo `model` | ❌ | Ausente |

**O que deveria ter:**
```yaml
---
name: relator-marmelstein
description: Gera relatório judicial estruturado a partir de documentos processuais
tools: Read Write
model: sonnet
---
```

---

### 1.2 Localização (10/10)

| Item | Status | Detalhe |
|------|--------|---------|
| Caminho correto | ✅ | `.claude/agents/extracao/relator-marmelstein.md` |
| Subpasta por categoria | ✅ | `extracao/` é categoria, não pipeline |
| Sem pipeline no path | ✅ | Não usa `/pipeline-sentenca/` ou similar |

**Único ponto 100% conforme.**

---

### 1.3 Tags Obrigatórias (0/40)

#### 3.1 Tag `<identidade>` (0/5)

**Spec requer:**
```xml
<identidade>
  <papel>Descrição do papel</papel>
  <estilo>Estilo de execução</estilo>
</identidade>
```

**Agent tem:**
```xml
<persona>
Você é um ASSISTENTE JURÍDICO DE ALTO NÍVEL especializado em...
</persona>
```

**Problemas:**
1. Tag `<persona>` ≠ `<identidade>` (nomenclatura v1)
2. Texto em prosa, não subtags estruturadas
3. Falta `<papel>` e `<estilo>`

---

#### 3.2 Tag `<capacidade>` (0/10)

**Spec requer:**
```xml
<capacidade>
  <habilidade>Verbo infinitivo + o que faz</habilidade>
  <especializacao>Área de conhecimento</especializacao>
</capacidade>
```

**Agent tem:**
```xml
<objetivo>
Sua tarefa é realizar uma LEITURA abrangente...
</objetivo>
```

**Problemas:**
1. Tag `<objetivo>` ≠ `<capacidade>` (semântica diferente)
2. Descreve TAREFA, não CAPACIDADE
3. Hardcoda filename: "Arquivo `relatorio-marmelstein.md`"
4. Falta `<habilidade>` e `<especializacao>`

---

#### 3.3 Tag `<contrato>` (0/10)

**Spec requer:**
```xml
<contrato>
  <entrada>
    <tipo>Tipo genérico</tipo>
    <formato>MD, TXT</formato>
    <requisitos>O que deve conter</requisitos>
  </entrada>
  <saida>
    <tipo>Tipo produzido</tipo>
    <formato>MD</formato>
  </saida>
</contrato>
```

**Agent tem:**
```html
<!--
ENTRADA: processo.txt
SAÍDA: relatorio-marmelstein.md
CONTEXTO: Apenas o processo
-->
```

**Problemas:**
1. Comentário HTML, não tag XML
2. Caminhos HARDCODED (não tipos genéricos)
3. Não reutilizável - assume `processo.txt`
4. Viola princípio de granularidade

---

#### 3.4 Tag `<restricoes>` (0/5)

**Status:** AUSENTE

O agent tem restrições espalhadas em outras tags, mas não estruturadas:
- L118: "NÃO incluir: qualificação das partes..."
- L132: "SEM asteriscos/hashtags"

**Falta obrigatória v2.0:**
- "NÃO assumir caminhos de arquivo - recebe via contexto"

---

#### 3.5 Tag `<contingencias>` (0/5)

**Status:** AUSENTE

Agent não define o que fazer se:
- Entrada não tiver petição inicial
- Entrada estiver incompleta
- Formato não puder ser seguido

---

#### 3.6 Tag `<instrucoes>` (0/5)

**Spec requer:**
```xml
<instrucoes>
  <passo numero="1" nome="Receber entrada">...</passo>
  <passo numero="2" nome="Processar">...</passo>
</instrucoes>
```

**Agent tem:** Tags não estruturadas como passos:
- `<leitura>` (L91-94)
- `<pecas_relevantes>` (L96-105)
- `<extracao>` (L107-119)

**Problema:** Informações de instrução fragmentadas, não sequenciais.

---

### 1.4 Tags Recomendadas (8/10)

#### 4.1 `<formato_saida>` (3/3)

| Item | Status |
|------|--------|
| Tag presente | ✅ (`<formato_saida_marmelstein>`) |
| Template literal | ✅ |
| Sinalizadores | ✅ (início: "RELATÓRIO", fim: "É o que havia de relevante a relatar.") |

**Nota:** Tag usa sufixo customizado `_marmelstein`. Funcionalmente correto.

---

#### 4.2 `<sinalizadores>` (1/3)

| Item | Status |
|------|--------|
| Tag separada | ❌ (embutido em `<formato>`) |
| Define Início | ✅ (implícito) |
| Define Fim | ✅ (implícito) |

**Agent tem (L127-133):**
```xml
<formato>
  - Iniciar com "RELATÓRIO" (com acento)
  - Terminar com "É o que havia de relevante a relatar."
</formato>
```

**Deveria ter:**
```xml
<sinalizadores>
  | Posição | Texto Obrigatório |
  |---------|-------------------|
  | Início  | "RELATÓRIO" |
  | Fim     | "É o que havia de relevante a relatar." |
</sinalizadores>
```

---

#### 4.3 `<exemplos>` (3/3)

| Item | Status |
|------|--------|
| Tag presente | ✅ |
| Exemplo de entrada | ⚠️ (implícito no formato) |
| Exemplo de saída | ✅ (completo, 20+ linhas) |

**Ponto forte:** Exemplo extenso e realista (L65-86).

---

#### 4.4 Extensões de Domínio (1/1)

Tags de domínio bem organizadas:
- `<pecas_relevantes>` - O que incluir/ignorar
- `<extracao>` - O que extrair de cada peça
- `<armadilha>` - Erros comuns a evitar
- `<formato>` - Regras de formatação
- `<leitura>` - Como processar documentos longos

---

### 1.5 Ausência de Anti-Patterns (0/10)

| Padrão Proibido | Encontrado? | Local |
|-----------------|-------------|-------|
| `processo.txt` | ✅ SIM | L4, comentário |
| `relatorio-marmelstein.md` | ✅ SIM | L5, L20 |
| `Read: caminho/específico` | ❌ Não | - |
| `Write: caminho/específico` | ❌ Não | - |
| Número de processo | ❌ Não | - |
| Referência a etapa | ✅ SIM | L1: "# ETAPA 01" |

**Score: 0/10** - Três violações encontradas.

---

## 2. Análise de Granularidade (META)

O usuário especificou que este agent deve ser **granular e reutilizável**:

> "A ideia é que ele receba o que tiver no workspace (pode ser só o processo.txt, pode ser o processo com a linha do tempo, pode ter até outros documentos a depender do pipeline)"

### 2.1 Análise do Agent Atual

| Aspecto | Status | Problema |
|---------|--------|----------|
| Assume `processo.txt` | ❌ | Nome fixo no comentário |
| Usa linha-tempo se disponível | ❌ | Nem menciona |
| Adapta-se a múltiplos documentos | ⚠️ | Menciona "documentos fornecidos" mas não estrutura |
| Entrada por tipo, não por nome | ❌ | Hardcoda filename |

### 2.2 Como Deveria Ser (Granular)

```xml
<contrato>
  <entrada>
    <tipo>Documentos processuais em texto</tipo>
    <formato>TXT ou MD</formato>
    <requisitos>
      OBRIGATÓRIO: Ao menos um arquivo com conteúdo processual (petição inicial, movimentação)
      OPCIONAL: Linha do tempo (se disponível, usar para ordenação cronológica)
      OPCIONAL: Outros documentos de análise prévia
    </requisitos>
  </entrada>
  <saida>
    <tipo>Relatório judicial estruturado</tipo>
    <formato>MD</formato>
  </saida>
</contrato>
```

### 2.3 Lacuna no Checklist Atual

O checklist v1.0 **NÃO verifica granularidade**. Proposta de nova seção:

```markdown
## 6. Modularidade e Granularidade (10 pontos)

### 6.1 Entrada Flexível (CRÍTICO - 5 pts)

[ ] Entrada descrita por TIPO, não por nome de arquivo?
[ ] Agent funciona com entrada mínima?
[ ] Agent aproveita entradas adicionais se disponíveis?
[ ] Nenhuma suposição sobre QUAIS arquivos existem?

### 6.2 Saída Genérica (ALTO - 5 pts)

[ ] Nome do arquivo de saída definido pelo orquestrador?
[ ] Agent não assume destino da saída?
[ ] Formato de saída independente do pipeline?
```

---

## 3. Calibração do Checklist (META-ANÁLISE)

Baseado nesta auditoria, identificamos lacunas no checklist atual:

### 3.1 Problemas Encontrados no Checklist v1.0

| # | Problema | Impacto | Proposta |
|---|----------|---------|----------|
| 1 | Não verifica granularidade | Agent pode estar hardcoded e passar | Adicionar seção 6 |
| 2 | Tag customizada ambígua | `<formato_saida_marmelstein>` é válido? | Clarificar regras de sufixo |
| 3 | Tags de domínio não listadas | `<pecas_relevantes>`, `<armadilha>` são válidas? | Documentar extensões permitidas |
| 4 | Nomenclatura v1 não detectada | `<persona>` vs `<identidade>` | Adicionar tabela de mapeamento v1→v2 |
| 5 | Comentários HTML ignorados | Pseudo-contrato em comentário passou | Verificar ausência de contratos em comentários |

### 3.2 Proposta de Atualização do Checklist

**Nova seção 6 - Modularidade e Granularidade:**
```
## 6. Modularidade e Granularidade (10 pontos)

### 6.1 Entrada Flexível (CRÍTICO - 5 pts)

[ ] Entrada definida por TIPO genérico, não nome de arquivo?
    ✅ Correto: <tipo>Documentos processuais em texto</tipo>
    ❌ Errado: ENTRADA: processo.txt

[ ] Agent funciona com entrada mínima?
    ✅ "Ao menos um documento processual"
    ❌ "Deve haver processo.txt e contestacao.txt"

[ ] Agent aproveita entradas opcionais?
    ✅ "Se houver linha-tempo, usar para ordenação"
    ❌ Ignora completamente outros arquivos

### 6.2 Saída Genérica (ALTO - 5 pts)

[ ] Saída definida por TIPO, não caminho?
    ✅ Correto: <tipo>Relatório estruturado</tipo>
    ❌ Errado: SAÍDA: relatorio-marmelstein.md

[ ] Formato independente do pipeline?
    ✅ Nome de arquivo definido pelo orquestrador
    ❌ Nome hardcoded no agent
```

**Adição à seção 5 - Anti-Patterns:**
```
### 5.2 Sem Pseudo-Contratos em Comentários (ALTO - 5 pts)

[ ] NENHUM comentário HTML/XML define entrada/saída?

Buscar padrões proibidos:
  ❌ <!-- ENTRADA: arquivo.txt -->
  ❌ <!-- SAÍDA: resultado.md -->
  ❌ // Input: data.json
```

**Adição ao guia - Mapeamento v1 → v2:**
```
### Tags Obsoletas (v1 → v2)

| Tag v1 (obsoleta) | Tag v2 (correta) |
|-------------------|------------------|
| <persona> | <identidade> |
| <objetivo> | <capacidade> + <contrato> |
| <regras> | <restricoes> |
| <instrucao> (singular) | <instrucoes> (plural) com <passo> |
```

---

## 4. Recomendações de Correção

### Prioridade 1 (CRÍTICA - Bloqueia uso em pipeline modular)

1. **Adicionar YAML frontmatter:**
   ```yaml
   ---
   name: relator-marmelstein
   description: Gera relatório judicial estruturado no formato Marmelstein
   tools: Read Write
   model: sonnet
   ---
   ```

2. **Substituir `<persona>` por `<identidade>`:**
   ```xml
   <identidade>
     <papel>Assistente jurídico especializado em extração e síntese processual</papel>
     <estilo>Metódico, detalhista, cronológico</estilo>
   </identidade>
   ```

3. **Substituir `<objetivo>` por `<capacidade>` + `<contrato>`:**
   ```xml
   <capacidade>
     <habilidade>Extrair e sintetizar atos processuais em relatório estruturado</habilidade>
     <especializacao>Direito previdenciário e processual civil</especializacao>
   </capacidade>

   <contrato>
     <entrada>
       <tipo>Documentos processuais em texto</tipo>
       <formato>TXT ou MD</formato>
       <requisitos>
         OBRIGATÓRIO: Conteúdo processual (petição, contestação, decisões)
         OPCIONAL: Linha do tempo (melhora ordenação cronológica)
         OPCIONAL: Análises prévias (contexto adicional)
       </requisitos>
     </entrada>
     <saida>
       <tipo>Relatório judicial estruturado</tipo>
       <formato>MD</formato>
     </saida>
   </contrato>
   ```

4. **Remover título de etapa:**
   - DE: `# ETAPA 01 - RELATÓRIO`
   - PARA: `# Agent: Relator Marmelstein`

5. **Remover comentário de pseudo-contrato:**
   - Deletar linhas 3-7 (comentário HTML)

### Prioridade 2 (ALTA - Afeta qualidade)

6. **Adicionar `<restricoes>` estruturadas:**
   ```xml
   <restricoes>
     - NÃO assumir caminhos de arquivo - recebe via contexto do orquestrador
     - NÃO incluir qualificação das partes (CPF, endereço)
     - NÃO reproduzir jurisprudência citada como argumento
     - NUNCA inventar informações não presentes nos documentos
     - SEMPRE incluir IDs de todas as peças citadas
     - SEMPRE usar português com acentos corretos
     - SEMPRE seguir ordem cronológica
   </restricoes>
   ```

7. **Adicionar `<contingencias>`:**
   ```xml
   <contingencias>
     <se_entrada_insuficiente>
       Se não houver petição inicial identificável, iniciar relatório com:
       "Não foi possível identificar petição inicial nos documentos fornecidos."
     </se_entrada_insuficiente>
     <se_ambiguo>
       Se houver múltiplos processos nos documentos, relatar apenas o principal
       (identificado pelo número no cabeçalho das peças).
     </se_ambiguo>
   </contingencias>
   ```

8. **Estruturar `<instrucoes>` com passos:**
   ```xml
   <instrucoes>
     <passo numero="1" nome="Receber entrada">
       Ler os documentos fornecidos pelo orquestrador.
       → A entrada vem via contexto, não de caminho fixo.
     </passo>
     <passo numero="2" nome="Identificar peças">
       Catalogar peças processuais relevantes (inicial, contestação, etc.)
       Ignorar peças de rotina (procurações, certidões, ARs).
     </passo>
     <passo numero="3" nome="Extrair informações">
       De cada peça relevante, extrair: datas, nomes, eventos, argumentos, pedidos.
     </passo>
     <passo numero="4" nome="Produzir relatório">
       Gerar relatório no formato Marmelstein especificado.
       → O destino é definido pelo orquestrador.
     </passo>
   </instrucoes>
   ```

### Prioridade 3 (MÉDIA - Padronização)

9. **Renomear `<formato_saida_marmelstein>` para `<formato_saida>`**

10. **Adicionar tag `<sinalizadores>` separada**

11. **Manter tags de domínio (estão boas):**
    - `<pecas_relevantes>` ✅
    - `<extracao>` ✅
    - `<armadilha>` ✅
    - `<formato>` ✅
    - `<leitura>` ✅

---

## 5. Score Projetado Após Correções

| Categoria | Atual | Projetado | Ganho |
|-----------|-------|-----------|-------|
| YAML Frontmatter | 0 | 30 | +30 |
| Localização | 10 | 10 | 0 |
| Tags Obrigatórias | 0 | 40 | +40 |
| Tags Recomendadas | 8 | 10 | +2 |
| Anti-Patterns | 0 | 10 | +10 |
| *Granularidade* | N/A | +10 | +10 |
| **TOTAL** | **18** | **100+10** | **+92** |

**Score projetado: 100/100** (ou 110/110 se nova seção de granularidade for adicionada)

---

## 6. Conclusões para Calibração do Pack

### 6.1 O que o Checklist Atual Captura Bem

- Presença de YAML frontmatter
- Localização correta de arquivos
- Tags obrigatórias estruturadas
- Anti-patterns de caminhos hardcoded

### 6.2 O que o Checklist Precisa Adicionar

1. **Seção de Granularidade** - Verificar se agent é reutilizável
2. **Mapeamento v1→v2** - Detectar tags obsoletas
3. **Verificação de pseudo-contratos** - Comentários não substituem tags
4. **Regras de customização de tags** - Quando sufixos são permitidos

### 6.3 Implicações para Outros Agents

Se `relator-marmelstein` (um dos agents mais maduros do projeto) tem score 18/100, é provável que **todos os outros agents do pipeline-sentenca precisem de refatoração similar**.

Recomenda-se auditar em sequência:
1. `linha-tempo-processual.md` (já ajustado para v2.1)
2. `analisador-marmelstein.md`
3. `pesquisador-julia.md`
4. `pesquisador-cjf.md`
5. `fundamentador.md`

---

**Auditoria realizada em:** 2026-01-18

---

## 7. Status da Correção

**Data da correção:** 2026-01-18

### Ações Realizadas

| # | Recomendação | Status |
|---|--------------|--------|
| 1 | Adicionar YAML frontmatter | ✅ CORRIGIDO |
| 2 | Substituir `<persona>` por `<identidade>` | ✅ CORRIGIDO |
| 3 | Substituir `<objetivo>` por `<capacidade>` + `<contrato>` | ✅ CORRIGIDO |
| 4 | Remover título de etapa | ✅ CORRIGIDO |
| 5 | Remover comentário de pseudo-contrato | ✅ CORRIGIDO |
| 6 | Adicionar `<restricoes>` estruturadas | ✅ CORRIGIDO |
| 7 | Adicionar `<contingencias>` | ✅ CORRIGIDO |
| 8 | Estruturar `<instrucoes>` com passos | ✅ CORRIGIDO |
| 9 | Renomear `<formato_saida_marmelstein>` | ✅ CORRIGIDO |
| 10 | Adicionar tag `<sinalizadores>` separada | ✅ CORRIGIDO |
| 11 | Manter tags de domínio | ✅ MANTIDO |

### Score Final

| Categoria | Antes | Depois |
|-----------|-------|--------|
| YAML Frontmatter | 0 | 30 |
| Localização | 10 | 10 |
| Tags Obrigatórias | 0 | 40 |
| Tags Recomendadas | 8 | 10 |
| Anti-Patterns | 0 | 20 |
| Granularidade | 0 | 10 |
| **TOTAL** | **18** | **120** |

**Classificação:** EXCELENTE (score perfeito)

### Artefatos Gerados

- `relator-marmelstein.md` - Agent corrigido
- `exemplo-agent-corrigido.md` - Referência com transformações documentadas
