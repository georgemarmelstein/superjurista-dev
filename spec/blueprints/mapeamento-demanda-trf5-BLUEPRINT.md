# Blueprint: mapeamento-demanda-trf5

**Gerado por:** /planejar-sistema
**Data:** 2026-01-31
**Categoria:** Jurídico/Estatístico

---

## 1. Visão Geral

**Objetivo:** Mapear a demanda real do TRF5 para subsidiar a especialização de turmas em núcleos temáticos, classificando ~5.000 ementas de 2025 com eficiência de tokens.

**Entrada:**
- JSON com ementas brutas do JULIA (já baixadas, com duplicatas)
- Lista de etiquetas temáticas (a fornecer)

**Saída:**
- Dashboard interativo (app web React)
- Relatório analítico (MD/PDF)
- Planilha com dados brutos (XLSX)

**Desafio Principal:** Processar ~5.000 ementas (~2 páginas cada = ~20-30M tokens) com qualidade de classificação e mínimo desperdício.

---

## 2. Estratégia de Eficiência de Tokens

### 2.1. Problema

| Métrica | Valor |
|---------|-------|
| Ementas | ~5.000 |
| Tamanho médio | ~2 páginas (~1.500 tokens) |
| Total bruto | ~7.5M tokens de entrada |
| Se incluir prompt | ~10-15M tokens |
| Custo Sonnet (input) | $3/1M → ~$30-45 |
| Custo Opus (input) | $15/1M → ~$150-225 |

### 2.2. Estratégias Implementadas

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ESTRATÉGIA 1: EXTRAÇÃO PRÉ-CLASSIFICAÇÃO                                   │
│  ─────────────────────────────────────────                                  │
│  Antes de classificar, extrair APENAS:                                      │
│  - Objeto da ação (1 linha)                                                 │
│  - Pedido principal (1-2 linhas)                                            │
│  - Decisão (provido/improvido)                                              │
│  - Turma julgadora                                                          │
│                                                                             │
│  Redução: ~1.500 tokens → ~100 tokens (93% economia)                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  ESTRATÉGIA 2: BATCHING INTELIGENTE                                         │
│  ───────────────────────────────────                                        │
│  Ao invés de: 1 prompt por ementa (5.000 chamadas)                          │
│  Fazer: 50 ementas por prompt (100 chamadas)                                │
│                                                                             │
│  Economia em overhead de sistema + melhor uso do contexto                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  ESTRATÉGIA 3: CLASSIFICADOR HIERÁRQUICO                                    │
│  ────────────────────────────────────────                                   │
│  Nível 1 (Haiku): Classificação grosseira em 3 núcleos                      │
│           ↓ 90% das ementas resolvidas aqui                                 │
│  Nível 2 (Sonnet): Casos ambíguos → classificação fina                      │
│           ↓ ~10% das ementas                                                │
│  Nível 3 (Opus): Casos limítrofes para validação                            │
│           ↓ ~1% das ementas                                                 │
│                                                                             │
│  Custo médio: (0.90 × Haiku) + (0.09 × Sonnet) + (0.01 × Opus)              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  ESTRATÉGIA 4: CHECKPOINTS E PERSISTÊNCIA                                   │
│  ─────────────────────────────────────────                                  │
│  - Salvar progresso a cada 100 ementas                                      │
│  - Se falhar, retomar do último checkpoint                                  │
│  - Nunca reprocessar o que já foi classificado                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.3. Estimativa de Custo Final

| Estratégia | Tokens | Custo Estimado |
|------------|--------|----------------|
| Naive (Sonnet, 1 por 1) | ~15M | ~$45 |
| Com extração prévia | ~1.5M | ~$4.50 |
| Com batching (50/prompt) | ~800K | ~$2.40 |
| Com hierarquia (Haiku→Sonnet) | ~500K médio | ~$0.50 |

**Economia total: ~99%**

---

## 3. Diagrama de Arquitetura

