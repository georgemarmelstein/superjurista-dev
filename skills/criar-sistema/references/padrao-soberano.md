# Padrão Soberano — Formato Canônico Unificado (v3.0)

> Documento de referência mestre do motor `/criar-sistema`.
> TODO subagente gerador e validador lê este arquivo no passo 1 da sua execução.
> Define: as 14 Iron Laws, os 3 templates canônicos (orquestrador, agente, skill de
> conhecimento), as regras de modelo/cor e a resolução de conflitos entre convenções.

O Padrão Soberano é a síntese do melhor de duas convenções que convivem no ambiente:
o **orquestrador-cego** disciplinado (injeção de contexto, self-bootstrap, checklists
pontuados) e o **agente XML-semântico rico** (contrato explícito, sinalizadores,
hierarquia de autoridade). Ele governa o que o motor emite, mas se adapta à convenção
local do projeto-alvo quando ela existe (ver `deteccao-convencao.md`).

## O que mudou na v3.0 (o encanamento, não a filosofia)

A filosofia é a mesma: orquestrador cego, injeção de contexto, contratos por tipo,
menor privilégio. O que mudou foi como as peças conversam em execução — as quatro
correções que aposentam os "andaimes da era 200k":

1. **Saída em disco + status de 1 linha.** O subagente GRAVA o documento no arquivo
   (Write) e responde ao orquestrador apenas uma linha ("etapa OK | arquivo"). O
   documento nunca volta inline na resposta. (Antes: o agente devolvia o texto
   inteiro emoldurado por sinalizadores, e o orquestrador o lia.)
2. **Retomada por varredura.** Um gate por script varre o workspace e imprime
   `PENDENTES: ...` — que É o plano de execução. Etapa cujo artefato já passa no gate
   não roda de novo. Primeira rodada e retomada pós-falha são a MESMA operação.
3. **Validação determinística por script.** As âncoras de início/fim de cada etapa
   são conferidas por `verificar_<sistema>.py` (com acentos/caixa normalizados), não
   pelo orquestrador lendo o documento. O orquestrador só vê o exit-code / a linha
   PENDENTES.
4. **Merge/handoff por script.** Concatenação e passagem de resultado entre etapas
   não passam pelo contexto do orquestrador: um script concatena/valida, ou o handoff
   é uma única linha extraída por `grep`.

O molde vivo desse padrão é `.claude/commands/pipeline-sentenca.md` (v3.0) com
`scripts/verificar_sentenca.py`/`merge_sentenca.py`; o motor de gate reutilizável é
`scripts/verificar_pipeline.py`.

---

## As 14 Iron Laws

Leis invioláveis. Uma violação é **falha crítica de validação**, independente do score.

- **L1 — Nome com componente único.** Nenhum artefato tem nome genérico que o Claude
  possa presumir conhecer. Todo nome carrega metodologia, domínio, técnica, autor ou
  versão. `revisor` falha; `revisor-anticliche-hootly` passa.
- **L2 — Atomicidade de responsabilidade.** Um agente, uma capacidade. Um orquestrador,
  um pipeline. Uma skill, um domínio de conhecimento. Sobreposição é reprovação.
- **L3 — Contratos por tipo, nunca por caminho.** O contrato de um agente declara tipos
  genéricos ("capítulo em Markdown", "relatório de pesquisa") — jamais caminhos. Caminhos
  são injetados pelo orquestrador via `$VAR`.
- **L4 — Orquestrador injeta, agente executa.** O orquestrador conhece o workspace e
  calcula as variáveis. O agente conhece sua capacidade, não onde os arquivos estão.
  Caminho hardcoded em agente é falha crítica.
