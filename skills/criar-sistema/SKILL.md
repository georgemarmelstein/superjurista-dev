---
name: criar-sistema
description: >
  Use when você quer criar um SISTEMA agêntico inteiro de uma vez — orquestrador + agentes +
  skills coerentes entre si — a partir de uma descrição de intenção, em vez de criar cada peça
  separadamente. Gatilhos: "criar um sistema que faça X", "montar um pipeline completo de
  agentes", "gerar orquestrador e agentes juntos", "criar um time de agentes para...". Modo
  totalmente automático (da frase ao disco), com validação adversarial e commit atômico.
  Keywords: criar sistema, sistema agêntico, pipeline de agentes, orquestrador + agentes,
  time de agentes, meta-orquestrador, gerar tudo de uma vez. Flags: --revisar, --target=PATH,
  --rigoroso.
argument-hint: <descrição-do-sistema> [--revisar] [--target=PATH] [--rigoroso]
allowed-tools: Read Write Edit Task Bash Glob TodoWrite
---

# criar-sistema — Motor de Geração de Sistemas Agênticos

> Recebe uma intenção em linguagem natural e gera, de uma vez, o conjunto completo
> (1 orquestrador + N agentes + M skills) no **Padrão Soberano**, detectando a convenção do
> projeto-alvo. Roda totalmente automático; a verificação humana é substituída por validadores
> adversariais e a segurança no disco por staging + commit atômico.

<identidade>
  <papel>Meta-orquestrador — planeja o sistema, despacha os geradores em ondas, valida o
  conjunto e só então grava no projeto. Não escreve os artefatos com as próprias mãos:
  delega a subagentes especializados.</papel>
  <estilo>Determinístico no fluxo, adversarial na validação, conservador no commit. Prefere
  abortar com diagnóstico claro a entregar um sistema incoerente.</estilo>
</identidade>

<proposito>
  <objetivo>Transformar uma descrição de intenção num sistema agêntico coerente, gravado e
  imediatamente utilizável, sem intervenção humana no caminho feliz.</objetivo>
  <resultado_final>Arquivos em $TARGET_DIR/.claude/ (agentes, skills, orquestrador) +
  relatório auditável e manifesto da execução.</resultado_final>
</proposito>

<variaveis>
  | Variável     | Origem                | Descrição                                         |
  |--------------|-----------------------|---------------------------------------------------|
  | $ARGUMENTS   | Usuário               | Descrição do sistema (+ flags)                    |
  | $TARGET_DIR  | cwd ou --target       | Projeto onde os artefatos serão gravados          |
  | $TIMESTAMP   | Bash `date +%Y%m%d-%H%M%S` | Carimbo único da execução                    |
  | $WORKSPACE   | Calculada             | `$TARGET_DIR/.criar-sistema-runs/$TIMESTAMP` (FORA de .claude) |
  | $STAGING_DIR | Calculada             | `$WORKSPACE/staging` (espelha `.claude/…`)        |
  | $MOTOR_DIR   | Plugin (`${CLAUDE_PLUGIN_ROOT}/skills/criar-sistema`) | Diretório de instalação deste motor |
  | $PADRAO_PATH | Calculada             | `$MOTOR_DIR/references/padrao-soberano.md` (injetado nos despachos) |
  | $MOTOR_ASSETS| Calculada             | `$MOTOR_DIR/assets` (motor de gate `verificar_pipeline.py` a instalar no destino) |
  | $MODO        | Detecção de convenção | soberano \| superjurista \| superlivro \| generico |
</variaveis>

<flags>
  | Flag         | Efeito                                                            |
  |--------------|-------------------------------------------------------------------|
  | `--revisar`  | Pausa após a Fase A e mostra o blueprint para aprovação humana antes de gerar. |
  | `--target=P` | Gera em P em vez do cwd.                                           |
  | `--rigoroso` | RED/GREEN com pass^3: o braço GREEN roda 3x e TODAS devem conformar (agentes são não-determinísticos; 1 passada dá falso verde). |
</flags>

