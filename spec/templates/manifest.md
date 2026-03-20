# Template: Manifest (_manifest.md)

> **Propósito:** Índice do workspace que permite descoberta dinâmica de arquivos.
>
> **Localização:** `workspace/processo-XXX/_manifest.md`

---

## Por que usar Manifest?

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SEM MANIFEST                           COM MANIFEST                        │
│                                                                             │
│  Agent precisa saber:                   Agent lê _manifest.md:              │
│  - Qual arquivo de relatório?           - "relatorio.md existe"             │
│  - Qual extensão? .txt? .md?            - "analise/marmelstein.md existe"   │
│  - Já foi processado?                   - "status: aguardando revisão"      │
│                                                                             │
│  → Caminhos hardcoded                   → Descoberta dinâmica               │
│  → Frágil a mudanças                    → Flexível                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Princípio:** Manifest é o "mapa" do workspace. Subagente lê o manifest para descobrir o que existe.

---

## Template

```markdown
# Manifest: Processo [NUMERO]

> Criado em: [DATA_CRIACAO]
> Última atualização: [DATA_ATUALIZACAO]
> Status: [STATUS_GERAL]

---

## Identificação

| Campo | Valor |
|-------|-------|
| Processo | [NUMERO] |
| Classe | [CLASSE_PROCESSUAL] |
| Assunto | [ASSUNTO_PRINCIPAL] |
| Origem | [ORIGEM_DADOS] |

---

## Arquivos Disponíveis

### Entrada (dados brutos)

| Arquivo | Descrição | Status |
|---------|-----------|--------|
| `fonte/[NUMERO].txt` | Texto extraído do PDF | disponível |
| `fonte/anexos/` | Documentos anexos | [N] arquivos |

### Artefatos KANBAN (prefixo [NUMERO] - vão para frontend)

| Arquivo | Descrição | Status |
|---------|-----------|--------|
| `[NUMERO]-linha-tempo.md` | Cronologia processual | disponível |
| `[NUMERO]-analise.md` | Classificação e orientação | disponível |
| `[NUMERO]-minuta.md` | Sentença completa | disponível |

### Artefatos Intermediários (nome fixo - não vão para Kanban)

| Arquivo | Descrição | Status |
|---------|-----------|--------|
| `relatorio-marmelstein.md` | Relatório estruturado | disponível |
| `fundamentacao-marmelstein.md` | Fundamentação jurídica | disponível |

### Pesquisa

| Arquivo | Descrição | Status |
|---------|-----------|--------|
| `pesquisa/bnp.md` | Precedentes vinculantes | disponível |
| `pesquisa/cjf.md` | Jurisprudência STJ/TRFs | disponível |
| `pesquisa/julia.md` | Jurisprudência TRF5 | disponível |

### Revisão

| Arquivo | Descrição | Status |
|---------|-----------|--------|
| `revisao/advogado-diabo.md` | Análise crítica | pendente |
| `revisao/consistencia-interna.md` | Verificação vs autos | pendente |
| `revisao/consistencia-externa.md` | Verificação citações | pendente |

---

## Pipeline Executado

| Etapa | Comando | Data | Status |
|-------|---------|------|--------|
| 1 | /relatar-processo | [DATA] | concluído |
| 2 | /pesquisar-jurisprudencia | [DATA] | concluído |
| 3 | /analisar-caso | [DATA] | concluído |
| 4 | /sentenciar | [DATA] | em andamento |
| 5 | /revisar-sentenca | - | pendente |

---

## Notas

[Observações relevantes sobre o processo ou o andamento do pipeline]
```

---

## Guia de Preenchimento

### Seções Obrigatórias

| Seção | Propósito |
|-------|-----------|
| `## Identificação` | Dados básicos do processo |
| `## Arquivos Disponíveis` | Lista de arquivos com status |
| `## Pipeline Executado` | Histórico de etapas |

### Status de Arquivo

| Status | Significado |
|--------|-------------|
| `disponível` | Arquivo existe e está pronto para uso |
| `pendente` | Arquivo ainda não foi gerado |
| `em andamento` | Arquivo está sendo gerado |
| `erro` | Falha na geração |
| `[N] arquivos` | Pasta com N arquivos |

### Status Geral do Processo

| Status | Significado |
|--------|-------------|
| `em preparação` | Dados brutos disponíveis |
| `relatado` | Relatório gerado |
| `pesquisado` | Pesquisa concluída |
| `analisado` | Classificação concluída |
| `minutado` | Sentença em elaboração |
| `revisado` | Revisão concluída |
| `concluído` | Pipeline completo |

---

## Como o Orquestrador Usa o Manifest

### Criar Manifest (Etapa 0)

```xml
<passo numero="3" nome="Criar manifest inicial">
  Se $MANIFEST não existe:
    Write: $WORKSPACE/_manifest.md
    → Preencher com dados básicos
    → Status geral: "em preparação"
    → Arquivos: apenas entrada disponível
</passo>
```

### Atualizar Manifest (após cada etapa)

```xml
<passo numero="5" nome="Atualizar manifest">
  Read: $WORKSPACE/_manifest.md
  → Marcar arquivo gerado como "disponível"
  → Atualizar "Pipeline Executado"
  → Atualizar "Última atualização"
  Write: $WORKSPACE/_manifest.md
</passo>
```

### Subagente Lê Manifest (descoberta)

```xml
<passo numero="2" nome="Descobrir arquivos">
  Read: $WORKSPACE/_manifest.md
  → Identificar quais arquivos estão disponíveis
  → Usar caminhos listados no manifest
</passo>
```

---

## Estrutura de Pastas Padrão

```
workspace/
└── processo-12345/
    ├── _manifest.md                      # Índice do workspace
    ├── fonte/
    │   ├── 12345.txt                     # Texto extraído
    │   └── anexos/                       # Documentos anexos
    ├── 12345-relatorio.md                # Relatório estruturado
    ├── 12345-linha-tempo.md              # Cronologia processual
    ├── 12345-analise.md                  # Classificação e orientação
    ├── 12345-fundamentacao.md            # Fundamentação jurídica
    ├── 12345-sentenca.md                 # Sentença completa
    ├── pesquisa/
    │   ├── 12345-bnp.md                  # Precedentes vinculantes
    │   ├── 12345-cjf.md                  # Jurisprudência STJ/TRFs
    │   └── 12345-julia.md                # Jurisprudência TRF5
    └── revisao/
        ├── 12345-advogado-diabo.md       # Análise crítica
        ├── 12345-consistencia-interna.md # Verificação vs autos
        └── 12345-consistencia-externa.md # Verificação citações
```

**Convenção de Nomenclatura:** `[NUMERO]-tipo.md`

- O prefixo `[NUMERO]` é o número do processo (completo ou abreviado)
- Facilita busca por arquivos relacionados ao mesmo processo
- Evita colisão de nomes em workspaces compartilhados

---

## Checklist de Validação

```
[ ] Arquivo nomeado _manifest.md (com underscore)?
[ ] Seção Identificação com dados do processo?
[ ] Seção Arquivos Disponíveis com status de cada arquivo?
[ ] Seção Pipeline Executado com histórico?
[ ] Status geral reflete o estado atual?
[ ] Caminhos são relativos ao workspace (não absolutos)?
[ ] Atualizado após cada etapa do pipeline?
```
