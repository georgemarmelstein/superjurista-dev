# Framework Super Jurista

> **Atualização v3.0 (04/07/2026) — leia antes das seções de validação abaixo.**
> A filosofia deste framework (orquestrador cego, injeção de contexto, contratos, menor
> privilégio) permanece. Mudou o **encanamento** dos pipelines: (1) o subagente GRAVA o
> documento e responde 1 linha de status — não devolve o texto inline; (2) a validação é por
> SCRIPT (`scripts/verificar_<sistema>.py`, motor `scripts/verificar_pipeline.py`), com âncoras
> normalizadas de acento/caixa — o orquestrador não lê o documento para validar; (3) pipelines são
> RETOMÁVEIS (a linha `PENDENTES` do gate é o plano; etapa válida não roda de novo); (4) merge por
> script. Onde este README ainda descreve "validar lendo o sinalizador" ou "regenerar por
> sufixo sem gate", isso vale para pipelines antigos; o padrão vigente é o do
> `scaffold/commands/pipeline-sentenca.md` e das 14 Iron Laws do Padrão Soberano
> (`${CLAUDE_PLUGIN_ROOT}/skills/criar-sistema/references/padrao-soberano.md`).

## Visão Geral

O **Super Jurista** é um framework para construção de **pipelines determinísticos** usando Claude Code. Estabelece padrões para criação de agentes, orquestradores e workflows que trocam flexibilidade por previsibilidade.

```
PIPELINES TROCAM FLEXIBILIDADE POR PREVISIBILIDADE.
```

Em vez de agentes livres que podem "viajar", usamos:
- Fluxo fixo de etapas
- Contratos rígidos entre etapas
- Validação obrigatória em cada transição
- Isolamento de contexto (cada etapa = subagent limpo)

---

## Princípio Central: Orquestrador Cego

O termo "Orquestrador Cego" significa que o orquestrador **não precisa conhecer** a lógica interna dos agents. Ele coordena sem executar.

**O que o orquestrador FAZ:**
- Calcula variáveis de contexto ($WORKSPACE, $NUMERO)
- Injeta caminhos prontos nos subagentes
- Dispara subagentes via Task tool
- Valida outputs via sinalizadores
- Rastreia progresso via TodoWrite

**O que o orquestrador NÃO FAZ:**
- Não lê o conteúdo completo dos prompts de agents
- Não executa a tarefa do subagente (análise, redação, etc.)
- Não copia/resume prompts - instrui subagente a ler

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ORQUESTRADOR CEGO                              │
│                                                                     │
│   "Cego" = não precisa entender a lógica do agent                  │
│   O orquestrador COORDENA, o agent EXECUTA                         │
│                                                                     │
│   Orquestrador sabe:                                                │
│   ├── QUAL arquivo contém o agent                                   │
│   ├── QUAL contexto injetar ($WORKSPACE)                            │
│   ├── QUAL saída esperar                                            │
│   └── COMO validar (sinalizadores)                                  │
│                                                                     │
│   NOTA: O orquestrador pode conter instruções de EXECUÇÃO para     │
│   os subagentes (como ler o arquivo X, salvar em Y), mas NÃO       │
│   contém a lógica do AGENT em si.                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Arquitetura de Duas Camadas (v2.0)

A partir da v2.0, o framework adota uma separação clara entre **instruções** (estáticas) e **dados** (dinâmicos):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CAMADA 1: INSTRUÇÕES (estática)                                            │
│  .claude/agents/[nome-agent].md                                             │
│                                                                             │
│  → Define CAPACIDADE: "Sei analisar casos e classificar"                    │
│  → NÃO conhece caminhos específicos                                         │
│  → Reutilizável em múltiplos pipelines                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  CAMADA 2: DADOS (dinâmica)                                                 │
│  workspace/processo-XXX/                                                    │
│                                                                             │
│  → Contém arquivos do processo específico                                   │
│  → Orquestrador injeta caminho via $ARGUMENTS                               │
│  → _manifest.md lista o que está disponível                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Padrão de Injeção de Contexto

O orquestrador recebe `$ARGUMENTS` do usuário e **injeta** caminhos calculados nos subagentes:

```
┌──────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│  $ARGUMENTS  │────▶│    ORQUESTRADOR      │────▶│    SUBAGENTES    │
│  (usuário)   │     │                      │     │                  │
│  "12345"     │     │  Calcula:            │     │  Recebem:        │
│              │     │  $WORKSPACE =        │     │  Caminhos PRONTOS│
│              │     │  workspace/processo- │     │  Não variáveis   │
│              │     │  12345               │     │                  │
└──────────────┘     └──────────────────────┘     └──────────────────┘
```

**Princípio:** Agent define CAPACIDADE. Orquestrador injeta CONTEXTO.

### Manifest (_manifest.md)

Cada workspace contém um `_manifest.md` que serve como índice:

```markdown
# Manifest: Processo 12345

## Arquivos Disponíveis

| Arquivo | Status |
|---------|--------|
| `fonte/12345.txt` | disponível |
| `12345-relatorio.md` | disponível |
| `12345-analise.md` | pendente |
```

**Convenção de Nomenclatura:** `[NUMERO]-tipo.md`
- Facilita busca por arquivos do mesmo processo
- Evita colisão em workspaces compartilhados

Subagentes podem ler o manifest para descobrir o que está disponível sem hardcodar caminhos.

---

## Estrutura de Diretórios