- **L5 — Sinalizadores vivem NO ARQUIVO, validados por SCRIPT — nunca inline.** Todo
  output de agente é GRAVADO em disco (Write) delimitado por `[INICIO_X]`/`[FIM_X]` (ou
  pelas âncoras de seção do documento). O agente NÃO ecoa o documento na resposta:
  responde UMA linha de status ("etapa OK | <arquivo>"). Quem confere os marcadores é um
  gate determinístico (`verificar_<sistema>.py`) que lê o arquivo com acentos/caixa
  normalizados — não o orquestrador lendo texto. A ausência de sinalizador dispara retry
  com sufixo de correção, detectada pelo exit-code do gate.
- **L6 — TodoWrite é exclusivo do orquestrador.** Subagentes nunca usam TodoWrite (causa
  corrida de estado e viola a separação de responsabilidades).
- **L7 — Subagentes não disparam subagentes.** A ferramenta Task é exclusiva do
  orquestrador. Executores não criam sub-hierarquias.
- **L8 — Circuit breaker de 2 tentativas.** Se uma etapa falha duas vezes, para-se e
  informa-se o usuário. Nunca loop infinito.
- **L9 — Mínimo privilégio de ferramentas.** Cada agente recebe só as ferramentas que sua
  tarefa exige. Conceder ferramentas inúteis é defeito. (Write é legítimo — e esperado —
  para o agente que grava o próprio output.)
- **L10 — Sem fabricação.** Agentes nunca inventam dados, fontes ou informação ausente.
  Quando falta, usam `[VERIFICAR: afirmação]` ou `[LACUNA: descrição]` e continuam.
- **L11 — Português brasileiro com acentuação completa.** Todo conteúdo em português usa
  acentos corretos. Código e nomes de variáveis em inglês.
- **L12 — Description com CSO.** A `description` de qualquer artefato descreve GATILHOS de
  uso ("Use when…"), não o workflow interno.
- **L13 — Retomada por varredura.** Antes de despachar qualquer etapa, o gate diz o que
  já está válido; etapa cujo artefato passa no gate NÃO roda de novo. A linha `PENDENTES`
  é o plano de execução — primeira rodada e retomada pós-falha são a MESMA operação.
  Falha na etapa N não repaga as etapas 1..N-1 (retrabalho em opus é o desperdício mais
  caro). Todo orquestrador nasce retomável.
- **L14 — Validação por script, não por leitura.** O orquestrador NUNCA lê o documento
  para validar — roda `verificar_<sistema>.py --etapa <nome>` e confia no exit-code
  (0 = válida). Read do conteúdo é exceção rara de diagnóstico de falha persistente,
  jamais rotina. Merge puro (concatenação) e handoff (passar um resultado adiante) também
  são deterministas: um script concatena/valida, ou o handoff é uma linha via `grep` —
  o conteúdo não transita pelo contexto do orquestrador.

> **Andaimes proibidos (era 200k, mortos):** "um processo por vez"/`/clear` entre
> processos (pipelines de processos distintos são independentes e podem rodar em
> paralelo), "leia em blocos"/chunking defensivo, "NUNCA truncar", tetos de 10–30
> resultados por busca, e devolver o documento inteiro inline entre sinalizadores.

---

## Template canônico — ORQUESTRADOR (SKILL.md de entrada)

O orquestrador é o único artefato que usa TodoWrite, Task e Bash e que conhece o
workspace. Pode ser uma skill (`.claude/skills/<nome>/SKILL.md`) ou um command
(`.claude/commands/<nome>.md`). O Padrão Soberano prefere SKILL.md (auto-trigger).

Todo pipeline gerado nasce com um **gate por script**: um `verificar_<sistema>.py` de
poucas linhas que importa o motor `scripts/verificar_pipeline.py` e declara só a tabela
de etapas (âncoras). É o gate que faz a retomada (varredura → PENDENTES), a validação
(`--etapa`) e o portão final (`--gate`).