```
[ENTRADA: ementas_brutas.json + etiquetas.json]
    │
    ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  ORQUESTRADOR: /pipeline-mapeamento-trf5                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ ETAPA 1  │───▶│ ETAPA 2  │───▶│ ETAPA 3  │───▶│ ETAPA 4  │              │
│  │ Dedupl.  │    │ Extração │    │ Classif. │    │ Análise  │              │
│  │          │    │          │    │ Hierárq. │    │ Quant.   │              │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘              │
│       │              │              │                 │                     │
│       ▼              ▼              ▼                 ▼                     │
│  ementas_        ementas_       ementas_          analise.json             │
│  unicas.json     resumidas.json classificadas.json                         │
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                              │
│  │ ETAPA 5  │───▶│ ETAPA 6  │───▶│ ETAPA 7  │                              │
│  │ Dashboard│    │ Relatório│    │ Planilha │                              │
│  │ (React)  │    │ (MD/PDF) │    │ (XLSX)   │                              │
│  └──────────┘    └──────────┘    └──────────┘                              │
│       │              │              │                                       │
│       ▼              ▼              ▼                                       │
│  frontend/dist   relatorio.md   dados.xlsx                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
    │
    ▼
[SAÍDAS: Dashboard + Relatório + Planilha]
```

---

## 4. Especificação de Etapas

### ETAPA 1: Deduplicação

| Campo | Valor |
|-------|-------|
| **Capacidade** | Agrupar ementas por número de processo, selecionar mais antiga |
| **Tipo** | Script Python (não precisa de LLM) |
| **Entrada** | `ementas_brutas.json` |
| **Saída** | `ementas_unicas.json` |
| **Lógica** | GROUP BY numero_processo, ORDER BY data_julgamento ASC, LIMIT 1 |
| **Categoria** | Script |
| **Status** | ❌ CRIAR |

```python
# Pseudocódigo
def deduplicar(ementas):
    grupos = defaultdict(list)
    for e in ementas:
        grupos[e['numero_processo']].append(e)

    unicas = []
    for numero, lista in grupos.items():
        mais_antiga = min(lista, key=lambda x: x['data_julgamento'])
        unicas.append(mais_antiga)

    return unicas
```

---

### ETAPA 2: Extração de Resumo

| Campo | Valor |
|-------|-------|
| **Capacidade** | Extrair objeto, pedido, decisão de cada ementa (reduzir tokens) |
| **Tipo** | Agent LLM (Haiku - rápido e barato) |
| **Entrada** | `ementas_unicas.json` (texto completo) |
| **Saída** | `ementas_resumidas.json` (objeto+pedido+decisão) |
| **Modelo** | Haiku (extração simples) |
| **Batching** | 50 ementas por prompt |
| **Categoria** | extracao |
| **Status** | ❌ CRIAR |

**Formato do Resumo:**
```json
{
  "numero_processo": "0800123-45.2024.4.05.8100",
  "turma": "1a TURMA",
  "data_julgamento": "2025-01-15",
  "objeto": "Aposentadoria por idade rural",
  "pedido": "Concessão de benefício desde o requerimento administrativo",
  "decisao": "PROVIDO",
  "tokens_originais": 1523,
  "tokens_resumo": 87
}
```

---

### ETAPA 3: Classificação Hierárquica

| Campo | Valor |
|-------|-------|
| **Capacidade** | Classificar resumos nas etiquetas temáticas com cascata de modelos |
| **Tipo** | Agent LLM (Haiku → Sonnet → Opus) |
| **Entrada** | `ementas_resumidas.json` + `etiquetas.json` |
| **Saída** | `ementas_classificadas.json` |
| **Modelo** | Cascata: 90% Haiku, 9% Sonnet, 1% Opus |
| **Batching** | 50 resumos por prompt (nível 1) |
| **Categoria** | analise |
| **Status** | ❌ CRIAR |