```
projeto/
├── CLAUDE.md                     # Instruções do projeto
│
├── .claude/
│   ├── commands/                 # ORQUESTRADORES (entry points)
│   │   └── pipeline-xxx.md           # Invocado via /pipeline-xxx
│   │
│   ├── agents/                   # EXECUTORES (capacidades modulares)
│   │   ├── extracao/                 # Subpasta por CATEGORIA (opcional)
│   │   │   └── linha-tempo.md
│   │   ├── revisao/
│   │   │   └── advogado-diabo.md
│   │   ├── analise-marmelstein.md    # Ou direto na raiz
│   │   └── fundamentador.md
│   │   # Nota: Subpastas por CATEGORIA ok. Por PIPELINE proibido.
│   │
│   ├── skills/                   # CONHECIMENTO + SCRIPTS
│   │   └── [skill-name]/
│   │       ├── SKILL.md              # Instruções (<500 linhas)
│   │       ├── references/           # Docs detalhadas (sob demanda)
│   │       ├── scripts/              # Scripts executáveis
│   │       └── assets/               # Recursos (templates, images, data)
│   │
│   └── specs/                    # FRAMEWORK (este diretório)
│       ├── README.md                 # Este arquivo
│       ├── templates/                # Templates primários (uso direto)
│       │   ├── agent.md              # v2.0 - Capacidade modular
│       │   ├── orquestrador.md       # v2.0 - Injeção de contexto
│       │   ├── skill.md              # v1.4 - Spec Anthropic
│       │   └── manifest.md           # v2.0 - Índice de workspace
│       └── referencias/              # Documentação de consulta
│           ├── variantes-subagente.md   # Catálogo de variantes
│           └── contrato-avancado.md     # Para pipelines complexos
│
└── workspace/                    # DADOS DINÂMICOS (por processo)
    └── processo-XXX/
        ├── _manifest.md              # Índice do workspace
        ├── fonte/                    # Dados brutos
        │   └── XXX.txt               # [NUMERO].txt
        ├── XXX-relatorio.md          # [NUMERO]-tipo.md
        ├── XXX-linha-tempo.md
        ├── XXX-analise.md
        ├── XXX-fundamentacao.md
        ├── XXX-sentenca.md
        ├── pesquisa/
        │   ├── XXX-bnp.md
        │   ├── XXX-cjf.md
        │   └── XXX-julia.md
        └── revisao/
            ├── XXX-advogado-diabo.md
            ├── XXX-consistencia-interna.md
            └── XXX-consistencia-externa.md
```

### Por que Organização por Categoria (não por Pipeline)?

A v2.0 proíbe organizar agents por pipeline (ex: `.claude/agents/sentenca/relator.md`). Por quê?

**Problema da organização por pipeline:**
- Agent `relator.md` fica em `agents/sentenca/`
- Mas o mesmo agent pode ser usado em `pipeline-embargos`
- Duplicação ou referência cruzada confusa

**Solução: organização por categoria:**
```
.claude/agents/
├── extracao/           # Agents que EXTRAEM dados
│   ├── linha-tempo-processual.md
│   └── relator-marmelstein.md
├── analise/            # Agents que ANALISAM
│   ├── analisador-marmelstein.md
│   └── fundamentador-marmelstein.md
├── pesquisa/           # Agents que PESQUISAM precedentes
│   └── pesquisador-bnp.md
└── revisao/            # Agents que REVISAM
    └── verificador-calculos.md
```

**Benefícios:**
- Um agent pode ser usado por múltiplos pipelines
- Facilita descoberta (todos os agents de análise juntos)
- Evita duplicação de código

---

## Agent vs Skill: Quando Usar Cada Um

Uma dúvida comum é decidir entre criar um **Agent** ou uma **Skill**. A diferença é fundamental:

| Aspecto | Agent | Skill |
|---------|-------|-------|
| **Propósito** | Executa tarefas via LLM | Fornece conhecimento/scripts |
| **Invocação** | Via Task tool (subagent) | Via Read (carregado no contexto) |
| **Contexto** | Isolado (não vê conversa) | Compartilhado (vê conversa) |
| **Output** | Produz artefato (arquivo) | Informa/instrui o Claude |
| **Exemplo** | `relator-marmelstein.md` → gera relatório | `pje-download/` → ensina como baixar PDFs |

### Quando Criar um AGENT

Use agent quando você precisa de:
- **Processamento isolado**: Cada execução deve ser independente
- **Artefato de saída**: O resultado é um arquivo (relatório, análise, sentença)
- **Capacidade reutilizável**: O mesmo agent pode ser usado em vários pipelines
- **Validação rigorosa**: Sinalizadores de formato, contratos de dados

**Exemplos de agents:**
- `linha-tempo-processual.md` - extrai cronologia
- `fundamentador-marmelstein.md` - redige fundamentação
- `verificador-calculos.md` - valida cálculos

### Quando Criar uma SKILL

Use skill quando você precisa de:
- **Conhecimento especializado**: Regras, tabelas, referências
- **Scripts utilitários**: Automação de tarefas (download, conversão)
- **Instruções detalhadas**: Como fazer algo passo a passo
- **Progressive disclosure**: Carregar informação sob demanda

**Exemplos de skills:**
- `pje-download/` - scripts para baixar processos do PJE
- `converter-pdf/` - scripts de conversão PDF→TXT
- `consultor-implementacao/` - ajuda a decidir qual artefato criar

### Regra Prática

```
Se a resposta é "gerar um arquivo processado" → AGENT
Se a resposta é "ensinar/informar o Claude" → SKILL
```

---

## Anatomia de um Agent (v2.0)

A partir da v2.0, agents são **capacidades modulares reutilizáveis**. Não conhecem caminhos específicos - recebem contexto do orquestrador.

### Camada 1: YAML Frontmatter

```yaml
---
name: nome-do-agente
description: Descrição da CAPACIDADE do agent
tools: Read Write
model: sonnet
---
```

#### Campos Obrigatórios

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Identificador único do agent |
| `description` | string | A CAPACIDADE do agent (não o que faz em um pipeline específico) |
| `tools` | lista | Tools separadas por espaço (sem vírgulas) |
| `model` | enum | `haiku`, `sonnet`, `opus` |

### Camada 2: XML Estruturado (v2.0)

