# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Propósito do Projeto

**SuperJurista** é um sistema agêntico para processamento de processos judiciais, construído com arquitetura de pipelines determinísticos. Implementa **Inteligência Aumentada** que potencializa o trabalho do magistrado sem substituí-lo.

## Arquitetura: Orquestrador Cego com Injeção de Contexto

```
┌──────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│  $ARGUMENTS  │────▶│    ORQUESTRADOR      │────▶│    SUBAGENTES    │
│  (usuário)   │     │  (calcula $WORKSPACE │     │  (recebem        │
│              │     │   e $NUMERO)         │     │   caminhos       │
│              │     │                      │     │   prontos)       │
└──────────────┘     └──────────────────────┘     └──────────────────┘
```

**Princípios:**
- Commands (orquestradores) delegam via Task tool, não contêm prompts inline
- Agents definem CAPACIDADE, orquestradores injetam CONTEXTO
- Subagentes leem seus próprios prompts via Read tool (contexto isolado)
- Validação obrigatória por sinalizadores entre etapas
- Skills com `context: fork` isolam output verboso de scripts

## Estrutura de Diretórios

```
.claude/
├── commands/           # ORQUESTRADORES (entry points via /comando)
├── agents/             # SUBAGENTES por categoria
│   ├── extracao/       # linha-tempo, relator, seletor-documentos, super-conversor
│   ├── analise/        # marmelstein, haack, pearl, embargos, hootly, probatica
│   ├── pesquisa/       # bnp, cjf, julia, consolidador
│   ├── redacao/        # redator-minuta-robustecida
│   ├── revisao/        # verificadores (calculos, honorarios, remessa, fontes)
│   └── lista-trf/      # agentes para análise de listas de julgamento
├── skills/             # CONHECIMENTO + SCRIPTS
│   ├── pje-download/   # API REST do PJE (scripts Python)
│   ├── converter-pdf/  # Conversão PDF→TXT com OCR híbrido
│   ├── capturar-sessao-pje/  # Captura sessão via Chrome MCP
│   ├── criar-mcp-precedente/ # Criação de MCPs de jurisprudência
│   └── fork-terminal/  # Execução paralela em terminais
└── mcp-servers/        # SERVIDORES MCP LOCAIS
    └── tjsc-eproc/     # Jurisprudência TJSC via eProc (público)

data/                   # SAÍDAS DO SISTEMA
├── sentenca/           # Processos para sentença
│   └── <numero-processo>/
│       ├── processo.txt          # Entrada (texto extraído)
│       └── <numero>-*.md         # Artefatos gerados
└── decisao/            # Processos para decisão
```

## Comandos Disponíveis

### Pipelines Principais

| Comando | Descrição |
|---------|-----------|
| `/pipeline-sentenca` | Pipeline completo de sentença (6 etapas) |
| `/pipeline-sentenca-team` | Versão com Agent Teams (pesquisa paralela) |
| `/pipeline-embargos` | Pipeline de embargos de declaração |
| `/pipeline-pesquisa` | Pesquisa paralela em BNP, CJF e JULIA |
| `/pipeline-probatica` | Análise probabilística de provas (Haack/Pearl) |
| `/pipeline-minutar-pdf` | PDF para sentença completa |
| `/pipeline-revisao-minuta` | Revisão e validação final |

### Download e Conversão

| Comando | Descrição |
|---------|-----------|
| `/baixar-pje` | Baixa processos do PJE via API |
| `/baixar-converter` | Baixa e converte para TXT |
| `/baixar-inteligente` | Download com seleção por LLM |

### Utilidades

| Comando | Descrição |
|---------|-----------|
| `/relatar-processo` | Linha do tempo + relatório |
| `/analisar-lista` | Análise de lista de julgamento TRF5 (9 etapas) |
| `/fork-terminal` | Execução paralela em terminais Windows |
| `/planejamento-epistemico` | Planejamento estruturado de pesquisa |

## Execução de Scripts Python

```bash
# Listar processos do PJE
python .claude/skills/pje-download/scripts/listar_processos.py \
  --cookies pje_session.json --modo sentenca --limite 5 --output processos.json

# Baixar PDFs (várias opções)
python .claude/skills/pje-download/scripts/baixar_pdfs.py \
  --cookies pje_session.json --processos processos.json --output data/sentenca

python .claude/skills/pje-download/scripts/baixar_por_tipo.py \
  --cookies pje_session.json --processo-id ID --tipos "sentença,petição inicial"

python .claude/skills/pje-download/scripts/baixar_por_id.py \
  --cookies pje_session.json --documento-ids "123,456,789"

# Extrair índice de documentos
python .claude/skills/pje-download/scripts/extrair_indice_completo.py \
  --cookies pje_session.json --processo-id ID --output indice.json

# Converter PDF para TXT
python .claude/skills/converter-pdf/scripts/pdf_para_txt.py \
  --input data/sentenca/<numero>/<numero>.pdf --output data/sentenca/<numero>/
```

## Dependências

**Python 3.8+:**
```bash
pip install requests beautifulsoup4 pdfplumber PyPDF2 pdf2image pytesseract
```

