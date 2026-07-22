# `/criar-feature` — Design (blueprint para a `/criar-sistema`)

> Escrito em 22/07/2026. Base: conversa exploratória do product owner (juiz federal de 1º
> grau, autor do catálogo) + a sessão que construiu o MCP local do STF ponta a ponta +
> consumo da skill `criar-mcp-cloudflare` (gabinete). É a spec do `/criar-feature` e o
> blueprint que a `/criar-sistema` vai consumir. **Antes de gerar, rodar `iniciar_superjurista`
> e `carregar_pipeline` (sem argumentos) para reconferir o inventário real** — os números do
> catálogo foram lidos em jul/2026 e podem ter mudado.

---

## 1. Problema

O SuperJurista é um **sistema epistêmico**, não um projeto de software: o produto é a
**integridade do conhecimento jurídico** que ele produz (verbatim, procedência, honestidade),
não o código. Por isso `feature-dev` não serve — os *gates* de criação não são "o código
compila / tem teste", são **epistêmicos**.

A dor concreta do PO: *"não temos uma ferramenta que acopla automaticamente o mcp no plugin
integrado ao Cloudflare"*. O gargalo não é falta de documentação (os docs de estado e visão
são bons) — é que **a costura é conhecimento tribal**: cada recurso novo re-fia as mesmas
junções à mão. A sessão do STF provou: colocar UMA base no ar tocou ~15–20 pontos em 4+
lugares (worker → ci.yml → deploy.yml → gateway [5 arquivos] → .mcp.json → plugin → catálogo
→ CLAUDE.md → memória), cada um decorado de cabeça. A regra existe nos docs; falta um **motor**
que a execute.

## 2. O que é o `/criar-feature`

Uma **porta-mestra governada**, no plugin `superjurista-dev`, por cima da família de criadores
que **já existe** (`criar-mcp-precedente`, `criar-mcp-doutrina`, `criar-skill`,
`criar-pje-download`, `criar-team`, `adicionar-pipeline`, `criar-vertical`). Ela **consome, não
copia**. Faz três coisas que nenhum criador-irmão faz sozinho:

1. **Classifica** o recurso e declara o nascimento (casa única · quem consome · papel frente
   aos vizinhos).
2. **Roteia** para o criador-irmão certo.
3. **Impõe o contrato epistêmico como gate + executa a costura inteira + reconcilia** catálogo,
   CLAUDE.md e memória.

É a filosofia **"F0 primeiro — o mecanismo"** que o roadmap do produto já prega (skill
`criar-vertical` antes das verticais), generalizada de um tipo para **todos** os tipos de
recurso.

## 3. Princípios (herdados, não inventados)

- **Consumir, nunca copiar** — o `/criar-feature` orquestra os criadores existentes.
- **Dado, não ferramenta** — recurso novo é dado (pronto, dialeto, receita), quase nunca uma
  ferramenta nova no conector.
- **Regra de nascimento** — todo artefato declara ao nascer: fonte de verdade · onde se
  registra · papel frente aos vizinhos · linha no README/CLAUDE.md do lar (a `criar-mcp-cloudflare`
  já traz isso; aqui vira gate universal).
- **O piloto define a ordem** — não construir a matriz inteira antes de 10 usuários reais.

## 4. Taxonomia de recursos (o que ela governa)

| Tipo | Criador-irmão consumido | Casa (lar) | Costuras-chave |
|------|-------------------------|------------|----------------|
| **base/MCP** | `criar-mcp-cloudflare` (migrar+atualizar) / `criar-mcp-precedente` | edge: `origens/` · local-híbrido: `.claude/mcp-servers/` + plugin · pessoal | ci.yml, deploy.yml, gateway (federação), plugin `.mcp.json`, Cowork config, catálogo, dependencias.md |
| **pronto** | curadoria `conteudo/prontos/` + `regenerar-conteudo` | produto | banco.gen.ts, versão/dono/data |
| **pipeline** | `adicionar-pipeline` | produto (fábrica) | manifesto, gates, âncoras congeladas |
| **método** | banco | produto | banco.gen.ts |
| **disciplina** | (F1: `conteudo/disciplinas/`) | produto | `carregar_disciplina`, 4 consumos |
| **standard/verbete** | `criar-vertical` + `curar-verbete` | produto (por área) | lastro verbatim, janela temporal |
| **vertical** | `criar-vertical` | produto | kit §3 (bases → standards → pipelines → prontos) |
| **perfil** | constituição no bootstrap | produto | catálogo filtrado por perfil |