```xml
<identidade>
  <papel>Definição do papel do agente</papel>
  <estilo>Estilo de comunicação/execução</estilo>
</identidade>

<capacidade>
  <habilidade>O QUE este agent sabe fazer</habilidade>
  <especializacao>Em que área é especialista</especializacao>
</capacidade>

<contrato>
  <entrada>
    <tipo>Tipo de dado que espera (relatório, texto, lista)</tipo>
    <formato>Formato esperado (TXT, MD, JSON)</formato>
    <requisitos>O que a entrada DEVE conter</requisitos>
  </entrada>
  <saida>
    <tipo>Tipo de dado que produz</tipo>
    <formato>Formato da saída</formato>
  </saida>
</contrato>

<restricoes>
  - NUNCA [restrição crítica]
  - NUNCA inventar informações não presentes na entrada
  - NÃO assumir caminhos de arquivo - recebe via contexto
  - SEMPRE [obrigação]
  - SEMPRE usar português com acentos corretos
</restricoes>

<contingencias>
  <se_entrada_insuficiente>O que fazer se entrada não tiver dados necessários</se_entrada_insuficiente>
  <se_ambiguo>O que fazer se houver ambiguidade</se_ambiguo>
</contingencias>

<formato_saida>
  [SINALIZADOR_INICIO]
  [Template literal do output esperado]
  [SINALIZADOR_FIM]
</formato_saida>

<sinalizadores>
  | Posição | Texto Obrigatório |
  |---------|-------------------|
  | Início  | "SINALIZADOR_INICIO" |
  | Fim     | "SINALIZADOR_FIM"    |
</sinalizadores>

<instrucoes>
  <passo numero="1" nome="Receber entrada">
    Ler o conteúdo fornecido pelo orquestrador.
  </passo>
  <passo numero="2" nome="Processar">
    Aplicar capacidade à entrada.
  </passo>
  <passo numero="3" nome="Produzir saída">
    Gerar saída no formato especificado.
  </passo>
</instrucoes>
```

### Tags `<capacidade>` vs `<proposito>`: Qual Usar?

A confusão entre essas tags é comum. Aqui está a diferença:

| Tag | Foco | Quando Usar | Exemplo |
|-----|------|-------------|---------|
| `<capacidade>` | **O QUE sabe fazer** | Agents modulares (v2.0) | "Sei extrair cronologia de processos" |
| `<proposito>` | **POR QUE existe** | Agents e Orquestradores | "Existo para gerar relatório estruturado" |

**Regra prática:**
- `<capacidade>` descreve **habilidade genérica** (reutilizável)
- `<proposito>` descreve **objetivo específico** (contexto do uso)

**Na prática, você pode usar AMBAS:**

```xml
<capacidade>
  <habilidade>Extrair cronologia de processos judiciais</habilidade>
  <especializacao>Direito previdenciário e processual civil</especializacao>
</capacidade>

<proposito>  <!-- Tag OPCIONAL - adiciona contexto -->
  <objetivo>Gerar linha do tempo para subsidiar análise</objetivo>
  <razao>Etapa 1 do pipeline de sentença requer cronologia estruturada</razao>
</proposito>
```

**Recomendação:**
- Agents modulares: use `<capacidade>` (obrigatória) + `<proposito>` (opcional)
- Orquestradores: use `<proposito>` (descreve objetivo do pipeline)

### Diferença v1 → v2

| Aspecto | v1 (Acoplado) | v2 (Modular) |
|---------|---------------|--------------|
| Caminhos | Hardcoded no agent | Injetados via $WORKSPACE |
| Reutilização | Difícil (amarrado a pipeline) | Fácil (capacidade genérica) |
| Entrada/Saída | "Leia de X, escreva em Y" | "Espero tipo X, produzo tipo Y" |
| Estrutura | `<proposito>` | `<capacidade>` + `<contrato>` |
| Localização | `.claude/agents/[pipeline]/` | `.claude/agents/` (raiz) |

### Exemplo Completo de Agent

```markdown
---
name: relator-processual
description: Extrai relatório estruturado de processo judicial
tools: Read Write
model: sonnet
color: yellow
---

<identidade>
  <papel>Extrator de relatórios judiciais</papel>
  <estilo>Metódico, exaustivo, neutro. Apenas extrai, nunca analisa.</estilo>
</identidade>

<proposito>
  <objetivo>Gerar relatório estruturado do processo judicial</objetivo>
  <razao>Permitir que etapas posteriores compreendam o caso sem consultar os autos</razao>
  <resultado_final>Arquivo `relatorio.md` com síntese de todos os atos relevantes</resultado_final>
</proposito>

<restricoes>
  - NUNCA inventar fatos ou datas
  - NUNCA analisar ou sugerir decisões
  - SEMPRE incluir IDs dos documentos citados
  - SEMPRE usar português COM ACENTOS
  - SEM asteriscos, SEM hashtags no corpo
</restricoes>

<contingencias>
  <se_nao_encontrar>Escreva "[NÃO LOCALIZADO NOS AUTOS]"</se_nao_encontrar>
  <se_id_ausente>Use "Id. NÃO CONSTA"</se_id_ausente>
</contingencias>

<formato_saida>
RELATÓRIO

Trata-se de `TIPO DE AÇÃO` proposta por `AUTOR` contra `RÉU`, com o objetivo de `PEDIDO`.

Alega a parte autora (`Id. XXXXX`) que `FATOS ALEGADOS`.

Em sua contestação (`Id. XXXXX`), a parte requerida alegou que `DEFESA`.

`DEMAIS PEÇAS RELEVANTES`

É o que havia de relevante a relatar.
</formato_saida>

<sinalizadores>
  | Posição | Texto Obrigatório |
  |---------|-------------------|
  | Início  | "RELATÓRIO"       |
  | Fim     | "É o que havia de relevante a relatar." |
</sinalizadores>
```

---

## Anatomia de um Orquestrador

O orquestrador é um **command** que coordena a execução de etapas.

### Estrutura do Orquestrador