```markdown
---
name: [nome-pipeline-dominio]
description: >
  Use when [GATILHO 1], [GATILHO 2], or [GATILHO 3].
  Keywords: [termo1], [termo2], [sinônimo].
argument-hint: <argumento-obrigatorio> [--opcao]
allowed-tools: Read Write Task Bash TodoWrite
---

# [Nome do Pipeline]

> Pipeline v3.0: [o que transforma em quê, numa linha]. Retomável, validado por script.

<identidade>
  <papel>Orquestrador — coordenador, não executor. Delega, valida por script e retoma.</papel>
  <estilo>Metódico, sequencial, validador rigoroso. Nada de conteúdo pesado no próprio
  contexto. Para antes de propagar erro.</estilo>
</identidade>

<proposito>
  <objetivo>Transformar [ENTRADA] em [SAÍDA FINAL] em [N] etapas controladas, retomáveis
  e validadas por script.</objetivo>
  <resultado_final>[Descrição do artefato final e onde fica].</resultado_final>
</proposito>

<variaveis>
  | Variável   | Origem    | Descrição                          |
  |------------|-----------|------------------------------------|
  | $ARGUMENTS | Usuário   | [argumento principal]              |
  | $WORKSPACE | Calculada | [padrão de caminho do workspace]   |
  | $SLUG      | Calculada | [identificador p/ nomes de arquivo]|
</variaveis>

<capacidades>
  <tools_orquestrador>
    | Tool     | Função                                              | Quando usar          |
    |----------|-----------------------------------------------------|----------------------|
    | Bash     | Gate/retomada (verificar_<sistema>.py), merge, test -f | Etapa 0, validações |
    | Task     | Disparar subagentes                                 | Etapas com agente    |
    | TodoWrite| Rastrear progresso                                  | Início e transições  |
    | Read     | EXCEÇÃO rara: diagnosticar falha persistente        | Nunca para validar   |
  </tools_orquestrador>
  <regras_uso>
    - RETOMADA (L13): a varredura da Etapa 0 lista PENDENTES; só as pendentes rodam.
    - CONDUZIR POR CAMINHO: o orquestrador passa paths; o subagente lê a entrada e GRAVA
      o documento. O documento nunca volta inline (L5).
    - VALIDAÇÃO POR SCRIPT (L14): sempre `verificar_<sistema>.py --etapa`, nunca lendo.
    - Subagentes LEEM o próprio prompt via Read (Passo 1); o orquestrador não copia a
      capacidade deles.
    - Etapas de UM pipeline são sequenciais entre si; pipelines de PROCESSOS distintos
      são independentes e podem rodar em paralelo (não existe "um por vez" entre processos).
  </regras_uso>
</capacidades>

<contratos_dados>
  | # | Etapa       | Agente/Script       | Entrada            | Saída               | Validação               |
  |---|-------------|---------------------|--------------------|---------------------|-------------------------|
  | 0 | Preparação  | —                   | $ARGUMENTS         | $WORKSPACE + PENDENTES | gate varredura (o plano) |
  | 1 | [Nome]      | agents/<slug>.md    | $WORKSPACE/[input] | $WORKSPACE/[output] | verificar --etapa <n> → 0 |
  | M | Merge       | — (script)          | [saídas parciais]  | [artefato unificado]| merge_<sistema>.py → 0  |
  | N | Finalização | —                   | tudo               | resumo ao usuário   | verificar --gate → 0    |

  As âncoras de início/fim/seções de cada etapa vivem CODIFICADAS no verificar_<sistema>.py
  (fonte única) — este arquivo não as duplica.
</contratos_dados>

<restricoes>
  <orquestrador>
    - NUNCA ler os documentos gerados para validar — validação é do script (L14)
    - NUNCA redespachar etapa que o gate deu como válida (o trabalho já foi pago — L13)
    - NUNCA prosseguir com etapa cuja anterior está pendente/inválida
    - NUNCA embutir a lógica do agente no prompt — o agente lê o próprio arquivo (L4)
    - NUNCA tentar a mesma etapa mais de 2x — parar e reportar o output do gate (L8)
    - SEMPRE substituir $WORKSPACE pelo valor real antes de despachar
  </orquestrador>
  <subagentes>
    - NUNCA imprimir o documento na resposta — o documento vai no ARQUIVO (L5)
    - NUNCA usar TodoWrite (L6); NUNCA disparar Task (L7)
    - NUNCA assumir caminhos — recebê-los do orquestrador (L4)
    - NUNCA inventar dados — usar [VERIFICAR]/[LACUNA] (L10)
  </subagentes>
</restricoes>

<contingencias>
  <etapa_invalida>Gate acusa [AUSENTE]/[INVALIDA] após o despacho → redespachar a MESMA
  etapa com o motivo do gate anexado ao prompt (máx 2 tentativas; depois PARAR e reportar).</etapa_invalida>
  <falha_de_entrada>merge/handoff acusa entrada inválida → o defeito é da etapa anterior;
  voltar à etapa apontada, não ao merge.</falha_de_entrada>
</contingencias>

<sufixos_correcao>
  <sufixo_gate>[FALHA NO GATE. O documento gravado não passou em verificar_<sistema>.py
  --etapa <n>: <motivo do gate>. Corrija o arquivo (abra com o marcador de início, feche
  com o de fim, inclua as seções obrigatórias, use acentos) e regrave.]</sufixo_gate>
  <sufixo_eco>[FALHA DE CONTRATO. Você imprimiu o documento na resposta. GRAVE-o com Write
  no caminho indicado e responda APENAS uma linha de status; não ecoe o conteúdo.]</sufixo_eco>
</sufixos_correcao>

## Etapa 0 — Preparação, gate e retomada
1. Validar $ARGUMENTS (parar se vazio/inválido). Calcular $WORKSPACE e $SLUG.
2. `Bash: test -f "$WORKSPACE/<entrada>"` — se faltar a entrada do pipeline, PARAR.
3. `Bash: python scripts/verificar_<sistema>.py "$WORKSPACE"` → a linha `PENDENTES: ...`
   é o plano. Tudo "(nenhuma)" → pular direto à Finalização (já estava completo).
4. TodoWrite com todas as etapas — as já válidas nascem `completed`.

## Etapa N — [Nome]
**Agente:** `.claude/agents/[categoria]/[nome-agente].md`
- **Retomada:** se "<slug-etapa>" NÃO está em PENDENTES → pular (não despachar).
- Despachar Task com o prompt-invólucro (cabeçalho ═══ + passos numerados), $WORKSPACE
  já substituído: Passo 1 = `Read: .claude/agents/[categoria]/[nome-agente].md`; ler as
  entradas por caminho; GRAVAR (Write) o documento completo em $WORKSPACE/<saida>;
  responder APENAS "<slug-etapa> OK | <arquivo>" — NÃO imprimir o documento.
- Validar: `Bash: python scripts/verificar_<sistema>.py "$WORKSPACE" --etapa <slug-etapa>`
  (exit 1 → contingência etapa_invalida). Transição ou PARAR.

## Etapa M — Merge (script, sem LLM) — quando aplicável
`Bash: python scripts/merge_<sistema>.py "$WORKSPACE"` concatena/valida sem passar o
conteúdo pelo contexto. Re-roda se uma entrada foi regenerada nesta execução.

## Finalização
`Bash: python scripts/verificar_<sistema>.py "$WORKSPACE" --gate` (exit 1 → algo regrediu,
reportar e PARAR). Exibir o resumo, marcando o que foi REAPROVEITADO vs gerado agora.
```