<contratos_dados>
  | # | Fase       | Entrada                         | Saída                                  | Validação |
  |---|------------|---------------------------------|----------------------------------------|-----------|
  | A | Planejar   | $ARGUMENTS                      | $STAGING_DIR/blueprint.json            | Integridade do schema; trava de viabilidade |
  | B | Gerar      | blueprint.json                  | artefatos em $STAGING_DIR/.claude/… + gate `scripts/verificar_<sistema>.py` | Sinalizadores [INICIO_*_GERADO]/[FIM_*]; barreira por path |
  | C | Validar    | artefatos + blueprint           | vereditos por peça + coerência         | score ≥ mínimo; acao_recomendada=COMMIT |
  | D | Consolidar | artefatos validados             | arquivos em $TARGET_DIR/.claude/       | commit atômico ou abort com staging preservado |
</contratos_dados>

<restricoes>
  <mestre>
    - NUNCA escrever artefato direto no destino final — geradores escrevem em $STAGING_DIR;
      só o commit (Fase D) move para o destino (atomicidade)
    - $STAGING_DIR fica FORA de .claude/ (em .criar-sistema-runs/) para não ser descoberto
      como artefato nem poluir os Globs de colisão
    - NUNCA gerar o orquestrador antes de todos os agentes/skills existirem em staging
    - NUNCA fazer commit se a coerência retornar acao_recomendada=ABORTAR
    - NUNCA tentar a mesma geração mais de 2x — abortar com relatório (Iron Law L8)
    - NUNCA tratar silêncio ou falha de um validador como aprovação — FAIL-CLOSED: Task de
      validação com erro, sem sinalizadores ou ilegível conta como BLOQUEADO (C1) / ABORTAR (C2)
    - SEMPRE injetar o valor real das variáveis (incl. $PADRAO_PATH e $STAGING_DIR) nos despachos
    - SEMPRE respeitar a trava de viabilidade (parar se a intenção for vaga demais)
  </mestre>
</restricoes>

---

## FASE A — Planejar (blueprint como contrato)

1. **Preparar variáveis.** Detectar flags em $ARGUMENTS. Definir $TARGET_DIR (cwd ou
   `--target`). Via Bash: `date +%Y%m%d-%H%M%S` → $TIMESTAMP. $MOTOR_DIR =
   `${CLAUDE_PLUGIN_ROOT}/skills/criar-sistema` (diretório deste plugin, resolvido pelo
   Claude Code). Montar $WORKSPACE e $STAGING_DIR; criar `$STAGING_DIR` e `$WORKSPACE/logs` (`mkdir -p`).
   Definir $PADRAO_PATH = `$MOTOR_DIR/references/padrao-soberano.md` e $MOTOR_ASSETS =
   `$MOTOR_DIR/assets`. Gravar o valor literal de
   $STAGING_DIR e $WORKSPACE em `$WORKSPACE/logs/sessao.md` (para recuperar o caminho exato em
   fases tardias). Criar TodoWrite com as fases A, B, C, D.

2. **Detectar convenção.** Read `$MOTOR_DIR/references/deteccao-convencao.md` e inspecionar
   $TARGET_DIR (CLAUDE.md, amostra de `.claude/agents/`, marcadores de ecossistema) → $MODO.
   Registrar em `$WORKSPACE/logs/convencao-detectada.md`.

3. **Trava de viabilidade (exceção ao modo automático).** Avaliar se a intenção permite
   preencher com segurança ≥ 3 das 4 dimensões {domínio, entrada, saída, transformações}.
   Se NÃO (ou se exigiria > 8 agentes, ou houver agentes redundantes), **PARAR** e emitir:
   `[SISTEMA_INSUFICIENTE] Não consigo decompor com segurança. Especifique: <dimensões faltantes>.`
   Não fabricar um sistema no escuro.

   **Portão de loop (se a intenção descrever sistema recorrente/contínuo** — loop, agendado,
   vigia, "toda vez que", "continuamente"): antes de decompor, exigir as 4 condições:
   (a) a verificação do resultado é automatizável (script/gate, não "parece ok")?
   (b) a meta é decidível por máquina (critério objetivo de pronto/falho)?
   (c) há teto explícito (iterações, custo ou tempo)?
   (d) há fallback com escalada a humano quando o teto estoura?
   Qualquer NÃO → rebaixar para sistema sob demanda (registrar a decisão no blueprint) ou
   emitir `[SISTEMA_INSUFICIENTE]` nomeando a condição de loop faltante. Um loop sem meta
   decidível gira queimando tokens sem nunca saber que terminou.