```markdown
---
description: Pipeline de [nome]
argument-hint: [parametro]
allowed-tools: Read, Task, Bash
---

<identidade>
  <papel>Coordenador do pipeline, não executor</papel>
  <estilo>Metódico, sequencial, validador rigoroso</estilo>
</identidade>

<proposito>
  <objetivo>Transformar [entrada] em [saída] através de N etapas</objetivo>
  <resultado_final>[Descrição do artefato final]</resultado_final>
</proposito>

<capacidades>
  <tools_orquestrador>Task, Read, Bash</tools_orquestrador>
  <tools_subagentes>Read, Write</tools_subagentes>

  <regras_uso>
    - Subagentes LEEM prompts diretamente (não recebem cópia)
    - Orquestrador NÃO executa tarefas dos subagentes
    - Orquestrador NÃO lê o prompt: instrui subagente a ler via Read
    - Cada subagente tem contexto ISOLADO
  </regras_uso>
</capacidades>

<restricoes>
  <orquestrador>
    - NUNCA executar etapas em paralelo (exceto quando explícito)
    - NUNCA copiar/resumir prompts — instrua subagente a LER
    - NUNCA prosseguir sem validar etapa anterior
    - NUNCA tentar mais de 2 vezes a mesma etapa
  </orquestrador>

  <subagentes>
    - NUNCA inventar dados
    - NUNCA remover acentos do português
    - NUNCA usar markdown no corpo (asteriscos, hashtags)
  </subagentes>
</restricoes>

<contingencias>
  <output_vazio>
    ERRO CRÍTICO: Subagente não salvou arquivo.
    → Verificar se path está correto
    → Regenerar com prompt idêntico
    → Se falhar 2x → PARAR e informar usuário
  </output_vazio>

  <sinalizador_ausente>
    AVISO: Sinalizador não encontrado.
    → Regenerar com SUFIXO DE CORREÇÃO
    → Se falhar 2x → PARAR e informar usuário
  </sinalizador_ausente>
</contingencias>

<contratos_dados>
  | # | Etapa | Entrada | Saída | Validação |
  |---|-------|---------|-------|-----------|
  | 1 | Nome  | input   | output | sinalizadores |
  | 2 | Nome  | input   | output | sinalizadores |
</contratos_dados>

<etapas_pipeline>

  <etapa numero="1" nome="Nome da Etapa">
    <config>
      <modelo>sonnet</modelo>
      <tools>Read, Write</tools>
      <entrada>[arquivo de entrada]</entrada>
      <saida>[arquivo de saída]</saida>
    </config>

    <prompt_subagente>
    ═══════════════════════════════════════════════════════════════
    VOCÊ É UM SUBAGENTE. EXECUTE DIRETAMENTE.
    ═══════════════════════════════════════════════════════════════

    ## IDENTIDADE
    Você é um [papel].

    ## SUA EXECUÇÃO

    Passo 1 - Ler instruções:
    Read: .claude/agents/[pipeline]/[agent].md
    → Este arquivo é LEI. Siga fielmente.

    Passo 2 - Ler entrada:
    Read: [arquivo de entrada]

    Passo 3 - Executar tarefa:
    → [instruções específicas]

    Passo 4 - Salvar:
    Write: [arquivo de saída]
    ═══════════════════════════════════════════════════════════════
    </prompt_subagente>

    <validacao>
      | # | Verificação | Se Falhar |
      |---|-------------|-----------|
      | 1 | Arquivo existe | ERRO: não salvou |
      | 2 | Sinalizador início | REGENERAR |
      | 3 | Sinalizador fim | REGENERAR |
    </validacao>

    <transicao>
      Se OK → ETAPA 2
      Se FALHAR 2x → PARAR
    </transicao>
  </etapa>

</etapas_pipeline>
```

---

## Contratos de Dados

Todo pipeline deve ter uma tabela de contratos explícita:

```
| # | Etapa | Entrada | Saída | Validação |
|---|-------|---------|-------|-----------|
| 0 | Preparação | $ARGUMENTS | $NUMERO, $WORKSPACE | Número extraído |
| 1 | Relatório | $NUMERO.txt | $NUMERO-relatorio.md | "RELATÓRIO"..."relatar" |
| 2 | Análise | $NUMERO-relatorio.md | $NUMERO-analise.md | "Vamos começar"..."Pronto" |
| 3 | Fundamentação | relatorio + analise | $NUMERO-fundamentacao.md | "FUNDAMENTAÇÃO"..."JUIZ" |
| 4 | Merge | relatorio + fund | $NUMERO-sentenca.md | Todas seções + acentos |
```

**Convenção:** Arquivos de saída seguem padrão `[NUMERO]-tipo.md` para facilitar busca.

---

## Sinalizadores de Formato

Expressões obrigatórias que indicam se o subagente seguiu o prompt:

```
| Etapa | Início Obrigatório | Fim Obrigatório |
|-------|-------------------|-----------------|
| Relatório | "RELATÓRIO" | "É o que havia de relevante a relatar." |
| Análise | "Vamos começar" | "Pronto." |
| Fundamentação | "FUNDAMENTAÇÃO" | "JUIZ FEDERAL" |
```

**Regra:** Se sinalizador ausente → prompt não foi seguido → REGENERAR com sufixo de correção.

### Sufixos de Correção

```xml
<sufixo_formato>
[FALHA DE FORMATO. Releia o prompt em .claude/agents/[agent].md.
DEVE começar com "[INICIO]". DEVE terminar com "[FIM]".]
</sufixo_formato>

<sufixo_acentos>
[FALHA DE ACENTOS. Use acentos do português: é, á, ã, ç, ô, ê, í, ú.
Documento jurídico brasileiro EXIGE acentuação correta.]
</sufixo_acentos>
```

---

## Anatomia de uma Skill

Skills são blocos de **conhecimento + scripts** reutilizáveis. Seguem a especificação oficial da Anthropic (agentskills.io).

### YAML Frontmatter (Padrão Anthropic)

```yaml
---
name: nome-da-skill
description: >
  Descrição do que a skill faz E quando usá-la.
  Inclua palavras-chave que Claude usará para detectar quando ativar.

# === CAMPOS OPCIONAIS ===
license: MIT
compatibility: >
  Requer Python 3.10+, poppler-utils.
metadata:
  author: Super Jurista
  version: "1.0.0"
allowed-tools: Read Write Bash
---
```

#### Campos e Validação

| Campo | Obrigatório | Constraints | Descrição |
|-------|-------------|-------------|-----------|
| `name` | **Sim** | Max 64 chars, lowercase+hyphens, deve coincidir com nome da pasta | Identificador único |
| `description` | **Sim** | Max 1024 chars | O que faz + quando usar + palavras-chave |
| `license` | Não | - | Nome da licença ou referência a arquivo |
| `compatibility` | Não | Max 500 chars | Requisitos de ambiente |
| `metadata` | Não | key-value strings | author, version, etc. |
| `allowed-tools` | Não | Space-delimited | Tools pré-aprovadas (experimental) |

#### Regras para o Campo `name`

**Válidos:**
```yaml
name: pdf-processing
name: pesquisa-juridica
```

**Inválidos:**
```yaml
name: PDF-Processing      # maiúsculas não permitidas
name: -pdf                # não pode começar com hífen
name: pdf--processing     # hífens consecutivos não permitidos
name: pdf_processing      # underscore não permitido
```

