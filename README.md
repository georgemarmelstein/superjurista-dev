# superjurista-dev

Plugin de meta-ferramentas para criar e customizar sistemas agênticos judiciais com Claude Code. Inclui ferramentas para criar agentes, orquestradores, skills, teams e um scaffold completo do sistema SuperJurista -- um sistema de inteligência aumentada para processamento de processos judiciais, construído com arquitetura de pipelines determinísticos.

## Instalação

### 1. Via GitHub (recomendado)

```
/plugin marketplace add georgemarmelstein/superjurista-dev
/plugin install superjurista-dev@georgemarmelstein/superjurista-dev
```

### 2. Para desenvolvimento local

```bash
git clone https://github.com/georgemarmelstein/superjurista-dev.git
claude --plugin-dir ./superjurista-dev
```

## Comandos

| Comando | Descrição |
|---------|-----------|
| `/instalar-superjurista` | Instala o sistema SuperJurista completo no projeto atual |
| `/criar-agente` | Cria agentes modulares seguindo as SPECs v2.0 |
| `/criar-orquestrador` | Cria orquestradores (commands) com injeção de contexto |
| `/criar-skill` | Cria skills com TDD e CSO (Claude Search Optimization) |
| `/criar-team` | Cria Agent Teams (paralelo ou debate) |
| `/planejar-sistema` | Gera blueprint arquitetural antes de criar artefatos |

## Skills

- **criar-skill**: Workflow TDD para criação de skills -- garante que a skill ensina o comportamento correto ao Claude, com testes de conformidade e otimização para busca interna.
- **criar-mcp-precedente**: Guia para criar servidores MCP de jurisprudência com scraping de tribunais, incluindo padrões de extração e configuração de endpoints.
- **criar-pje-download**: Cria skills de download do PJE para qualquer tribunal via engenharia reversa de arquivos HAR -- identifica endpoints, cookies, headers e gera scripts Python parametrizados.

## O que o /instalar-superjurista cria

O comando `/instalar-superjurista` gera um sistema judicial completo no projeto atual:

- **16 pipelines e comandos** para processamento judicial (sentença, embargos, pesquisa, revisão, etc.)
- **~52 agentes especializados** em 7 categorias (extração, análise, pesquisa, redação, revisão, lista-trf, tribunal)
- **6 skills de domínio** (download PJE, conversão PDF, análise probatória, captura de sessão, etc.)
- **2 servidores MCP** (TJSC eProc, TCU)
- **Estrutura de dados pronta** (`data/sentenca/`, `data/decisao/`)
- **CLAUDE.md e README.md** configurados para o projeto

## Framework

O sistema baseia-se no framework v2.7 de orquestração agêntica com padrão "Orquestrador Cego" e injeção de contexto. Neste padrão, commands (orquestradores) delegam tarefas via Task tool para subagentes que possuem contexto isolado -- cada agente lê seu próprio prompt e recebe apenas os caminhos de workspace necessários. Templates e referências completas estão disponíveis em `spec/`.

## Licença

[MIT](LICENSE)