**Sistema (OCR):**
- Tesseract OCR com idioma português
- Poppler (Windows: extrair para `~/poppler/`)

## MCP Servers Disponíveis

| Server | Função | Sintaxe de Busca |
|--------|--------|------------------|
| `bnp-api` | Banco Nacional de Precedentes (STF/STJ) | `+termo -termo "frase exata"` |
| `cjf-jurisprudencia` | Portal CJF (STF, STJ, TRFs) | `TERMO E OU NAO ADJ PROX COM MESMO` (MAIÚSCULO) |
| `julia-trf5` | Sistema JULIA do TRF5 | `termo e ou nao prox adj $` (minúsculo) |
| `tjsc-eproc` | Jurisprudência do TJSC (eProc) | `termo ou nao prox "frase" *wildcard` (case-insensitive) |
| `jurisdf-tjdft` | Jurisprudência do TJDFT | Similar ao CJF |
| `infojuris-cnj` | InfoJuris do CNJ | Precedentes qualificados |
| `claude-in-chrome` | Automação browser (sessão PJE, login) | Controle nativo do navegador |

## Convenções

- **Documentação:** Português brasileiro COM acentos
- **Código:** Inglês (padrão internacional)
- **Pastas:** kebab-case (`pje-download/`)
- **Arquivos Python:** snake_case (`listar_processos.py`)
- **Arquivos de saída:** `[NUMERO]-tipo.md` (ex: `0814624-28.2019.4.05.8100-relatorio.md`)

## Sinalizadores de Formato

Cada etapa do pipeline tem sinalizadores obrigatórios para validação:

| Etapa | Início | Fim |
|-------|--------|-----|
| Linha do Tempo | `# Linha do Tempo Processual` | `É o que satisfaz extrair dos autos.` |
| Relatório | `RELATÓRIO` | `É o que havia de relevante a relatar.` |
| Análise | `Vamos começar. Preciso pensar profundamente sobre esse caso.` | `Pronto.` |
| Fundamentação | `FUNDAMENTAÇÃO` | `JUIZ FEDERAL` |

## Regras Invioláveis (Iron Laws)

1. **Nenhuma citação sem verificação** - Se não verificou via BNP/CJF/JULIA, não cite
2. **Nenhuma afirmação sem referência** - "Os autos indicam" exige página/documento
3. **Nenhum dispositivo sem correspondência** - Cada pedido deve ser decidido
4. **Nenhuma etapa sem contrato** - Sem schema, não há validação
5. **Nenhuma completude sem evidência** - Checklist verificado antes de "feito"

## Regras Críticas do Pipeline (Resistentes à Compactação)

> **IMPORTANTE:** Esta seção sobrevive à compactação de contexto. O CLAUDE.md é re-injetado a cada turno.

### Orquestrador: Papel e Limites

| DEVE | NUNCA |
|------|-------|
| Delegar via Task tool | Executar tarefas de subagentes |
| Instruir subagente a LER seu prompt | Copiar/resumir prompts |
| Validar sinalizadores entre etapas | Prosseguir sem validação |
| Calcular $WORKSPACE e $NUMERO na Etapa 0 | Usar caminhos hardcoded |
| Usar TodoWrite para rastrear progresso | Deixar subagentes usarem TodoWrite |

### Subagentes: Isolamento de Contexto

- Subagentes têm contexto ISOLADO (não veem conversa anterior)
- Subagentes LEEM seus prompts via Read tool (não recebem cópia)
- Subagentes NUNCA usam TodoWrite (apenas orquestrador)
- Cada etapa produz arquivo com sinalizadores obrigatórios

### Agent Teams

Para tarefas paralelas, use Agent Teams em vez de múltiplas chamadas Task:
- Definir em `team-manifest.md` na pasta do workspace
- Execução paralela simples ou debate real entre agentes

### Validação Entre Etapas

Cada output DEVE ser validado antes de prosseguir:
1. Arquivo existe?
2. Sinalizador de INÍCIO presente?
3. Sinalizador de FIM presente?
4. Acentos em português presentes?

Se falhar: REGENERAR com sufixo de correção (máx 2 tentativas)

### Múltiplos Processos na Mesma Sessão

Para evitar degradação por compactação:
1. Executar `/clear` entre processos
2. O `/clear` limpa contexto mas preserva CLAUDE.md
3. Ao re-executar pipeline, o command é re-lido do disco

## Arquivo pje_session.json

Credenciais do PJE capturadas via Chrome MCP usando o comando `/capturar-sessao-pje` ou manualmente via DevTools do navegador. Contém cookies de autenticação necessários para acessar a API REST do PJE.

**Como obter:**
1. Fazer login no PJE pelo navegador
2. Usar `/capturar-sessao-pje` (requer MCP `claude-in-chrome` ativo)
3. Ou extrair manualmente os cookies via DevTools (Application > Cookies)

**IMPORTANTE:** Este arquivo contém credenciais sensíveis. **NÃO VERSIONAR!** Adicione `pje_session.json` ao `.gitignore`.
