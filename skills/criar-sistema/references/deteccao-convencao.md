# Detecção de Convenção do Projeto-Alvo

> O motor `/criar-sistema` vive globalmente, mas gera artefatos DENTRO de um projeto-alvo
> (o cwd da invocação). Antes de gerar, ele inspeciona esse projeto e decide entre aplicar
> o **Padrão Soberano** puro ou respeitar uma convenção local já estabelecida — para não
> introduzir um agente em estilo estranho ao que já existe ali.
>
> Esta detecção roda na Fase A e grava o resultado em `meta.modo_convencao` do blueprint
> e em `logs/convencao-detectada.md`.

---

## Sequência de inspeção

1. **Ler `CLAUDE.md` do projeto-alvo.** Se mencionar convenção explícita ("use P.O.E.M.A.",
   "siga o padrão SuperJurista", "agentes XML-semântico"), isso tem prioridade máxima →
   registrar como `CONVENCAO_LOCAL_DECLARADA`.

2. **Amostrar agentes existentes.** Glob `.claude/agents/**/*.md`; ler os 3 primeiros e
   identificar o esquema de tags predominante:
   - `<identidade>/<capacidade>/<contrato>/<restricoes>` → **convenção v2** (Soberano-compatível)
   - `<persona>/<objetivo>/<estilo>/<modelo>` → **P.O.E.M.A. v1** (obsoleta)
   - Markdown com "5 Cs" (CHARACTER/CAUSE/CONSTRAINT/CONTINGENCY/CALIBRATION) → convenção `agent-implementation`
   - Sem tags XML / ausência de agentes → **projeto virgem**

3. **Marcadores de ecossistema.**
   - `.claude/specs/` presente → ecossistema **SuperJurista** (ler versão do checklist).
   - `.claude/series/` ou `.claude/perfis-autorais/` presente → ecossistema **SuperLivro**.
   - `.claude/skills/<x>/SKILL.md` como orquestrador de entrada → padrão de orquestração por skill.

---

## Tabela de decisão

| Contexto detectado | `modo_convencao` | Ação do motor |
|--------------------|------------------|---------------|
| Projeto virgem (sem agentes) | `soberano` | Padrão Soberano integral |
| SuperLivro (`.claude/series/` presente) | `superlivro` | Padrão Soberano + extensões de domínio liberadas (tags extras nomeadas); orquestrador como SKILL.md |
| SuperJurista v2 (`.claude/specs/` + tags v2) | `superjurista` | Padrão Soberano; orquestrador como **command** em `.claude/commands/`; harmonizar description para CSO |
| SuperJurista v1 (tags `<persona>/<objetivo>`) | `superjurista` | Modo compatibilidade: gerar em **v2** e registrar mapeamento v1→v2 no relatório |
| Convenção explícita em CLAUDE.md | conforme declarado | Respeitar a convenção local; aplicar somente as Iron Laws universais (L1–L12) |

---

## Diferenças concretas por modo

O esqueleto (tags v2, Iron Laws, sinalizadores) é o mesmo em todos os modos. O que muda:

- **Tipo do orquestrador.** `superlivro`/`soberano` → SKILL.md auto-trigger.
  `superjurista` → command `.md` com `argument-hint` + `allowed-tools` (inclui TodoWrite).
- **Profundidade do agente.** `superlivro` permite e incentiva extensões ricas
  (`<hierarquia_de_autoridade>`, `<ecos>`, `<diversidade_compositiva>`). `superjurista`
  tende a agentes mais enxutos focados na capacidade.
- **`<example>` na description.** Liberado para agentes que possam ser ativados direto pelo
  usuário; dispensável para agentes puramente orquestrados.

---

## Princípio

Na dúvida entre dois modos, **prefira o Padrão Soberano** (ele é superconjunto compatível).
Nunca gere em P.O.E.M.A. v1 (tags obsoletas), mesmo num projeto que ainda as use — gere em
v2 e ofereça o mapeamento. O objetivo da detecção é *encaixar*, não *clonar defeitos*.