Seções **obrigatórias** do orquestrador: `<identidade>`, `<proposito>`, `<variaveis>`,
`<capacidades>`, `<contratos_dados>`, `<restricoes>`, `<contingencias>`,
`<sufixos_correcao>`, Etapa 0 (com gate/varredura + TodoWrite), etapas com cláusula de
retomada e gate `--etapa`, Finalização com `--gate`. Opcionais: `<resumo_arquitetura>`
(diagrama ASCII), `<agents_utilizados>`.

### O gate do pipeline (obrigatório)

Todo pipeline gerado acompanha `scripts/verificar_<sistema>.py`:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verificar_pipeline import rodar_cli   # motor genérico (scripts/verificar_pipeline.py)

ETAPAS = {
    # etapa: (sufixo_do_arquivo, inicio, fim, contem[], minimo_chars)
    "<slug-etapa-1>": ("-<slug1>.md", "<âncora de início>", "<âncora de fim>",
                       ["<seção obrigatória>"], 500),
    # `fim` pode ser tupla p/ fim alternativo: ("juiz federal", "juíza federal", ...)
}

if __name__ == "__main__":
    rodar_cli(ETAPAS, titulo="<nome-sistema>")
```

**Calibragem das âncoras (crítico):** as âncoras de `ETAPAS` DEVEM casar com os
`<sinalizadores>` reais dos agentes que geram cada arquivo. Havendo artefato real em
`data/`, confira `head`/`tail` dele e ajuste antes de fixar. O motor normaliza
acento/caixa dos dois lados, então escreva as âncoras com acentos naturais.

---

## Template canônico — AGENTE

Síntese do XML-semântico rico (SuperLivro) com o frontmatter de triggering (Anthropic).
As tags v2 são o esqueleto obrigatório; extensões de domínio entram como tags nomeadas
adicionais (ex.: `<hierarquia_de_autoridade>`, `<ecos>`), nunca substituindo as v2.

O contrato do agente **não muda na v3.0**. O que a v3.0 explicita é onde o output vive:
o agente que grava o próprio artefato (o caso normal) tem `Write`, GRAVA o documento
completo no caminho que o orquestrador injeta e responde uma linha de status. Os
`<sinalizadores>` são as âncoras que o gate do pipeline confere NO ARQUIVO — não um
texto para emoldurar uma resposta de chat.

```markdown
---
name: [nome-capacidade-dominio]
description: >
  [Capacidade numa linha — o QUE sabe fazer, não em qual pipeline opera]
  # <example> opcional (recomendado p/ agentes ativáveis diretamente pelo usuário)
