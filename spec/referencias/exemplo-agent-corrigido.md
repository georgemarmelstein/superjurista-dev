# Referência: Exemplo de Agent Corrigido (v2.0)

> **Propósito:** Exemplo real de agent que passou pela auditoria e foi corrigido.
>
> **Agent de origem:** `relator-marmelstein.md`
>
> **Score antes:** 18/120 (REPROVADO)
> **Score depois:** 120/120 (EXCELENTE)

---

## Transformações Aplicadas

### 1. YAML Frontmatter (0 → 30 pts)

**ANTES:** Ausente

**DEPOIS:**
```yaml
---
name: relator-marmelstein
description: Gera relatório judicial estruturado no formato Marmelstein a partir de documentos processuais
tools: Read Write
model: sonnet
---
```

**Regras:**
- `name`: kebab-case, reflete CAPACIDADE (não pipeline/etapa)
- `description`: uma linha, descreve O QUE faz
- `tools`: separadas por ESPAÇO (não vírgula)
- `model`: haiku, sonnet ou opus

---

### 2. Título (ETAPA → Agent)

**ANTES:**
```markdown
# ETAPA 01 - RELATÓRIO
```

**DEPOIS:**
```markdown
# Agent: Relator Marmelstein
```

**Regra:** Agent não sabe em qual etapa está. Nome reflete capacidade.

---

### 3. Pseudo-contrato em comentário → Tag `<contrato>`

**ANTES:**
```html
<!--
ENTRADA: processo.txt
SAÍDA: relatorio-marmelstein.md
CONTEXTO: Apenas o processo
-->
```

**DEPOIS:**
```xml
<contrato>
  <entrada>
    <tipo>Documentos processuais em texto</tipo>
    <formato>TXT ou MD</formato>
    <requisitos>
      OBRIGATÓRIO: Ao menos um arquivo com conteúdo processual
      OPCIONAL: Linha do tempo processual
      OPCIONAL: Outros documentos de contexto
    </requisitos>
  </entrada>
  <saida>
    <tipo>Relatório judicial estruturado no formato Marmelstein</tipo>
    <formato>MD</formato>
  </saida>
</contrato>
```

**Regras:**
- Entrada definida por TIPO, não por nome de arquivo
- Requisitos indicam o que é OBRIGATÓRIO vs OPCIONAL
- Saída genérica - nome do arquivo definido pelo orquestrador

---

### 4. Tag `<persona>` → `<identidade>`

**ANTES:**
```xml
<persona>
Você é um ASSISTENTE JURÍDICO DE ALTO NÍVEL especializado em...
</persona>
```

**DEPOIS:**
```xml
<identidade>
  <papel>
    Assistente jurídico de alto nível especializado em escrita jurídica...
  </papel>
  <estilo>
    Metódico, detalhista e cronológico...
  </estilo>
</identidade>
```

**Regras:**
- Tag `<identidade>` (não `<persona>`)
- Subtags `<papel>` e `<estilo>` obrigatórias
- Sem texto solto fora das subtags

---

### 5. Tag `<objetivo>` → `<capacidade>`

**ANTES:**
```xml
<objetivo>
Sua tarefa é realizar uma LEITURA abrangente...
**Você DEVE entregar:**
1. Arquivo `relatorio-marmelstein.md`...
</objetivo>
```

**DEPOIS:**
```xml
<capacidade>
  <habilidade>
    Extrair e sintetizar atos processuais em relatório judicial estruturado
  </habilidade>
  <especializacao>
    Direito previdenciário, processual civil e análise de documentos extensos
  </especializacao>
</capacidade>
```

**Regras:**
- Tag `<capacidade>` (não `<objetivo>`)
- `<habilidade>`: verbo no infinitivo + O QUE faz
- `<especializacao>`: área de conhecimento
- NÃO menciona arquivos específicos

---

### 6. Nova tag `<restricoes>` estruturada

**ANTES:** Restrições espalhadas em outras tags

**DEPOIS:**
```xml
<restricoes>
  - NÃO assumir caminhos de arquivo - recebe via contexto do orquestrador
  - NÃO incluir qualificação das partes (CPF, RG, endereço)
  - NUNCA inventar informações não presentes nos documentos
  - SEMPRE incluir IDs de todas as peças citadas
  - SEMPRE usar português com acentos corretos
</restricoes>
```

**Regras:**
- Prefixos NÃO/NUNCA/SEMPRE obrigatórios
- DEVE incluir "NÃO assumir caminhos de arquivo"
- DEVE incluir "SEMPRE usar português com acentos"

---

### 7. Nova tag `<contingencias>`

**ANTES:** Ausente

**DEPOIS:**
```xml
<contingencias>
  <se_entrada_insuficiente>
    Se não houver petição inicial identificável:
    - Iniciar relatório com: "Não foi possível identificar petição inicial..."
    - Relatar as peças que ESTIVEREM disponíveis
  </se_entrada_insuficiente>
  <se_ambiguo>
    Se houver documentos de múltiplos processos:
    - Relatar APENAS o processo principal
    - Ignorar peças de outros processos anexadas
  </se_ambiguo>
</contingencias>
```

**Regras:**
- Define comportamento em cenários de falha
- Subtags nomeadas por cenário
- Ações específicas e executáveis

---

### 8. Nova tag `<instrucoes>` com passos

**ANTES:** Tags não estruturadas (`<leitura>`, `<extracao>`, etc.)