**v1 implementa só o tipo `base/MCP`** (as três casas); os demais entram um a um.

## 5. O contrato epistêmico (os gates comuns)

Cada recurso, antes do commit atômico, passa por estes gates (o validador é adversarial):

| Gate | O que exige | Como se verifica |
|------|-------------|------------------|
| **Verbatim** | nunca citar de memória; citação = cópia exata de fonte citável | a saída expõe campo `fonte`/`verbatim`; sem fonte → marcada "não verificada" |
| **Procedência** | fonte + confiabilidade (oficial × registro de acervo × defasado) + data de cobertura | bloco de citação carrega `PROCEDÊNCIA`; bases de confiabilidade diferente não saem vestidas igual |
| **Lastro** | verbete/standard sem fonte não entra (Lei do Lastro) | gate bloqueia standard sem verbatim + data |
| **Dado, não ferramenta** | recurso não incha o manifesto do conector | conta ferramentas expostas; recurso vira dado consultável |
| **Consumir, não copiar** | capacidade transversal vive uma vez | busca duplicata antes de gerar |
| **Versão + dono + data** | todo pronto/pipeline versionado e com dono | rejeita artefato sem esses campos (o 150º pronto citando artigo revogado custa mais que os 149 constroem) |
| **Degradação honesta** | `indisponível` ≠ `inexistente` | falha de base tem mensagem própria; `total=0` nunca vira "não existe" |
| **Parcial-mas-honesto** | argumenta pelo polo, jamais inventa fato/julgado nem omite o desfavorável | vale em todo papel e regime |
| **Regra de nascimento** | 4 declarações (fonte de verdade · registro · papel · linha no CLAUDE.md) | ausência = artefato invisível ou duplicado |

## 6. As três casas do tipo base/MCP (o que atualiza a `criar-mcp-cloudflare`)

A `criar-mcp-cloudflare` hoje só conhece **edge** e **pessoal**. Esta sessão descobriu a
terceira, obrigatória:

1. **Edge Worker** (padrão): TS Worker em `origens/`, single-tenant, deploy agêntico, service
   binding no gateway. Para fontes com **API pública alcançável do datacenter**.
2. **Local-híbrido (NOVO):** corpo local (Python + Playwright + **Chrome real**, IP
   **residencial**) + cérebro no gateway. **Para fontes que bloqueiam IP de datacenter** —
   provado com o STF (do edge: HTTP 526/connection reset; do IP residencial: 200; e o WAF
   rejeita headless-shell com 403, só passa o Chrome real). Provável TSE/TREs também.
3. **Pessoal/legado:** ferramenta do gabinete fora do produto.

**Decisão de casa** (Passo 0 do `/criar-feature` para base/MCP): *onde o dado mora* **e** *a
fonte bloqueia datacenter?* — e o teste do desenvolvedor (IP residencial) **engana**, porque
passa onde o edge falha. **Testar o bloqueio de IP antes de escolher a casa.**

## 7. O contrato do híbrido: `carregar_config` (corpo local ↔ cérebro Cloudflare)

Separa **plano de dados** (local, obrigatório) de **plano de controle** (gateway):

- O corpo local, ao subir e periodicamente, chama `carregar_config(convite)` no gateway →
  recebe `{ autorizado, config, disabled, versao }`, onde `config` é a **receita viva**
  (campos ES / seletores / mapa de bases / parâmetros do WAF).
- O corpo **reporta telemetria** (contagem + status HTTP; **NUNCA a consulta nem os autos** —
  privacidade: só o veredito/contagem cruza a rede).
- **Falha do gateway:** fail-open com cache + TTL (resiliência), mas `disabled` é kill-switch.
- **Enforcement honesto:** como o código roda na máquina do usuário, é **dissuasor +
  dependência de receita viva** (o STF drifta; sem gateway a cópia apodrece), não trava
  criptográfica — proporcional ao público (assinantes, não crackers).
- **Convite:** herdado do conector remoto que o plugin já autentica (não env var — env var com
  credencial é banida). *Viabilidade técnica a confirmar (pergunta aberta).*
- **Bônus:** o mesmo canal que licencia é o que **atualiza os seletores** quando um tribunal
  redesenha o portal, e alimenta o subsistema de **debugging agêntico dos MCPs**. Controle,
  atualização e debug viram uma engrenagem só.

## 8. Mapa de costuras