tools: Read Write [apenas as necessárias — Write se grava o próprio output]
model: [haiku|sonnet|opus]
color: [yellow|green|red|blue]
---

<identidade>
  <papel>[Papel específico, não genérico]</papel>
  <estilo>[Como executa — metódico, cirúrgico, criativo…]</estilo>
</identidade>

<capacidade>
  <habilidade>[Verbo no infinitivo + objeto específico]</habilidade>
  <especializacao>[Domínio concreto de expertise]</especializacao>
</capacidade>

<contrato>
  <entrada>
    <tipo>[Tipo genérico — não caminho]</tipo>
    <requisitos_obrigatorios>- [o que a entrada DEVE conter]</requisitos_obrigatorios>
  </entrada>
  <saida>
    <tipo>[Tipo do output]</tipo>
    <destino>Gravado em arquivo (Write) no caminho injetado pelo orquestrador; a resposta
    ao orquestrador é UMA linha de status, nunca o documento.</destino>
    <caracteristicas>- [propriedade do output]</caracteristicas>
  </saida>
</contrato>

<restricoes>
  <proibicoes>
    - NÃO assumir caminhos — receber do orquestrador
    - NÃO imprimir o documento na resposta — ele vai no ARQUIVO (L5)
    - NUNCA inventar dados ausentes — usar [VERIFICAR]/[LACUNA]
    - NÃO usar TodoWrite
    - [proibições do domínio]
  </proibicoes>
  <obrigacoes>
    - SEMPRE português com acentos
    - SEMPRE gravar o documento com [INICIO_X] e [FIM_X] (âncoras que o gate confere)
    - SEMPRE responder só a linha de status ("<etapa> OK | <arquivo>")
    - [obrigações do domínio]
  </obrigacoes>
</restricoes>

