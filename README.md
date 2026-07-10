# superjurista-dev

Plugin de meta-ferramentas para criar e customizar sistemas agenticos judiciais com Claude Code. Inclui ferramentas para criar agentes, orquestradores, skills, teams e um scaffold completo do sistema SuperJurista -- um sistema de inteligencia aumentada para processamento de processos judiciais, construido com arquitetura de pipelines deterministicos.

## Instalacao

### Opcao 1: Dentro de uma sessao do Claude Code (recomendado)

Tres comandos e o sistema inteiro esta funcionando:

```
/plugin marketplace add georgemarmelstein/superjurista-marketplace
/plugin install superjurista-dev@georgemarmelstein-superjurista-marketplace
/instalar-superjurista
```

**Passo a passo:**

1. **Adicionar o marketplace** -- registra o repositorio de plugins do SuperJurista:
   ```
   /plugin marketplace add georgemarmelstein/superjurista-marketplace
   ```

2. **Instalar o plugin** -- baixa as meta-ferramentas e o scaffold:
   ```
   /plugin install superjurista-dev@georgemarmelstein-superjurista-marketplace
   ```

3. **Instalar o sistema no projeto** -- copia agentes, pipelines, skills e MCPs para `.claude/`:
   ```
   /instalar-superjurista
   ```

### Opcao 2: Via interface interativa

Digite `/plugin` para abrir o gerenciador visual com abas (Discover, Installed, Marketplaces, Errors). Navegue com Tab/Shift+Tab.

### Opcao 3: Desenvolvimento local

```bash
git clone https://github.com/georgemarmelstein/superjurista-dev.git
claude --plugin-dir ./superjurista-dev
```

Depois, dentro da sessao: `/instalar-superjurista`

## Gerenciamento do plugin

| Acao | Comando |
|------|---------|
| Abrir gerenciador interativo | `/plugin` |
| Adicionar marketplace | `/plugin marketplace add owner/repo` |
| Instalar plugin | `/plugin install plugin@marketplace` |
| Listar instalados | `/plugin` > aba Installed |
| Desinstalar | `/plugin uninstall superjurista-dev@georgemarmelstein-superjurista-marketplace` |
| Desativar (sem remover) | `/plugin disable superjurista-dev@georgemarmelstein-superjurista-marketplace` |
| Reativar | `/plugin enable superjurista-dev@georgemarmelstein-superjurista-marketplace` |
| Recarregar apos instalar | `/reload-plugins` |

### Escopo da instalacao

Ao instalar, voce pode escolher o escopo:

- **user** -- funciona em todos os seus projetos (padrao)
- **project** -- salva em `.claude/settings.json` do repo (todos que clonarem terao o plugin)
- **local** -- so voce, so neste repositorio

### Pre-requisito

Versao minima do Claude Code: **1.0.33+**. Se `/plugin` nao aparecer:

```bash
npm update -g @anthropic-ai/claude-code
```

## Comandos

| Comando | Descricao |
|---------|-----------|
| `/instalar-superjurista` | Instala o sistema SuperJurista completo no projeto atual |
| `/criar-agente` | Cria agentes modulares seguindo as SPECs v2.0 |
| `/criar-orquestrador` | Cria orquestradores (commands) com injecao de contexto |
| `/criar-skill` | Cria skills com TDD e CSO (Claude Search Optimization) |
| `/criar-team` | Cria Agent Teams (paralelo ou debate) |
| `/planejar-sistema` | Gera blueprint arquitetural antes de criar artefatos |

## Skills