As costuras do PO (S1–S10 do doc de síntese: entrada→pronto, pronto↔pipeline↔método, gate→
decisão, política de busca, busca→bloco de citação, conector↔plugin, licenciamento↔ruleset,
atualização servidor→cliente, método×papel×matéria, falha de base→resposta) **são o esqueleto
do gate e da reconciliação**. Para o tipo base/MCP, a costura concreta a executar/reconciliar:

`ci.yml` (matrix) · `deploy.yml` (target + bundle) · gateway (`tipos.ts`, `origens.ts`,
`consulta.ts`, `parsear.ts`, `ferramentas.ts`, `wrangler.jsonc`) · plugin `.mcp.json`
(`${CLAUDE_PLUGIN_ROOT}`, stdio) · Cowork config · `catalogo-do-ecossistema.md` · tabela
`origens/` do CLAUDE.md · `dependencias.md` · memória. **Reconciliar é obrigatório** (regra
inviolável §6 do produto: deploy só termina reconciliando o catálogo).

## 9. Fluxo do orquestrador `/criar-feature`

1. **Classificar** o recurso (detectar/perguntar o tipo).
2. **Declarar nascimento** (as 4 declarações da regra de nascimento).
3. **Escolher casa** — para base/MCP: edge × local-híbrido × pessoal, com **teste de bloqueio
   de IP** decidindo edge vs local.
4. **Rotear** ao criador-irmão e gerar via ele (staging).
5. **Gate epistêmico** (validador adversarial contra os gates da §5).
6. **Executar a costura** (fiar em todas as casas da §8).
7. **Reconciliar** catálogo/CLAUDE.md/memória.
8. **Verificar** por `tools/call` real (nunca só `tools/list`); degradação honesta se a base
   falhar.

## 10. v1 e o que fica de fora

- **v1:** só o tipo **base/MCP**, com as **três casas**, e o **primeiro output real sendo o STF
   híbrido** (a máquina nasce resolvendo o caso que a motivou). Inclui **migrar+atualizar a
   `criar-mcp-cloudflare`** do gabinete para o plugin `superjurista-dev`, com a terceira casa.
- **Fora de v1** (entram depois, um a um): os demais tipos de recurso; o compilador
   `método × papel × matéria` (§3.5 do doc do PO); as *features de produto* (contrato de
   execução, bloco de citação com PROCEDÊNCIA, consolidação da superfície de busca) — essas são
   **outputs** que o `/criar-feature` ajuda a produzir, não partes dele.

## 11. Arquitetura de implementação (para a `/criar-sistema`)

Padrão Soberano; staging + commit atômico; validação adversarial. Alvo:
`--target=C:\Users\georg\superjurista-dev` (o plugin dos criadores).

- **Orquestrador:** command `/criar-feature` (em `commands/`), orquestrador-cego que injeta a
  missão nos agentes.
- **Agentes:** `classificador-de-recurso` (tipo + casa) · `roteador-base-mcp` (Passo 0 + teste
  de bloqueio de IP + despacho ao criador certo) · `validador-epistemico` (os gates da §5,
  adversarial) · `costurador-reconciliador` (executa e reconcilia a §8).
- **Skills (conhecimento):** `contrato-epistemico` (os gates) · `mapa-de-costuras` (as junções
  por tipo) · `criar-mcp-cloudflare` **migrada e atualizada** com a 3ª casa e o contrato
  `carregar_config`.

## 12. Perguntas em aberto (a resolver antes/durante o build)

Do PO (§6 do doc de síntese):
1. Gargalo é o usuário **não saber o que vai acontecer** (resolve no contrato de execução) ou
   **não saber o que pedir** (repensar a porta de entrada)?
2. Lista **exata dos métodos nomeados por autor** (maior risco não auditado).
3. MCPs STF/TSE/TRE extraem **jurisprudência** (rota oficial, scraper substituível) ou
   **consulta processual autenticada** (navegador insubstituível)?
4. Público: **magistrados** ou **mercado jurídico inteiro**?
5. Quantos tokens o manifesto do conector ocupa numa sessão limpa?

Novas (de governança e do híbrido):
6. A família `criar-*` migra **toda** para o plugin `superjurista-dev` (regra "2+ projetos →
   plugin"), ou fica repartida gabinete×plugin?
7. `carregar_config` vive no **conector** (`mcp.superjurista.com`) ou no **gateway**?
8. Como o corpo local **obtém o convite** sem env var (herdar do conector — confirmar
   viabilidade técnica no Cowork).

## 13. Build

`/criar-sistema` alimentada por esta spec como intenção/blueprint, com `--revisar` (o PO revê o
staging antes do commit atômico) e `--target` no `superjurista-dev`.