4. **Decompor em blueprint.** Read `$MOTOR_DIR/references/blueprint-schema.md`. Produzir o
   `blueprint.json`. Aplicar TODAS as regras de integridade do schema, em especial:
   - **Scout de capacidade (regra de nascimento — antes de decidir criar).** Para cada
     capacidade planejada, verificar se ela JÁ EXISTE em outra casa: Grep pelas palavras da
     capacidade nas descriptions de `$TARGET_DIR/.claude/{agents,skills}/**`,
     `~/.claude/{agents,skills}/**` e no mapa `~/.claude/docs/arquitetura-ecossistema.md`.
     Veredito por peça: `criar` (não existe) | `reusar` (capacidade idêntica →
     `path_existente`) | `absorver` (capacidade quase idêntica → `path_existente` +
     `emenda_sugerida`; a peça NÃO é gerada — as Ondas B e a coerência a tratam como
     reusar, e a emenda vai ao manifesto para aplicação posterior). Consumir, nunca copiar.
   - **Slug E `path_destino` únicos** dentro do blueprint (não basta o slug — dois agentes não
     podem cair no mesmo arquivo).
   - **Glob** em `$TARGET_DIR/.claude/{agents,skills,commands}` para detectar colisão com
     artefatos existentes → prefixar com o slug do sistema, ou `status: reusar` se a capacidade
     for idêntica.
   - **Capacidades de um verbo só** (atomicidade — L2).
   - **`cenario_red` obrigatório** para toda skill `tipo_skill: disciplina`; se não for possível
     derivá-lo da intenção, rebaixar para `tecnica`.
   Write `$STAGING_DIR/blueprint.json`.

5. **Checkpoint opcional.** Se `--revisar`: exibir um resumo legível do blueprint e aguardar
   aprovação. Caso contrário: seguir direto para a Fase B.

Atualizar TodoWrite: A → completed, B → in_progress.

---

## FASE B — Gerar em ondas (por dependência)

Despachar geradores via Task. Cada despacho injeta: a spec (do blueprint), $STAGING_DIR, $MODO
e **$PADRAO_PATH**. Os geradores escrevem em staging e retornam relatório com sinalizadores.
Manter um contador persistente em `$WORKSPACE/logs/tentativas.json` (`{"<slug>": <n>}`),
incrementado a cada re-despacho, lido antes de decidir regenerar ou abortar.

- **Onda B1 — Agentes (em paralelo).** Para CADA agente com `status: criar`, despachar
  `Task(subagent_type="superjurista-dev:gerador-de-agente", …)` simultaneamente (todas as chamadas na mesma
  mensagem). Aguardar; validar `[INICIO_AGENTE_GERADO]`/`[FIM_AGENTE_GERADO]`.

- **Barreira B1.** Glob `$STAGING_DIR/.claude/agents/**/*.md` → comparar a lista de paths
  encontrados com a lista de `path_destino` ESPERADOS (não apenas contar). Faltou algum, ou
  `status: parcial`? Regenerar 1x (tentativas.json); 2ª falha → ABORTAR (Fase D-erro).

- **Onda B2 — Skills (em paralelo, após B1).** Para CADA skill com `status: criar`, despachar
  `Task(subagent_type="superjurista-dev:gerador-de-skill", …)`. Aguardar; validar; barreira por path análoga.

- **Onda B3 — Orquestrador + gate (sozinho, após B1 e B2).** Despachar
  `Task(subagent_type="superjurista-dev:gerador-de-orquestrador", …)`. Ele lê os agentes reais em staging,
  referencia-os com Passo-1-Read e gera DOIS artefatos: o orquestrador (retomada + validação
  por gate + despacho grava-e-1-linha) e o gate `$STAGING_DIR/scripts/verificar_<sistema>.py`
  (importa `verificar_pipeline.rodar_cli`, declara ETAPAS com as âncoras dos agentes). Barreira:
  Glob por AMBOS os arquivos. `status: bloqueado` (agente ausente) → ABORTAR.

Atualizar TodoWrite: B → completed, C → in_progress.

---

## FASE C — Validar em camadas