<contingencias>
  <se_entrada_insuficiente>[Ação — não parar em silêncio]</se_entrada_insuficiente>
  <se_ambiguo>[Qual interpretação adotar]</se_ambiguo>
  <se_informacao_ausente>[Usar [VERIFICAR: x] e continuar]</se_informacao_ausente>
</contingencias>

<instrucoes>
  <passo numero="1" nome="Absorver contexto">[Ler entrada por caminho, internalizar]</passo>
  <passo numero="2" nome="Planejar">[O que planejar antes de produzir]</passo>
  <passo numero="3" nome="Gravar o documento">[Produzir e Write no caminho injetado, com
  marcadores de início/fim]</passo>
  <passo numero="4" nome="Responder status">[Autovalidar marcadores/acentos e responder
  UMA linha: "<etapa> OK | <arquivo>"]</passo>
</instrucoes>

<formato_saida>
  <!-- O template abaixo descreve o DOCUMENTO GRAVADO em arquivo, não a resposta. -->
  <arquivo>
[INICIO_[NOME]]
[Conteúdo produzido]
[FIM_[NOME]]
  </arquivo>
  <resposta_ao_orquestrador>[NOME] OK | [caminho-do-arquivo]</resposta_ao_orquestrador>
</formato_saida>

<sinalizadores>
  | Posição | Texto             | Uso                                              |
  |---------|-------------------|--------------------------------------------------|
  | Início  | `[INICIO_[NOME]]` | Abre o documento NO ARQUIVO (âncora do gate)     |
  | Fim     | `[FIM_[NOME]]`    | Fecha o documento NO ARQUIVO (âncora do gate)    |
  | Alerta  | `[VERIFICAR: x]`  | Afirmação não verificável                         |
  | Lacuna  | `[LACUNA: x]`     | Informação ausente na entrada                     |
</sinalizadores>

<metadados_workflow>
  <posicao>[Onde se situa no pipeline]</posicao>
  <predecessores>[Quem produz a entrada]</predecessores>
  <sucessores>[Quem consome a saída]</sucessores>
</metadados_workflow>
```

Seções **obrigatórias**: `<identidade>`, `<capacidade>`, `<contrato>`, `<restricoes>`,
`<contingencias>`, `<instrucoes>`, `<formato_saida>`, `<sinalizadores>`.
**Recomendadas**: `<metadados_workflow>`, `<exemplos>`. **Opcionais de domínio**: qualquer
tag nomeada relevante, após as obrigatórias.

> **Nota v3.0:** a disciplina de "gravar + responder 1 linha" é reforçada pelo
> orquestrador no prompt-invólucro de cada etapa; o agente coopera trazendo o
> `<destino>` no contrato e a `<resposta_ao_orquestrador>` no formato de saída. Um agente
> que apenas retorna texto (não grava) recebe só `Read` — mas o caso normal (grava_saida)
> é gravar e ter `Write`.

### Regra de modelo
| Tarefa | Modelo |
|--------|--------|
| Escrita longa, análise profunda, voz autoral | `opus` |
| Pesquisa, estruturação, revisão técnica | `sonnet` |
| Formatação, validação, operações simples | `haiku` |

### Regra de cor (semântica)
| Cor | Semântica | Exemplos |
|-----|-----------|----------|
| `yellow` | Exploração/investigação | pesquisador, estruturador |
| `green` | Construção/criação | escritor, curador |
| `red` | Revisão crítica/adversarial | revisor, cético |
| `blue` | Propósito geral | (neutro) |

---

## Template canônico — SKILL DE CONHECIMENTO

Skills ensinam metodologia; não escrevem arquivos. Padrão Anthropic com vocabulário XML.

```markdown
---
name: [nome-metodologia-dominio]
description: >
  Use when [GATILHO 1], [GATILHO 2], or [GATILHO 3].
  Keywords: [termo1], [termo2].
# context: fork   ← apenas se a skill executa scripts com output verboso
---