#### Regras para o Campo `description`

**Bom** (descreve O QUE + QUANDO + palavras-chave):
```yaml
description: >
  Extrai texto e tabelas de arquivos PDF, preenche formulários PDF.
  Use quando trabalhar com documentos PDF ou quando o usuário
  mencionar PDFs, formulários ou extração de documentos.
```

**Ruim** (muito vago):
```yaml
description: Ajuda com PDFs.
```

### Estrutura de Diretórios

```
.claude/skills/[nome-skill]/
├── SKILL.md              # Obrigatório: instruções principais (<500 linhas)
├── references/           # Opcional: documentação detalhada (sob demanda)
│   ├── REFERENCE.md      # Referência técnica principal
│   └── [topico].md       # Tópicos específicos
├── scripts/              # Opcional: scripts executáveis
│   └── [script].py
└── assets/               # Opcional: recursos estáticos
    ├── templates/        # Templates de documento/configuração
    ├── images/           # Diagramas, exemplos visuais
    └── data/             # Lookup tables, schemas
```

### Progressive Disclosure (Economia de Tokens)

A spec oficial define três níveis de carregamento:

```
┌─────────────────────────────────────────────────────────────────┐
│  CARREGAMENTO EM CAMADAS                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Nível 1: METADATA (~100 tokens)                                │
│  └─ Carregado no STARTUP                                        │
│  └─ Campos: name, description                                   │
│                                                                 │
│  Nível 2: SKILL.md (<5000 tokens recomendado)                   │
│  └─ Carregado quando ATIVADO                                    │
│  └─ Instruções principais, exemplos essenciais                  │
│                                                                 │
│  Nível 3: references/ (sob demanda)                             │
│  └─ Carregado quando NECESSÁRIO                                 │
│  └─ Documentação técnica detalhada                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Implicação prática:**
- Mantenha SKILL.md conciso (<500 linhas)
- Mova conteúdo detalhado para `references/`
- Claude carrega `references/` sob demanda

### Tipos de Skill

| Tipo | Conteúdo | Exemplo |
|------|----------|---------|
| **Conhecimento** | SKILL.md + references/ | pesquisa-precedentes |
| **Scripts** | SKILL.md + scripts/ | pje-integration |
| **Híbrida** | Conhecimento + Scripts | conversao-pdf |
| **Recursos** | SKILL.md + assets/ | brand-guidelines |

### Checklist de Validação de Skills

```
YAML Frontmatter:
[ ] name em lowercase com hífens, coincide com nome da pasta?
[ ] description descreve O QUE faz + QUANDO usar + palavras-chave?
[ ] description tem menos de 1024 caracteres?

Estrutura:
[ ] SKILL.md tem menos de 500 linhas?
[ ] Diretório references/ (não reference/)?
[ ] Caminhos relativos nas referências?

Progressive Disclosure:
[ ] Conteúdo detalhado movido para references/?
[ ] SKILL.md focado em instruções essenciais?

Isolamento (v2.7):
[ ] Se skill tem scripts verbosos, usa context: fork?
[ ] Se usa fork, tem agent definido?
[ ] Instrucoes sao imperativas (copiar e executar)?
```

---

## Skills com context: fork (v2.7)

A partir da v2.7, skills que executam scripts com output verboso devem usar `context: fork` para isolamento de contexto.

### Problema: Poluicao de Contexto

Quando uma skill executa scripts Python/Bash, todo o output vai para a conversa principal:

```
Usuario: /baixar-processo 12345

Claude: Executando download...
[500 linhas de output do script]
[Detalhes de cada arquivo baixado]
[Logs de debug]
...

Usuario: (contexto poluido, tokens desperdicados)
```

### Solucao: context: fork

```yaml
---
name: baixar-processo
description: Baixa processos do PJE
context: fork           # <- Executa em sub-agente isolado
agent: general-purpose  # <- Tipo de agente
allowed-tools: Bash Read Write
---

# Instrucoes enxutas aqui
```

**O que acontece:**

1. Skill e invocada
2. Claude cria sub-agente temporario (`context: fork`)
3. Sub-agente executa os scripts
4. Todo output verboso fica contido no sub-agente
5. Conversa principal recebe apenas resumo

### Padrao de Skill Imperativa

Skills com fork devem ser **imperativas** - instrucoes literais para copiar e executar:

```markdown
---
name: pje-download
description: Baixa processos do PJE
context: fork
agent: general-purpose
allowed-tools: Bash Read Write
---

# PJE Download

REGRA ABSOLUTA: Execute os scripts existentes. NAO crie codigo novo.

## Scripts Disponiveis

| Script | Comando |
|--------|---------|
| Listar | `python .claude/skills/pje-download/scripts/listar_processos.py` |
| Baixar | `python .claude/skills/pje-download/scripts/baixar_pdfs.py` |

## Retorno Esperado

Retorne APENAS:
- Status (sucesso/erro)
- Caminhos gerados
- Estatisticas resumidas

NAO inclua:
- Output completo dos scripts
- Logs detalhados
```

**Caracteristicas:**

1. **Menos de 100 linhas** - Enxuto, sem documentacao rica
2. **Comandos literais** - Copiar e executar, sem interpretacao
3. **Regra explicita** - "NAO crie codigo novo"
4. **Retorno definido** - O que incluir e o que NAO incluir

### Documentacao Rica em references/

A documentacao detalhada fica em `references/documentacao-completa.md`:

```
skill/
├── SKILL.md                          # ENXUTO (~70 linhas)
├── scripts/
│   └── *.py
└── references/
    ├── documentacao-completa.md      # Detalhes tecnicos
    ├── api-referencia.md             # Referencia de API
    └── casos-de-borda.md             # Edge cases
```

**Vantagens:**

- SKILL.md carregado rapidamente (poucos tokens)
- Documentacao disponivel sob demanda
- Modelo nao se perde em instrucoes extensas

### Commands Imperativos

Commands que usam skills devem ser **imperativos**:

**Antes (delegativo):**
```markdown
## Execucao
Siga os passos da skill `pje-download`
```

**Depois (imperativo):**
```markdown
## Execucao