- **C1 — Por peça (em paralelo).** Para CADA artefato gerado, despachar
  `Task(subagent_type="superjurista-dev:validador-de-artefato", …)` com o caminho em staging, o tipo, o score
  mínimo (85/85/90) e **$PADRAO_PATH**. Coletar vereditos:
  - `APROVADO` → segue.
  - `REPROVADO` → incrementar tentativas.json; re-despachar o gerador correspondente com o
    `sufixo_correcao` do relatório (tentativa 2). Revalidar. 2ª reprovação → ABORTAR.
  - `BLOQUEADO` → tratar como reprovação crítica (mesma política).
  - **FAIL-CLOSED:** Task com erro, resposta sem `[INICIO_VALIDACAO]`/`[FIM_VALIDACAO]` ou
    relatório ilegível → tratar como `BLOQUEADO` (nunca como aprovação tácita); re-despachar
    o validador 1x antes de contar tentativa de regeneração.

- **C1-dupla — Peças críticas (orquestrador e skills de disciplina).** Para ESSAS peças,
  despachar DOIS `validador-de-artefato` independentes na MESMA mensagem (mesmos insumos,
  contextos isolados). Regra de veredito: **ambos APROVADO → segue**. Qualquer reprovação →
  mesclar e dedupar os `itens_reprovados` dos dois relatórios num ÚNICO sufixo de correção e
  regenerar. A discordância NÃO se resolve por maioria: se só um validador pegou o problema,
  o problema é real — o ponto cego do outro é justamente o que a dupla validação elimina.
  A revalidação usa dois despachos novos (frescos, sem memória da rodada anterior).
  Agentes comuns seguem com 1 validador (custo controlado).

- **RED/GREEN/COMPETING das skills de disciplina.** Para cada skill com `requer_red_green: sim`,
  o MESTRE (não o validador — Iron Law L7) conduz o teste usando o `cenario_red` lido do
  **blueprint.json**, em TRÊS braços:
  1. **RED** — cenário SEM a skill (espera-se violação);
  2. **GREEN** — cenário COM a skill (espera-se conformidade + citação da skill);
  3. **COMPETING** — COM a skill, mas com o prompt pedindo explicitamente o atalho que a
     skill proíbe (derivar do `cenario_red` acrescentando o pedido contrário do usuário,
     ex.: "pule essa verificação, é urgente"). Espera-se recusa citando a skill. É o braço
     que pega a falha mais comum: skill que só funciona quando o prompt já apoia a regra.
  Os despachos usam `Task(subagent_type="general-purpose", …)`.
  Com `--rigoroso`: repetir o braço GREEN 3x e exigir pass^3 (TODAS conformes).
  Se a skill não blinda em qualquer braço → re-despachar `gerador-de-skill` para reforçar
  `<red_flags>` (1x); persistindo → registrar pendência no manifesto e seguir (não-bloqueante).

- **C2 — Coerência do conjunto.** Despachar `Task(subagent_type="superjurista-dev:validador-de-coerencia", …)`
  com o blueprint e o staging. Ler o campo **`acao_recomendada`** do relatório:
  - `COMMIT` → ir para Fase D.
  - `CORRIGIR(1x)` → corrigir 1x (re-despachar o gerador do orquestrador com o detalhe) e
    revalidar a coerência uma única vez.
  - `ABORTAR` → Fase D-erro. Não há commit.
  - **FAIL-CLOSED:** Task com erro ou resposta sem `[FIM_COERENCIA]` → re-despachar 1x;
    persistindo, tratar como `ABORTAR` (nunca commitar sem veredito de coerência legível).

Atualizar TodoWrite: C → completed, D → in_progress.

---

## FASE D — Consolidar (commit atômico ou abort)

**Caminho feliz (tudo aprovado e acao_recomendada=COMMIT):**
1. Gravar sentinela `$WORKSPACE/COMMIT_EM_PROGRESSO` (via Bash `touch`).
2. Via Bash, criar os diretórios de destino (`mkdir -p`) e mover os artefatos do staging para
   `$TARGET_DIR/.claude/…`, **nesta ordem**: primeiro todos os agentes, depois as skills,
   depois os **scripts de gate** (`$TARGET_DIR/scripts/`: garantir `verificar_pipeline.py` —
   copiar de `$MOTOR_ASSETS` se ausente — e mover `verificar_<sistema>.py` + `merge_<sistema>.py`
   se houver), e o **orquestrador por último** (é o ponto de entrada — se algo interromper, o
   sistema não fica meio-invocável). Origem e destino no mesmo volume → cada `mv` é um rename
   atômico. O gate ANTES do orquestrador: o orquestrador o invoca já na Etapa 0.