**Fluxo de Classificação:**
```
┌─────────────────┐
│ NÍVEL 1: Haiku  │  Confiança ≥ 0.8? ──▶ ✅ Classificado
│ (50 por batch)  │         │
└─────────────────┘         ▼ Confiança < 0.8
                    ┌─────────────────┐
                    │ NÍVEL 2: Sonnet │  Confiança ≥ 0.7? ──▶ ✅ Classificado
                    │ (1 por 1)       │         │
                    └─────────────────┘         ▼ Confiança < 0.7
                                        ┌─────────────────┐
                                        │ NÍVEL 3: Opus   │ ──▶ ✅ Classificado
                                        │ (revisão final) │     ou ⚠️ "Inclassificável"
                                        └─────────────────┘
```

**Formato da Classificação:**
```json
{
  "numero_processo": "0800123-45.2024.4.05.8100",
  "etiqueta_principal": "PREVIDENCIÁRIO - Aposentadoria Rural",
  "etiquetas_secundarias": ["PROVA - Início de prova material"],
  "confianca": 0.95,
  "modelo_usado": "haiku",
  "justificativa": "Pedido de aposentadoria por idade rural com discussão de início de prova material"
}
```

---

### ETAPA 4: Análise Quantitativa

| Campo | Valor |
|-------|-------|
| **Capacidade** | Agregar classificações, calcular estatísticas, gerar insights |
| **Tipo** | Script Python (pandas + análise) |
| **Entrada** | `ementas_classificadas.json` |
| **Saída** | `analise.json` |
| **Categoria** | Script |
| **Status** | ❌ CRIAR |

**Agregações:**
```json
{
  "total_ementas": 5234,
  "por_turma": {
    "1a TURMA": {"total": 748, "etiquetas": {...}},
    "2a TURMA": {"total": 721, "etiquetas": {...}}
  },
  "por_etiqueta": {
    "PREVIDENCIÁRIO - Aposentadoria Rural": {"total": 1234, "turmas": {...}},
    "TRIBUTÁRIO - Execução Fiscal": {"total": 892, "turmas": {...}}
  },
  "cruzamentos": {
    "etiqueta_turma": [[...]],
    "tendencias_mensais": [...]
  },
  "insights": [
    "1a Turma concentra 67% dos casos previdenciários",
    "Tributário distribuído uniformemente entre turmas"
  ]
}
```

---

### ETAPA 5: Dashboard Interativo

| Campo | Valor |
|-------|-------|
| **Capacidade** | Gerar frontend React com gráficos interativos |
| **Tipo** | Geração de código (React + Chart.js/Recharts) |
| **Entrada** | `analise.json` |
| **Saída** | `frontend/dist/` (build de produção) |
| **Categoria** | Geração |
| **Status** | ❌ CRIAR |

**Features do Dashboard:**
- Filtros por turma, etiqueta, período
- Gráficos: pizza (distribuição), barras (comparativo), linha (tendência temporal)
- Tabela com busca e paginação
- Exportação para CSV/PDF

---

### ETAPA 6: Relatório Analítico

| Campo | Valor |
|-------|-------|
| **Capacidade** | Gerar relatório narrativo MD com visualizações |
| **Tipo** | Agent LLM (Sonnet - redação) |
| **Entrada** | `analise.json` |
| **Saída** | `relatorio.md` |
| **Modelo** | Sonnet |
| **Categoria** | redacao |
| **Status** | ❌ CRIAR |

**Estrutura do Relatório:**
```markdown
# Relatório de Mapeamento de Demandas - TRF5 (2025)

## Sumário Executivo
[Principais achados em 1 página]

## Metodologia
[Descrição do processo de coleta e classificação]

## Distribuição por Núcleo Temático
[Gráficos + análise]

## Distribuição por Turma
[Gráficos + análise]

## Recomendações para Especialização
[Sugestões baseadas nos dados]

## Anexos
[Tabelas detalhadas]
```

---

### ETAPA 7: Planilha Analítica