**DEPOIS:**
```xml
<instrucoes>
  <passo numero="1" nome="Receber entrada">
    Ler os documentos processuais fornecidos pelo orquestrador.
    → A entrada vem via contexto, não de caminho fixo.
  </passo>
  <passo numero="2" nome="Identificar peças relevantes">
    Catalogar as peças processuais presentes nos documentos...
  </passo>
  <passo numero="3" nome="Extrair informações">
    De cada peça relevante, extrair COM PROFUNDIDADE...
  </passo>
  <passo numero="4" nome="Produzir relatório">
    Gerar relatório no formato especificado.
    → O nome e destino do arquivo são definidos pelo orquestrador.
  </passo>
</instrucoes>
```

**Regras:**
- Subtag `<passo>` com atributos `numero` e `nome`
- Passo 1 sempre menciona "receber entrada via contexto"
- Último passo menciona que destino é definido pelo orquestrador

---

### 9. Renomeação de tag customizada

**ANTES:** `<formato_saida_marmelstein>`

**DEPOIS:** `<formato_saida>`

**Regra:** Usar nome padrão do spec. Sufixos customizados permitidos apenas se necessário para desambiguação.

---

### 10. Nova tag `<sinalizadores>` separada

**ANTES:** Sinalizadores embutidos em `<formato>`

**DEPOIS:**
```xml
<sinalizadores>
  | Posição | Texto Obrigatório |
  |---------|-------------------|
  | Início  | "RELATÓRIO" |
  | Fim     | "É o que havia de relevante a relatar." |
</sinalizadores>
```

**Regras:**
- Tag separada, não embutida
- Formato de tabela markdown
- Define marcadores para validação

---

### 11. Tags de domínio reorganizadas

**ANTES:** `<pecas_relevantes>`, `<extracao>`, `<armadilha>`, `<formato>`, `<leitura>`

**DEPOIS:** Agrupadas em `<conhecimento_dominio>`:
```xml
<conhecimento_dominio>
  <pecas_relevantes>...</pecas_relevantes>
  <armadilhas>...</armadilhas>
  <regras_formato>...</regras_formato>
</conhecimento_dominio>
```

**Regra:** Tags de domínio são permitidas e encorajadas, mas devem ser agrupadas logicamente.

---

## Checklist de Verificação Final

```
YAML Frontmatter (30 pts):
[x] Bloco YAML presente com ---
[x] Campo name em kebab-case
[x] Campo description presente
[x] Campo tools com espaço (não vírgula)
[x] Campo model presente

Localização (10 pts):
[x] Em .claude/agents/ ou subpasta por categoria

Tags Obrigatórias (40 pts):
[x] <identidade> com <papel> e <estilo>
[x] <capacidade> com <habilidade> e <especializacao>
[x] <contrato> com <entrada> e <saida>
[x] <restricoes> com prefixos NÃO/NUNCA/SEMPRE
[x] <contingencias> com cenários de falha
[x] <instrucoes> com <passo> numerados

Tags Recomendadas (10 pts):
[x] <formato_saida> com template
[x] <sinalizadores> com início/fim
[x] <exemplos> com entrada/saída

Ausência de Anti-Patterns (20 pts):
[x] ZERO caminhos hardcoded
[x] ZERO pseudo-contratos em comentários
[x] ZERO tags v1 obsoletas

Granularidade (10 pts):
[x] Entrada por TIPO, não nome de arquivo
[x] Saída genérica
[x] Aproveita entradas opcionais

TOTAL: 120/120 (EXCELENTE)
```

---

## Comparativo Visual

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ANTES (v1 - 18/120)                 │  DEPOIS (v2 - 120/120)              │
├─────────────────────────────────────────────────────────────────────────────┤
│  # ETAPA 01 - RELATÓRIO              │  ---                                │
│                                       │  name: relator-marmelstein         │
│  <!-- ENTRADA: processo.txt -->       │  description: Gera relatório...    │
│                                       │  tools: Read Write                 │
│  <persona>                            │  model: sonnet                     │
│    Você é um ASSISTENTE...            │  ---                               │
│  </persona>                           │                                    │
│                                       │  # Agent: Relator Marmelstein      │
│  <objetivo>                           │                                    │
│    Sua tarefa é realizar...           │  <identidade>                      │
│    Arquivo relatorio-marmelstein.md   │    <papel>...</papel>              │
│  </objetivo>                          │    <estilo>...</estilo>            │
│                                       │  </identidade>                     │
│  <formato_saida_marmelstein>          │                                    │
│    ...                                │  <capacidade>                      │
│  </formato_saida_marmelstein>         │    <habilidade>...</habilidade>    │
│                                       │    <especializacao>...</esp...>    │
│  (sem <restricoes>)                   │  </capacidade>                     │
│  (sem <contingencias>)                │                                    │
│  (sem <instrucoes>)                   │  <contrato>                        │
│  (sem <sinalizadores>)                │    <entrada>                       │
│                                       │      <tipo>Documentos...</tipo>    │
│                                       │    </entrada>                      │
│                                       │    <saida>...</saida>              │
│                                       │  </contrato>                       │
│                                       │                                    │
│                                       │  <restricoes>...</restricoes>      │
│                                       │  <contingencias>...</conting...>   │
│                                       │  <instrucoes>...</instrucoes>      │
│                                       │  <formato_saida>...</formato>      │
│                                       │  <sinalizadores>...</sinaliz...>   │
│                                       │  <exemplos>...</exemplos>          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

**Versão:** 1.0
**Data:** 2026-01-18
**Baseado em:** Auditoria de relator-marmelstein.md