### Etapa 1: Listar processos
Executar EXATAMENTE:
```bash
python .claude/skills/pje-download/scripts/listar_processos.py --cookies pje_session.json --modo $2 --limite $1
```

### Etapa 2: Baixar PDFs
Executar EXATAMENTE:
```bash
python .claude/skills/pje-download/scripts/baixar_pdfs.py --cookies pje_session.json --processos processos.json
```
```

**Beneficios:**

1. Modelo nao tem espaco para interpretar
2. Comandos literais - copiar e colar
3. Checkpoints claros entre etapas
4. Reduz comportamento de "reinventar a roda"

### Quando Usar context: fork

| Cenario | Usar fork? | Justificativa |
|---------|------------|---------------|
| Skill executa scripts Python/Bash | **SIM** | Output verboso |
| Skill e apenas conhecimento | NAO | Sem execucao |
| Workflow multi-etapas | **SIM** | Isolamento entre etapas |
| Tarefa rapida (<10 linhas output) | NAO | Overhead desnecessario |
| Processamento de lote | **SIM** | Muito output acumulado |

### Exemplo Completo: Refatoracao pje-download

**Antes (318 linhas):**
```yaml
---
name: pje-download
description: Baixa processos do PJE...
---

# Skill: PJE Download

<identidade>...</identidade>
<proposito>...</proposito>
<quando_usar>...</quando_usar>
<restricoes>...</restricoes>
<scripts>...</scripts>
<instrucoes>
  <passo numero="1">...</passo>
  <passo numero="2">...</passo>
  ...
</instrucoes>
<casos_de_borda>...</casos_de_borda>
<exemplos>...</exemplos>
```

**Depois (71 linhas):**
```yaml
---
name: pje-download
description: Baixa processos do PJE via API REST
context: fork
agent: general-purpose
allowed-tools: Bash Read Write
---

# PJE Download

REGRA ABSOLUTA: Execute os scripts existentes. NAO crie codigo novo.

## Scripts Disponiveis
[tabela simples]

## Comandos Prontos
[bash literal para copiar]

## Retorno Esperado
[o que incluir/nao incluir]

## Documentacao
Para detalhes: references/documentacao-completa.md
```

**Resultado:**
- 78% reducao de linhas (318 → 71)
- Contexto isolado (fork)
- Modelo segue instrucoes literais
- Documentacao rica preservada em references/

---

## Isolando Fases que Consomem Contexto (v2.7)

Algumas fases de um workflow podem consumir muito contexto se executadas na conversa principal:

- Tentativas multiplas (retry)
- Leitura de arquivos grandes
- Codigo Python inline
- Debug e troubleshooting

### Problema: Contexto Poluido

```
Usuario: /baixar-pje 5

Claude: Verificando Chrome...
[leitura de arquivo HAR]
[tentativa 1 falhou]
[tentativa 2 com outro arquivo]
[Python inline para extrair cookies]
[mais debug]
...

→ 500+ tokens consumidos antes de comecar o trabalho real
```

### Solucao: Skill Auxiliar com Fork

Criar skill dedicada para a fase problematica:

```yaml
# capturar-sessao-pje/SKILL.md
---
name: capturar-sessao-pje
description: Captura sessao do PJE
context: fork
agent: general-purpose
---

[instrucoes da captura]
```

O command invoca a skill:

```markdown
### Etapa 1: Capturar sessao (CONTEXTO ISOLADO)

Invocar skill: capturar-sessao-pje

**Checkpoint:** pje_session.json existe?
```

### Beneficios

1. **Isolamento**: Tentativas e debug ficam no sub-agente
2. **Economia**: Conversa principal recebe apenas resultado
3. **Clareza**: Command fica enxuto e legivel
4. **Reuso**: Skill pode ser usada por multiplos commands

### Quando Isolar em Skill

| Fase | Isolar? | Motivo |
|------|---------|--------|
| Captura de sessao | **SIM** | Pode ter multiplas tentativas |
| Download de arquivos | **SIM** | Output verboso |
| Conversao PDF→TXT | **SIM** | Logs extensos |
| Validacao simples | NAO | Rapido, pouco output |
| Listar arquivos | NAO | Operacao trivial |

### Exemplo: Pipeline com Fases Isoladas

```
/baixar-converter 5 sentenca

Etapa 1: capturar-sessao-pje (FORK)    → pje_session.json
Etapa 2: listar processos               → processos.json
Etapa 3: pje-download (FORK)           → PDFs baixados
Etapa 4: converter-pdf (FORK)          → TXTs gerados
Etapa 5: relatorio                      → resumo ao usuario
```

Fases 1, 3, 4 rodam em contexto isolado. Conversa principal fica limpa.

---

## Iron Laws (Regras Invioláveis)

```
1. NENHUMA CITAÇÃO SEM VERIFICAÇÃO PRIMEIRO
   → Se não verificou via BNP/CJF/JULIA, não cite

2. NENHUMA AFIRMAÇÃO SEM REFERÊNCIA AOS AUTOS
   → "Os autos indicam" exige página/documento

3. NENHUM DISPOSITIVO SEM CORRESPONDÊNCIA AOS PEDIDOS
   → Cada pedido deve ser expressamente decidido

4. NENHUMA ETAPA SEM CONTRATO DEFINIDO
   → Sem schema, não há validação

5. NENHUMA COMPLETUDE SEM EVIDÊNCIA
   → Checklist verificado antes de declarar "feito"
```

---

## Fluxo de Execução

```
USUÁRIO: /pipeline-xxx [argumento]
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│  COMMAND (Orquestrador Cego)                                    │
│  .claude/commands/pipeline-xxx.md                               │
│                                                                 │
│  FASE 0: Preparação                                             │
│  └── Extrair variáveis de $ARGUMENTS                            │
│                                                                 │
│  FASE 1: Etapa 1                                                │
│  ├── Task: Subagente lê .claude/agents/[agent-1].md             │
│  ├── Validar sinalizadores                                      │
│  └── Se OK → próxima etapa                                      │
│                                                                 │
│  FASE 2: Etapa 2                                                │
│  ├── Task: Subagente lê .claude/agents/[agent-2].md             │
│  ├── Validar sinalizadores                                      │
│  └── Se OK → próxima etapa                                      │
│                                                                 │
│  FASE N: Finalização                                            │
│  └── Exibir relatório de conclusão                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
              │
              ▼
       workspace/[processo]/[artefato-final]