<identidade>
  <papel>[Metodologia/expertise que a skill representa]</papel>
  <dominio>[Área de conhecimento]</dominio>
</identidade>

<proposito>
  <objetivo>[O que a skill permite fazer]</objetivo>
  <razao>[Que problema resolve]</razao>
</proposito>

<quando_usar>
  <gatilhos>- [cenário 1]; - [cenário 2]; - keywords: [termos]</gatilhos>
  <exclusoes>- NÃO usar quando [situação inadequada]</exclusoes>
</quando_usar>

<instrucoes>
  <passo numero="1" nome="[Nome]">[Imperativo]. CRITÉRIO DE PARADA: [condição].</passo>
</instrucoes>

<restricoes>
  <nunca>- [proibido]</nunca>
  <sempre>- [obrigatório]</sempre>
  <!-- skills de DISCIPLINA acrescentam: -->
  <red_flags>Se você pensa "[racionalização]" — PARE. A skill existe para este momento.</red_flags>
</restricoes>

<referencias>- references/[arquivo].md — [o que contém]</referencias>
```

Tamanho: SKILL.md abaixo de 500 linhas (abaixo de 100 se `context: fork`). Conhecimento
extenso vai para `references/`; scripts para `scripts/`.

**Tipos de skill** (afetam o teste automático — ver `validador-de-artefato.md`):
Disciplina (impõe regra com custo → exige RED/GREEN), Técnica (método com passos),
Padrão (modelo mental), Referência (documentação → dispensa RED/GREEN).

### Skills que embarcam scripts (v3.0)

Quando uma skill traz `scripts/`, ela segue o mesmo espírito determinístico do pipeline:

- **`context: fork`** para isolar o output verboso do contexto principal (SKILL.md < 100
  linhas, comandos literais, "REGRA ABSOLUTA: NÃO crie código novo", documentação rica em
  `references/`).
- **Output mínimo `[INICIO]/[OK]/[ERRO]/[FIM]`** — uma linha por item processado; detalhe
  vai para arquivo de log, não para stdout.
- Se a skill é, na prática, um **mini-pipeline de 3+ etapas** com dependências (ideia →
  spec → artefato → validação), aplica-se o padrão do orquestrador: subagentes internos
  gravam em disco, o SKILL.md valida por `Bash: test -f`/`grep` (regra **zero-read**,
  nunca Read para checar existência) e há retomada por varredura. Ver
  `.claude/spec/referencias/design-skill-agentica-robusta.md`.

---

## Resolução de conflitos entre convenções

| Conflito | Decisão soberana |
|----------|------------------|
| `<persona>/<objetivo>` (P.O.E.M.A. v1) vs `<identidade>/<capacidade>` (v2) | **v2 é o padrão**; tags v1 são obsoletas |
| Description narrativa vs CSO "Use when…" | **CSO obrigatório** (L12) |
| Self-bootstrap vs "Passo 1: Read agent.md" | Ambos; o Padrão usa **"Passo 1: Read"** (recarrega o estado mesmo em subagente isolado) |
| Documento inline entre sinalizadores vs gravar + responder 1 linha | **Gravar em disco + 1 linha** (L5); o gate confere o arquivo |
| Validação por leitura do orquestrador vs gate por script | **Gate por script** (L14); Read é exceção de diagnóstico |
| Pipeline sem retomada vs retomável | **Retomável** (L13); PENDENTES é o plano |
| "Um processo por vez"/`/clear`/"leia em blocos" | **Mortos** — paralelismo entre processos, janelas grandes, sem chunking defensivo |
| TodoWrite em subagente | **Proibido** (L6) |
| `<example>` na description | Recomendado p/ agentes globais; opcional p/ agentes de pipeline |
| Tamanho de prompt inline no orquestrador | Até **~50 linhas E estruturado** (cabeçalho + passos + restrições) |
| Extensões ricas (`<hierarquia_de_autoridade>` etc.) | Permitidas **após** as seções obrigatórias |