| Campo | Valor |
|-------|-------|
| **Capacidade** | Gerar XLSX com dados brutos e tabelas dinâmicas |
| **Tipo** | Script Python (openpyxl) |
| **Entrada** | `ementas_classificadas.json` + `analise.json` |
| **Saída** | `dados.xlsx` |
| **Categoria** | Script |
| **Status** | ❌ CRIAR |

**Abas da Planilha:**
1. **Dados Brutos** - Todas as ementas com classificações
2. **Por Turma** - Pivot: turma × etiqueta
3. **Por Etiqueta** - Pivot: etiqueta × turma
4. **Tendência Mensal** - Série temporal
5. **Resumo** - KPIs principais

---

## 5. Especificação de Agents

| # | Nome | Capacidade | Categoria | Modelo | Status |
|---|------|------------|-----------|--------|--------|
| 1 | Script | Deduplicar ementas por número, manter mais antiga | - | Python | ❌ CRIAR |
| 2 | extrator-resumo-ementa | Extrair objeto+pedido+decisão de ementa | extracao | Haiku | ❌ CRIAR |
| 3 | classificador-tematico | Classificar resumo em etiquetas com confiança | analise | Cascata | ❌ CRIAR |
| 4 | Script | Agregar classificações em estatísticas | - | Python | ❌ CRIAR |
| 5 | Geração | Dashboard React interativo | - | Claude | ❌ CRIAR |
| 6 | relator-analitico | Gerar relatório narrativo de análise | redacao | Sonnet | ❌ CRIAR |
| 7 | Script | Gerar planilha XLSX | - | Python | ❌ CRIAR |

**Legenda:**
- **Script**: Não precisa de agent, é código Python puro
- **Agent**: Usa LLM via Task tool
- **Geração**: Claude gera código do zero (não é agent reutilizável)

---

## 6. Contratos de Dados

| # | Etapa | Entrada | Saída | Validação |
|---|-------|---------|-------|-----------|
| 0 | Preparação | Args (caminhos) | $WORKSPACE calculado | Diretório existe |
| 1 | Deduplicação | `ementas_brutas.json` | `ementas_unicas.json` | total_unicas < total_brutas |
| 2 | Extração | `ementas_unicas.json` | `ementas_resumidas.json` | todos têm objeto+pedido+decisao |
| 3 | Classificação | `ementas_resumidas.json` | `ementas_classificadas.json` | todos têm etiqueta_principal |
| 4 | Análise | `ementas_classificadas.json` | `analise.json` | total_por_turma = total_geral |
| 5 | Dashboard | `analise.json` | `frontend/dist/index.html` | HTML existe |
| 6 | Relatório | `analise.json` | `relatorio.md` | sinalizadores presentes |
| 7 | Planilha | `*.json` | `dados.xlsx` | arquivo abre no Excel |

---

## 7. Sinalizadores de Formato

| Etapa | Início Obrigatório | Fim Obrigatório |
|-------|-------------------|-----------------|
| 2 (Extração) | `[INICIO_EXTRACAO]` | `[FIM_EXTRACAO]` |
| 3 (Classificação) | `[INICIO_CLASSIFICACAO]` | `[FIM_CLASSIFICACAO]` |
| 6 (Relatório) | `# Relatório de Mapeamento` | `---FIM DO RELATÓRIO---` |

---

## 8. Estrutura de Arquivos

```
data/mapeamento-trf5/
├── input/
│   ├── ementas_brutas.json      # Entrada original (com duplicatas)
│   └── etiquetas.json           # Lista de categorias temáticas
│
├── processado/
│   ├── ementas_unicas.json      # Após deduplicação
│   ├── ementas_resumidas.json   # Após extração (tokens reduzidos)
│   ├── ementas_classificadas.json # Após classificação
│   └── analise.json             # Agregações e estatísticas
│
├── output/
│   ├── relatorio.md             # Relatório narrativo
│   ├── dados.xlsx               # Planilha analítica
│   └── dashboard/               # Build do frontend
│       ├── index.html
│       └── assets/
│
└── checkpoints/                 # Para retomada em caso de falha
    ├── classificacao_batch_001.json
    ├── classificacao_batch_002.json
    └── ...
```