- **criar-sistema**: Motor de geracao de sistemas agenticos inteiros (1 orquestrador + N agentes + M skills) a partir de uma descricao de intencao -- blueprint como contrato, geracao em ondas por 5 agentes especializados (geradores + validadores adversariais), staging e commit atomico. Flags: `--revisar`, `--target=PATH`.
- **criar-skill**: Workflow TDD para criacao de skills -- garante que a skill ensina o comportamento correto ao Claude, com testes de conformidade e otimizacao para busca interna.
- **criar-mcp-precedente**: Guia para criar servidores MCP de jurisprudencia — tribunais brasileiros e cortes internacionais (comprovado em CJF, TCU, TJSC/eProc e HUDOC/CEDH). Descoberta de endpoints e sintaxe booleana, template com busca compartilhada, registro via `.mcp.json` e roteamento em 3 rotas: MCP de scraping, mcp-builder (REST documentada) ou skill via Chrome MCP (portais com CAPTCHA por requisicao).
- **criar-pje-download**: Cria skills de download do PJE para qualquer tribunal via engenharia reversa de arquivos HAR -- identifica endpoints, cookies, headers e gera scripts Python parametrizados.

## O que o /instalar-superjurista cria

O comando `/instalar-superjurista` gera um sistema judicial completo no projeto atual:

- **16 pipelines e comandos** para processamento judicial (sentenca, embargos, pesquisa, revisao, etc.)
- **~52 agentes especializados** em 7 categorias (extracao, analise, pesquisa, redacao, revisao, lista-trf, tribunal)
- **6 skills de dominio** (download PJE, conversao PDF, analise probatoria, captura de sessao, etc.)
- **2 servidores MCP** (TJSC eProc, TCU)
- **Estrutura de dados pronta** (`data/sentenca/`, `data/decisao/`)
- **CLAUDE.md e README.md** configurados para o projeto

### Estrutura gerada

```
projeto/
├── .claude/
│   ├── commands/           # 16 pipelines e comandos
│   ├── agents/
│   │   ├── analise/        # Marmelstein, Haack, Pearl, embargos, probatoria
│   │   ├── extracao/       # Linha do tempo, relator, conversor
│   │   ├── lista-trf/      # 9 agentes para listas de julgamento
│   │   ├── pesquisa/       # BNP, CJF, JULIA, consolidador
│   │   ├── redacao/        # Redator de minutas
│   │   ├── revisao/        # Verificadores (calculos, honorarios, fontes)
│   │   └── tribunal/       # Acusador, defensor, juiz mediador
│   ├── skills/
│   │   ├── pje-download/   # API REST do PJE (10 scripts Python)
│   │   ├── converter-pdf/  # Conversao PDF para TXT com OCR hibrido
│   │   ├── analise-probatoria/  # Checklists por tipo de prova
│   │   ├── capturar-sessao-pje/ # Captura sessao via Chrome MCP
│   │   ├── analisador-erro-medico/ # Analise de erro medico
│   │   └── fork-terminal/  # Execucao paralela em terminais
│   └── mcp-servers/
│       ├── tjsc-eproc/     # Jurisprudencia TJSC
│       └── tcu-jurisprudencia/ # Jurisprudencia TCU
├── scripts/                # Gates deterministicos v3.0 (verificar_pipeline, verificar_sentenca, merge_sentenca)
├── data/
│   ├── sentenca/           # Processos para sentenca
│   └── decisao/            # Processos para decisao
├── CLAUDE.md               # Configuracao do projeto
└── README.md               # Documentacao do projeto
```

## Framework

O sistema baseia-se no framework v3.0 de orquestracao agentica com padrao "Orquestrador Cego" e injecao de contexto. Neste padrao, commands (orquestradores) delegam tarefas via Task tool para subagentes que possuem contexto isolado -- cada agente le seu proprio prompt, GRAVA o documento em disco e responde 1 linha de status. A validacao entre etapas e deterministica, por gate de script (`scripts/verificar_<sistema>.py`), e os pipelines sao retomaveis: a varredura inicial lista as etapas PENDENTES e etapa ja valida nao roda de novo. Templates e referencias completas estao disponiveis em `spec/`.

## Dependencias

**Python 3.8+:**
```bash
pip install requests beautifulsoup4 pdfplumber PyPDF2 pdf2image pytesseract
```

**Sistema (para OCR):**
- Tesseract OCR com pacote de idioma portugues
- Poppler (Windows: extrair para `~/poppler/`)

## Licenca

[MIT](LICENSE)
