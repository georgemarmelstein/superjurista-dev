# Changelog

## 1.1.0 (2026-07-04)

### Modernizado

- Meta-criadores (`/criar-orquestrador`, `/criar-agente`, `/criar-skill`) alinhados ao padrão v3.0:
  - **Retomada por varredura** (L13): a Etapa 0 do pipeline gerado roda um gate por script; a linha `PENDENTES` é o plano e etapa já válida não roda de novo.
  - **Gate por script** (L14): pipelines gerados nascem com `scripts/verificar_<sistema>.py` (importa `rodar_cli` do motor `verificar_pipeline.py`), validado por `--etapa`/`--gate`; o orquestrador não lê o documento para validar.
  - **Saída em disco + 1 linha** (L5): o subagente GRAVA o documento (Write) e responde apenas "etapa OK | arquivo"; nunca ecoa o conteúdo inline.
  - `/criar-orquestrador`: `allowed-tools` passou a incluir `Bash`; brainstorming aponta para a skill real `brainstorm`; Fase 2 gera o gate; checklist de 7 seções (/100) com seção v3.0 crítica.
  - `/criar-agente`: contrato de saída atualizado — `<formato_saida>` descreve o documento gravado + `<resposta_ao_orquestrador>` de 1 linha; `<sinalizadores>` como âncoras do gate; restrição "NÃO imprimir inline (L5)".
  - `/criar-skill`: padrão determinístico para skills com scripts ([INICIO]/[OK]/[ERRO]/[FIM], retorno resumido, zero-read/gate para mini-pipelines).
- **Templates** (`orquestrador`, `agent`, `skill`, `skill-agentica`) e **checklists/referências** (`checklist-validacao-orquestrador` → 130 pts com seções 7 e 8; `checklist-validacao-agent`; `variantes-subagente`) espelhados no padrão v3.0.
- Motor de gate embarcado em `scaffold/scripts/verificar_pipeline.py` (instalado no projeto-alvo por `/instalar-superjurista`).

### Corrigido

- Frontmatter YAML dos três meta-criadores movido para o TOPO do arquivo (antes vinha depois do H1, o que quebrava o carregamento do command).
- Removida referência à skill inexistente `brainstorming-pipeline` em `/criar-orquestrador`.
- Corrigidos caminhos de guia inexistentes em `/criar-skill` (`docs/2026-01-23-guia-escrita-skills.md` → `${CLAUDE_PLUGIN_ROOT}/skills/criar-skill/references/skill-writing-guide.md`).

## 1.0.0 (2026-03-20)

### Adicionado

- 6 comandos: criar-agente, criar-orquestrador, criar-skill, criar-team, planejar-sistema, instalar-superjurista
- 2 skills: criar-skill (TDD), criar-mcp-precedente
- Framework spec v2.7 completo (templates, referências, checklists)
- Scaffold judicial com 16 commands, ~52 agents, 6 skills, 2 MCPs
- README para juristas (scaffold)
- CLAUDE.md template (scaffold)