---

## 9. Checklist de Implementação

### Fase 1: Preparação

```bash
# 1.1 Criar estrutura de diretórios
mkdir -p data/mapeamento-trf5/{input,processado,output,checkpoints}

# 1.2 Colocar arquivo de entrada
# Usuário deve fornecer: data/mapeamento-trf5/input/ementas_brutas.json

# 1.3 Definir etiquetas
# Usuário deve criar: data/mapeamento-trf5/input/etiquetas.json
```

### Fase 2: Criar Scripts de Processamento

| Arquivo | Descrição | Comando para criar |
|---------|-----------|-------------------|
| `scripts/deduplicar.py` | Agrupa por processo, seleciona mais antiga | Manual |
| `scripts/analisar.py` | Gera estatísticas e agregações | Manual |
| `scripts/gerar_xlsx.py` | Cria planilha Excel | Manual |

### Fase 3: Criar Agents

```bash
# 3.1 Extrator de resumo
/criar-agente extrator-resumo-ementa --capacidade "Extrair objeto, pedido e decisão de ementa judicial para reduzir tokens"

# 3.2 Classificador temático
/criar-agente classificador-tematico --capacidade "Classificar resumo de ementa em etiquetas temáticas com score de confiança"

# 3.3 Relator analítico
/criar-agente relator-analitico --capacidade "Gerar relatório narrativo a partir de dados quantitativos"
```

### Fase 4: Criar Orquestrador

```bash
/criar-orquestrador pipeline-mapeamento-trf5
```

### Fase 5: Criar Dashboard

```bash
# Claude gera código React durante execução do pipeline
# ou pode ser criado separadamente com Claude
```

### Fase 6: Testar

```bash
# Teste com amostra pequena (100 ementas)
/pipeline-mapeamento-trf5 data/mapeamento-trf5-teste

# Verificar saídas
ls data/mapeamento-trf5-teste/output/
```

---

## 10. Notas de Design

### Decisões Arquiteturais

1. **Scripts vs Agents**: Operações determinísticas (deduplicação, agregação) são scripts Python. Apenas tarefas que requerem compreensão semântica usam LLM.

2. **Cascata de Modelos**: Haiku primeiro (barato), escala para Sonnet/Opus apenas quando necessário. Isso otimiza custo sem sacrificar qualidade.

3. **Batching**: 50 ementas por prompt reduz overhead de sistema e melhora throughput.

4. **Checkpoints**: Permite retomar processamento após falhas sem retrabalho.

### Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|---------------|-----------|
| Classificação incorreta | Média | Validação manual de amostra, ajuste de prompt |
| Timeout em batches grandes | Baixa | Reduzir batch size, aumentar timeout |
| Custo excede orçamento | Baixa | Monitorar tokens, ajustar cascata |
| Etiquetas não cobrem casos | Média | Categoria "Outros" + revisão posterior |

### Considerações Futuras

- **Embedding + Clustering**: Se etiquetas não forem pré-definidas, usar embeddings para descobrir clusters automaticamente
- **Fine-tuning**: Se volume crescer, treinar modelo específico para classificação TRF5
- **API**: Expor classificador como serviço para uso contínuo

---

## 11. Próximos Passos Imediatos

1. **Usuário fornece:**
   - Arquivo `ementas_brutas.json` (ou caminho para existente)
   - Arquivo `etiquetas.json` com lista de categorias

2. **Criar scripts de processamento** (deduplicar, analisar, xlsx)

3. **Criar agents** (extrator, classificador, relator)

4. **Criar orquestrador** `/pipeline-mapeamento-trf5`

5. **Testar com amostra pequena** (~100 ementas)

6. **Executar em escala** (~5.000 ementas)

---

**Próximo Passo:** Forneça o arquivo de etiquetas ou indique se deseja que eu proponha uma estrutura inicial baseada nos núcleos temáticos do TRF5.