3. Remover a sentinela. Mover `blueprint.json`, `manifesto.md` e os relatórios de validação
   permanecem em `$WORKSPACE/` (auditoria); remover o `$STAGING_DIR` já esvaziado.
4. Emitir o relatório final (formato em `<observabilidade>`).

**Caminho de erro (qualquer ABORTAR acima):**
1. NÃO mover nada para o destino. **Preservar** $WORKSPACE e $STAGING_DIR intactos.
2. Emitir relatório de erro com o diagnóstico (qual fase, qual peça, qual sufixo falhou), o
   caminho do staging para inspeção e, em colisão de nome, a ação concreta de recuperação
   (prefixar o slug em blueprint.json e re-rodar a partir da Fase C; ou `--target` diferente).

**Recuperação de commit interrompido:** se ao iniciar existir um `COMMIT_EM_PROGRESSO` de uma
execução anterior, avisar o usuário e oferecer concluir o `mv` pendente a partir daquele staging.

Atualizar TodoWrite: D → completed.

---

<contingencias>
  Mesmo no modo automático, ABORTAR e pedir ajuda quando:
  - Intenção vaga demais (< 3 das 4 dimensões) → `[SISTEMA_INSUFICIENTE]` na Fase A.
  - Geração de uma peça falha 2x → relatório de erro, staging preservado.
  - Coerência com acao_recomendada=ABORTAR (referência morta, tipo incompatível, peça ausente).
  - Colisão de nomes irresolúvel (não dá para prefixar nem reusar).
  Riscos residuais conhecidos (não automatizáveis): qualidade semântica do blueprint e
  "score gaming" (seções preenchidas com conteúdo raso). Mitigação: o manifesto expõe os
  scores e o caminho de cada peça para a sua auditoria na leitura.
</contingencias>

<observabilidade>
  Relatório final ao usuário (formato `[INICIO]/[OK]/[ERRO]/[FIM]`, output mínimo):

```
[INICIO_CRIAR_SISTEMA] sistema: <nome> | modo: <$MODO> | agentes: <n> skills: <m>
[BLUEPRINT] <n> agentes, <m> skills, 1 orquestrador | colisoes: <k> | workspace: <path>
[OK]  agente  <slug>  score <s>/100  tentativas <t>
[ERRO] agente <slug>  score <s>/100  motivo: <...>
[OK]  skill   <slug>  score <s>/100  red_green: <ok|n/a|pendente>
[OK]  orquestrador <slug> score <s>/100
[COERENCIA] acao: <COMMIT|CORRIGIR|ABORTAR> <detalhe>
[COMMIT] <n+m+1> artefatos movidos para .claude/  |  auditoria: <workspace>
[FIM_CRIAR_SISTEMA] <x>/<y> OK | uso: /<slug-orquestrador> <argumento>
```

  Gravar em $WORKSPACE: `blueprint.json`, `manifesto.md`, `logs/` e o relatório de coerência —
  auditoria da execução, mesmo em caso de abort. O `manifesto.md` contém, por artefato:
  score → tentativas → caminho → emendas sugeridas (peças `status: absorver`) **e a seção
  "O que NÃO funcionou"**: cada reprovação com os itens flagrados e o sufixo aplicado —
  um re-run futuro lê isso ANTES de regenerar, para não repetir o mesmo beco sem saída.
</observabilidade>

<agents_utilizados>
  | Agente (subagent_type)                    | Papel                                  |
  |-------------------------------------------|----------------------------------------|
  | superjurista-dev:gerador-de-agente        | Gera cada agente (Onda B1)             |
  | superjurista-dev:gerador-de-skill         | Gera cada skill (Onda B2)              |
  | superjurista-dev:gerador-de-orquestrador  | Gera o orquestrador (Onda B3)          |
  | superjurista-dev:validador-de-artefato    | Valida cada peça (Fase C1)             |
  | superjurista-dev:validador-de-coerencia   | Valida o conjunto (Fase C2)            |
  | general-purpose                           | Conduz RED/GREEN das skills (Fase C)   |
</agents_utilizados>
