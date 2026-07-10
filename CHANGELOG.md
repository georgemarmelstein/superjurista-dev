# Changelog

## 1.2.0 (2026-07-10)

### Adicionado

- **3 novos servidores MCP no scaffold** (o `/instalar-superjurista` agora entrega 5):
  - `bnp-api` — Banco Nacional de Precedentes do CNJ (STF/STJ, precedentes qualificados).
  - `cjf-jurisprudencia` — portal unificado do CJF (STF, STJ, TRFs; JSF/PrimeFaces).
  - `tnu-eproc` — jurisprudência VIVA da TNU via eProc, com inteiro teor real por id,
    citação oficial pronta e sintaxe validada empiricamente (engenharia reversa 10/07/2026).
- **Registro automático no `.mcp.json`**: nova etapa do `/instalar-superjurista` gera/mescla
  o `.mcp.json` na raiz do projeto com os 5 servidores (caminho absoluto, merge idempotente
  testado). Antes, o instalador copiava os arquivos mas nunca os registrava — os MCPs não
  carregavam para quem instalava.

### Corrigido

- READMEs dos 5 servidores do scaffold normalizados: registro via `.mcp.json` da raiz
  (settings.json era padrão antigo e falhava silenciosamente) e caminhos pessoais de
  desenvolvimento removidos das instruções.
- `scaffold/project-claude.md`: tabela de MCPs agora corresponde ao que o scaffold entrega
  (adicionados TCU e TNU; JULIA anotado como não incluído por exigir credenciais), com a
  divisão de trabalho entre as bases; árvore de diretórios atualizada.

## 1.1.1 (2026-07-10)

### Modernizado

- **Skill `criar-mcp-precedente`** atualizada com as lições dos 4 casos reais desde a sua
  criação (TCU 02/2026, TJSC/eProc 03/2026, HUDOC/CEDH 07/2026 e TSE/SJUR 07/2026):
  - **Registro no `.mcp.json`** da raiz do projeto (caminho absoluto) — a instrução antiga
    (settings.json) é padrão descontinuado e falha silenciosamente.
  - **Template refatorado**: busca implementada uma única vez em `_fazer_busca()`
    compartilhada entre `buscar_*` e `gerar_relatorio_*` (fim do convite ao copy-paste),
    com notas de charset legado (`response.encoding = "iso-8859-1"` para eProc) e de
    paginação com reaproveitamento de cookies.
  - **Terceira rota de roteamento**: CAPTCHA por requisição (hCaptcha/reCAPTCHA) ⇒ criar
    SKILL via Chrome MCP em vez de MCP server (modelo comprovado no SJUR/TSE), com a dica
    de mapear endpoints parcialmente abertos (inteiro teor às vezes dispensa CAPTCHA).
  - **Padrões novos no conhecimento**: múltiplas bases pesquisáveis (TCU — `Literal` +
    extractor por base + `listar_bases_*`), query builder para APIs com linguagem própria
    (HUDOC) e escopo ampliado a cortes internacionais.
  - **Nova referência** `references/licoes-de-campo.md`; exemplo JurisDF anotado como
    descontinuado (padrão continua válido); URL da mcp-builder corrigida
    (github.com/anthropics/skills).

## 1.1.0 (2026-07-10)

### Adicionado

- **Skill `criar-sistema`** — motor de geração de sistemas agênticos inteiros (1 orquestrador +
  N agentes + M skills) a partir de uma descrição de intenção: blueprint como contrato, geração
  em ondas, validação adversarial e commit atômico. Vem com 5 agentes próprios (primeira leva de
  `agents/` do plugin): `gerador-de-agente`, `gerador-de-skill`, `gerador-de-orquestrador`,
  `validador-de-artefato` e `validador-de-coerencia`, além das referências `padrao-soberano.md`
  (14 Iron Laws), `blueprint-schema.md` e `deteccao-convencao.md`.
- **2FA TOTP no PJe** (scaffold `capturar-sessao-pje`): o PJe TRF5 2.11 (05/2026) passou a exigir
  segundo fator no login. Nova Etapa 4.5 gera o código de 6 dígitos por software
  (`scripts/gerar_totp.py`, RFC 6238) a partir do seed em `.env` (`PJE_TOTP_SEED`), sem depender
  do celular. Diagnóstico em `references/2fa-totp.md`.
- **Gates do pipeline-sentenca no scaffold**: `verificar_sentenca.py` (varredura/`--etapa`/`--gate`)
  e `merge_sentenca.py` (merge da sentença por script, sem LLM) em `scaffold/scripts/`.

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
- **`scaffold/commands/pipeline-sentenca.md` v2.2 → v3.0**: retomada por etapa (etapa válida não
  redespacha), validação SÓ por script, subagente responde 1 linha, merge por script e
  paralelismo permitido ENTRE processos (fim do "um por vez").
- **`scaffold/project-claude.md`** com a doutrina v3.0 (validação por gate de script; múltiplos
  processos em paralelo na mesma sessão) e a nota do 2FA.
- **`spec/README.md`** sincronizado com a v3.0 (nota de atualização no topo; seções antigas de
  validação por leitura marcadas como legado).

### Corrigido

- Frontmatter YAML dos três meta-criadores movido para o TOPO do arquivo (antes vinha depois do H1, o que quebrava o carregamento do command).
- Removida referência à skill inexistente `brainstorming-pipeline` em `/criar-orquestrador`.
- Corrigidos caminhos de guia inexistentes em `/criar-skill` (`docs/2026-01-23-guia-escrita-skills.md` → `${CLAUDE_PLUGIN_ROOT}/skills/criar-skill/references/skill-writing-guide.md`).
- `spec/README.md`: caminhos com o typo `.claude/specs/` corrigidos para `spec/` do plugin.
- Removido o MCP `jurisdf-tjdft` (descontinuado) da tabela de servidores do `scaffold/project-claude.md`.

## 1.0.0 (2026-03-20)

### Adicionado

- 6 comandos: criar-agente, criar-orquestrador, criar-skill, criar-team, planejar-sistema, instalar-superjurista
- 2 skills: criar-skill (TDD), criar-mcp-precedente
- Framework spec v2.7 completo (templates, referências, checklists)
- Scaffold judicial com 16 commands, ~52 agents, 6 skills, 2 MCPs
- README para juristas (scaffold)
- CLAUDE.md template (scaffold)