```

---

## Checklist de Validação

### Estrutura do Projeto

```
[ ] CLAUDE.md existe na raiz?
[ ] .claude/commands/ contém orquestradores?
[ ] .claude/agents/ organizado por categoria (não por pipeline)?
[ ] .claude/skills/ separa conhecimento de scripts?
[ ] .claude/spec/ contém templates?
```

### Qualidade dos Agents

```
[ ] Agent tem YAML frontmatter completo?
[ ] Agent tem color semântica correta?
[ ] Agent usa tags XML estruturadas?
[ ] Agent tem sinalizadores definidos?
[ ] Agent tem restrições claras (NUNCA, NÃO)?
[ ] Agent tem contingências para erros?
```

### Qualidade dos Orquestradores

```
[ ] Orquestrador é CEGO (não contém prompts inline)?
[ ] Orquestrador tem tabela de contratos?
[ ] Orquestrador tem validação por sinalizadores?
[ ] Orquestrador tem limite de tentativas (max 2)?
[ ] Orquestrador tem sufixos de correção?
[ ] Orquestrador tem <rastreamento_progresso> com padrão TodoWrite?
[ ] Etapa 0 cria TodoWrite com todas as etapas?
[ ] Subagentes estão proibidos de usar TodoWrite?
```

---

## Relação com Spec-Driven Development (SDD)

O Super Jurista Pack é uma **especialização** do paradigma Spec-Driven Development para o domínio jurídico. Não é uma implementação completa do SDD clássico, mas compartilha princípios fundamentais.

### Mapeamento de Conceitos

| Conceito SDD | Equivalente no Super Jurista | Diferença |
|--------------|------------------------------|-----------|
| **Requirements** | Análise do caso judicial | Requisitos vêm dos autos, não de stakeholders |
| **Design Spec** | Estrutura do pipeline | Fixo por tipo (sentença, embargos, pesquisa) |
| **Implementation Tasks** | Etapas do pipeline | Sequenciais, validadas por sinalizadores |
| **Steering Docs** | CLAUDE.md | Simplificado para uso pessoal |
| **Property-Based Testing** | Sinalizadores de formato | Validação mais simples mas suficiente |

### O Que Adotamos do SDD

1. **Especificação antes de execução**: Agents e orquestradores são definidos em specs antes de executar
2. **Contratos explícitos**: Cada etapa tem entrada/saída documentada
3. **Validação contínua**: Sinalizadores verificam conformidade entre etapas
4. **Isolamento de contexto**: Subagentes têm visão limitada (princípio de menor privilégio)

### O Que NÃO Adotamos (intencionalmente)

1. **EARS (Easy Approach to Requirements Specification)**: Requisitos jurídicos são extraídos dos autos, não especificados formalmente
2. **Steering Docs múltiplos**: CLAUDE.md único é suficiente para uso pessoal
3. **Property-Based Testing**: Custo-benefício não justifica para pipeline jurídico
4. **Flexibilidade de fluxo**: Pipelines são determinísticos por design

### Por Que Essa Especialização?

O domínio jurídico tem características únicas:
- **Entrada padronizada**: Processos judiciais seguem estrutura definida
- **Saída previsível**: Sentenças, decisões, pareceres têm formato conhecido
- **Validação crítica**: Erros jurídicos têm consequências sérias
- **Rastreabilidade**: Cada afirmação deve ter referência aos autos

Essas características justificam um framework mais rígido que o SDD genérico.

---

## Referências

### Especificações Oficiais
- **Agent Skills Specification:** https://agentskills.io/specification
- **Skills Repository:** https://github.com/anthropics/skills
- **Padrão Anthropic (Agents):** https://github.com/anthropics/claude-code/tree/main/plugins/feature-dev/agents

### Documentação Interna
- **Estrutura canônica:** `docs/90-arquitetura-canonica-claude-code.md`
- **Guia de pipelines:** `docs/70-guia-arquitetura-pipelines-workflows.md`

### Templates (uso direto)
- **Agent:** `${CLAUDE_PLUGIN_ROOT}/spec/templates/agent.md`
- **Orquestrador:** `${CLAUDE_PLUGIN_ROOT}/spec/templates/orquestrador.md`
- **Command Simples:** `${CLAUDE_PLUGIN_ROOT}/spec/templates/command-simples.md` (v2.5)
- **Skill:** `${CLAUDE_PLUGIN_ROOT}/spec/templates/skill.md`

### Referências (consulta)
- **Checklist de Validação Agent:** `${CLAUDE_PLUGIN_ROOT}/spec/referencias/checklist-validacao-agent.md`
- **Checklist de Validação Orquestrador:** `${CLAUDE_PLUGIN_ROOT}/spec/referencias/checklist-validacao-orquestrador.md`
- **Variantes de Subagente:** `${CLAUDE_PLUGIN_ROOT}/spec/referencias/variantes-subagente.md`
- **Contrato Avançado:** `${CLAUDE_PLUGIN_ROOT}/spec/referencias/contrato-avancado.md`
- **Exemplo Agent Corrigido:** `${CLAUDE_PLUGIN_ROOT}/spec/referencias/exemplo-agent-corrigido.md` (v2.4)
- **Refatoracao Skills Fork:** `${CLAUDE_PLUGIN_ROOT}/spec/referencias/refatoracao-skills-fork.md` (v2.7)

---

**Framework:** Super Jurista
**Versao:** 2.7
**Data:** 2026-01-29

### Changelog

**v2.7 (2026-01-29)** - Skills com Contexto Isolado
- **NEW:** Campo `context: fork` para skills - executa em sub-agente isolado
- **NEW:** Campo `agent` para skills - especifica tipo de agente quando usando fork
- **NEW:** Skill `capturar-sessao-pje` - isola fase de captura de sessao do PJE
- **NEW:** Script `extrair_cookies_har.py` - fallback quando Chrome MCP falha
- **REFACTOR:** Skills `pje-download` e `converter-pdf` refatoradas para modelo enxuto
- **REFACTOR:** Documentacao rica movida para `references/documentacao-completa.md`
- **PATTERN:** Novo padrao "Skills Imperativas" - instrucoes diretas, sem espaco para interpretacao
- **PATTERN:** Commands agora usam instrucoes literais ("Executar EXATAMENTE")
- **PATTERN:** Fases que consomem contexto devem ser isoladas em skills com fork
- **DOC:** Template de skill atualizado com campos de isolamento
- **DOC:** Nova secao "Skills com context: fork" no README
- **SCORE:** Pack atualizado para ~95/100

**v2.6 (2026-01-20)** - Documentação Conceitual
- **NEW:** Seção "Relação com Spec-Driven Development (SDD)" - posiciona o framework em relação ao ecossistema
- **DOC:** Mapeamento de conceitos SDD → Super Jurista
- **DOC:** Explicação do que adotamos e o que não adotamos do SDD

**v2.5 (2026-01-20)** - Correções e Clarificações
- **FIX:** Reescrita da seção "Orquestrador Cego" - agora explica claramente o que FAZ e NÃO FAZ
- **FIX:** Diagrama de fluxo corrigido - removidos caminhos v1 (`.claude/agents/xxx/etapa-01.md`)
- **NEW:** Seção "Agent vs Skill: Quando Usar Cada Um" - guia de decisão com exemplos
- **NEW:** Seção "Tags `<capacidade>` vs `<proposito>`" - diferença clara entre as tags
- **NEW:** Seção "Por que Organização por Categoria" - justificativa arquitetural
- **NEW:** Template `command-simples.md` v1.0 - para commands que não são orquestradores
- **DOC:** Tag `<proposito>` oficializada como opcional em agents
- **SCORE:** Pack atualizado para ~90/100

**v2.4 (2026-01-18)** - Calibração do Checklist de Agent + Correção
- **AUDITORIA:** Analisado `relator-marmelstein.md` - score 18/120 (REPROVADO)
- **CORRIGIDO:** Agent reescrito seguindo spec v2.0 - score 120/120 (EXCELENTE)
- **META:** Checklist calibrado com base em agent real do pipeline-sentenca
- **NEW:** Seção 5.2 - Verificação de pseudo-contratos em comentários
- **NEW:** Seção 5.3 - Detecção de tags v1 obsoletas (mapeamento v1→v2)
- **NEW:** Seção 6 - Modularidade e Granularidade (10 pts extra)
- **NEW:** Referência `exemplo-agent-corrigido.md` com transformações documentadas
- **UPDATE:** Score máximo de 100 para 120 pontos
- **UPDATE:** Checklist de agent agora versão 1.1

**v2.3 (2026-01-18)** - Checklist de Orquestrador
- **NEW:** Criado `checklist-validacao-orquestrador.md` com 10 seções e 62 itens de verificação
- **AUDITORIA:** Analisado orquestrador real, identificadas 23 desconformidades
- **AUDITORIA:** Gerado relatório detalhado em `AUDITORIA-ORQUESTRADOR.md`
- **SCORE:** Pack atingiu 80/100 - pronto para distribuição

**v2.2 (2026-01-18)** - Correções de Auditoria
- **FIX:** Corrigido exemplo `tools: Read, Write` para `tools: Read Write` (sem vírgula)
- **FIX:** Atualizado checklist de "namespacing por pipeline" para "organizado por categoria"
- **FIX:** Atualizados `variantes-subagente.md` e `contrato-avancado.md` para padrão v2 (`.claude/agents/[agent].md`)
- **AUDITORIA:** Gerado relatório completo em `AUDITORIA-SPECS.md`

**v2.1 (2026-01-18)** - Convenção de Nomenclatura de Arquivos
- Nova convenção: `[NUMERO]-tipo.md` para todos os arquivos de saída
- Facilita busca por arquivos do mesmo processo
- Atualizado manifest.md com nova estrutura de pastas
- Atualizado README.md com exemplos da convenção
- Atualizada tabela de contratos de dados

**v2.0 (2026-01-18)** - Arquitetura de Duas Camadas
- **BREAKING:** Agents movidos de `.claude/agents/[pipeline]/` para `.claude/agents/` (raiz)
- **BREAKING:** Agents agora definem CAPACIDADE, não caminhos hardcoded
- Nova seção "Arquitetura de Duas Camadas" no README
- Template agent.md v2.0: nova tag `<capacidade>` + `<contrato>`
- Template orquestrador.md v2.0: padrão de injeção $ARGUMENTS
- Novo template manifest.md para índice de workspace
- Documentado padrão de injeção de contexto ($ARGUMENTS → $WORKSPACE)
- Estrutura de workspace padronizada com `_manifest.md`
- Atualizada estrutura de diretórios refletindo arquitetura modular

**v1.4 (2026-01-18)**
- Template de Skill alinhado 100% com spec oficial (agentskills.io)
- Nova tag `<instrucoes>` mapeada para "Step-by-step instructions" da spec
- Tags `<exemplos>` e `<casos_de_borda>` alinhadas com "Examples" e "Edge cases"
- Corrigido formato `allowed-tools` (sem colchetes)
- Adicionado exemplo completo de skill (pdf-processing)
- Tabela de mapeamento XML ↔ Spec Oficial no template

**v1.3 (2026-01-18)**
- Integração do TodoWrite no template do orquestrador
- Nova seção `<rastreamento_progresso>` para controle de etapas
- Adicionada regra: subagentes NUNCA usam TodoWrite (evita race conditions)
- TodoWrite adicionado ao `allowed-tools` do orquestrador
- Checklist atualizado com itens de rastreamento

**v1.2 (2026-01-18)**
- Reorganizada estrutura: separação entre templates (uso direto) e referências (consulta)
- Movido `contrato.md` → `referencias/contrato-avancado.md` (uso opcional)
- Movido `prompt-subagente.md` → `referencias/variantes-subagente.md` (catálogo)
- Atualizada documentação de estrutura de diretórios

**v1.1 (2026-01-18)**
- Adicionada seção "Anatomia de uma Skill" com spec oficial Anthropic
- Documentado Progressive Disclosure para economia de tokens
- Corrigido nome de diretório: `reference/` → `references/`
- Adicionadas regras de validação para campos `name` e `description`
- Incluídas referências à spec oficial (agentskills.io)

**v1.0 (2026-01-18)**
- Versão inicial do framework
