# Lições de Campo — MCPs reais criados com esta skill

Registro das técnicas que os MCPs reais exigiram além do template base. Fontes:
`tcu-jurisprudencia` (02/2026), `tjsc-eproc` (03/2026), `hudoc-echr` (07/2026), o caso
TSE/SJUR (07/2026, resolvido como skill Chrome MCP, não como MCP server) e os MCPs
trabalhistas `pesquisa-tst` + `pesquisa-jt` (Falcão nacional/CSJT) — 21/07/2026,
construídos direto como Worker TS em `superjurista-produto/origens/`.

---

## 1. Registro: `.mcp.json`, nunca settings.json

O que ativa o MCP no Claude Code é o `.mcp.json` na **raiz do projeto**, com caminho
ABSOLUTO do `server.py`. Config de MCP dentro de `settings.json` é padrão antigo e falha
silenciosamente (o servidor simplesmente não aparece na sessão).

```json
{
  "mcpServers": {
    "tjsc-eproc": {
      "command": "python",
      "args": ["C:\\Users\\usuario\\projeto\\.claude\\mcp-servers\\tjsc-eproc\\server.py"]
    }
  }
}
```

O arquivo do servidor pode viver em qualquer lugar (`.claude/mcp-servers/` do projeto,
`~/.claude/mcp-servers/` global, pasta própria) — o registro é que decide o escopo.
Servidor novo só carrega em **sessão nova**.

## 2. Busca implementada UMA vez (`_fazer_busca`)

O template antigo convidava a duplicar o código de busca entre `buscar_*` e
`gerar_relatorio_*` ("mesmo código de buscar_*"). Os três MCPs reais convergiram para
uma função compartilhada que retorna `(resultados, total)`:

```python
async def _fazer_busca(busca: str, max_resultados: int = 30, ...filtros) -> tuple[list, int]:
    ...
    return resultados[:max_resultados], total
```

As tools só formatam: `buscar_*` → XML, `gerar_relatorio_*` → Markdown. Correção de bug
ou mudança de endpoint acontece num lugar só.

## 3. Charset legado (eProc serve iso-8859-1)

O eProc do TJSC (e sistemas antigos em geral) responde HTML em `iso-8859-1`. Sem fixar o
encoding, o httpx assume UTF-8 e os acentos viram mojibake ("Ã§Ã£o"):

```python
resp = await client.post(SEARCH_URL, headers=HEADERS, data=form_data)
resp.encoding = "iso-8859-1"   # ANTES de acessar resp.text
```

Sintoma no teste: ementas com `Ã` espalhado. Diagnóstico: olhar o header
`Content-Type` da resposta ou o `<meta charset>` do HTML.

## 4. Paginação com reaproveitamento de sessão (padrão TJSC)

Portais HTML costumam paginar por um endpoint AJAX separado que depende dos cookies da
primeira resposta:

```python
resp = await client.post(SEARCH_URL, data=form_data)          # 1ª página
cookies = dict(resp.cookies)                                   # sessão da busca
for page in range(2, pages_needed + 1):
    if len(resultados) >= max_resultados:
        break
    pag = await client.post(PAGINATE_URL, headers=AJAX_HEADERS,
                            data={"hdnPaginaAtual": str(page), ...}, cookies=cookies)
    resultados.extend(_extrair_resultados(pag.text))
```

Limitar `page_size` ao máximo do portal (tipicamente 100) e parar quando atingir
`max_resultados` — não baixar tudo.

## 5. Múltiplas bases pesquisáveis (padrão TCU)

O TCU tem três bases com schemas de resposta diferentes (acórdãos, jurisprudência
selecionada, normas). O padrão que funcionou:

- Parâmetro `base` no input com `Literal["acordao", "jurisprudencia", "norma"]`
  (Pydantic valida e o Claude enxerga as opções no schema da tool);
- Um extractor por base (`_extrair_resultados_acordao`, `..._jurisprudencia`,
  `..._norma`) + um dispatcher `_extrair_resultados(data, base)`;
- A terceira tool vira `listar_bases_[tribunal]` (descreve as bases e quando usar
  cada uma) em vez de `listar_filtros_*`.

## 6. Linguagem de query própria (padrão HUDOC)

APIs internacionais (e algumas nacionais) têm linguagem de consulta própria — o HUDOC
(CEDH) usa expressões como `contentsitename:ECHR AND (violation:"6")`. Construir a query
por funções dedicadas, nunca por concatenação solta dentro da tool:

```python
def _or_filter(field: str, values: list[str]) -> str:
    return "(" + " OR ".join(f'{field}:"{v}"' for v in values) + ")"

def _construir_query(termo, artigos=None, idiomas=None, ...) -> str:
    partes = [termo_normalizado]
    if artigos: partes.append(_or_filter("article", artigos))
    ...
    return " AND ".join(partes)
```

Também vale a lição de escopo: a skill nasceu para tribunais brasileiros, mas o mesmo
método (Network tab → endpoint JSON → template) serviu para uma corte internacional
sem nenhuma mudança estrutural.

## 7. CAPTCHA por requisição → skill Chrome MCP, não MCP server (caso TSE)

O SJUR/TSE exige um token hCaptcha invisível **de uso único por busca** — impossível de
gerar em Python. A solução que funcionou NÃO foi um MCP server, e sim uma skill
(`jurisprudencia-eleitoral`) que roda a busca dentro do navegador real via Chrome MCP:

1. Abrir/reusar aba no SPA do tribunal e esperar `window.hcaptcha` carregar (~8s);
2. Executar a busca via `javascript_tool` (o hCaptcha gera o token porque o Chrome é real);
3. Para cada nova busca: `hcaptcha.reset()` + retry (até 3x);
4. Mapear a superfície ABERTA antes de desistir: no TSE, o download do inteiro teor
   (`GET .../rest/download/pdf/{codigoDecisao}`) dispensa CAPTCHA — só a busca é protegida.

Regra de roteamento: CAPTCHA por requisição ⇒ skill Chrome MCP; superfície parcialmente
aberta ⇒ MCP híbrido possível para a parte aberta.

## 8. Higiene do diretório do servidor

- `requirements.txt` mínimo real: `mcp`, `httpx`, `pydantic` (+ `beautifulsoup4` só se
  houver parsing de HTML). Não listar dependência que o server não importa.
- Não deixar `__pycache__/`, `.pyc` nem arquivos de estudo (PDFs de manual do portal)
  dentro da pasta versionada do servidor — documentação de descoberta vai no README.

## 9. SPA que carrega o backend de um `config.json` de runtime (padrão TST/Falcão)

SPAs modernas (React/Angular) não trazem a URL do backend no bundle — leem de um
`config.json` (ou `assets/config/config.json`) no runtime. Minerar o bundle por
`config`/`.get("base_url")` e então baixar o config:

```
GET https://jurisprudencia.tst.jus.br/config.json
→ { "base_url": "https://jurisprudencia-backend2.tst.jus.br", ... }
```

O endpoint real de busca fica sob esse `base_url` (ex.: `/rest/pesquisa-textual/...`).
Bundle-mining (`grep -oE '"/[^"]+"' main.js`) revela as rotas relativas; a captura de
rede (Chrome Network tab) confirma method/body/headers.

## 10. "Fazer Login" visível ≠ auth obrigatória — procurar o namespace `no-auth`

O Falcão (CSJT) tinha botão "Fazer Login" e o mapa o dera como travado por Keycloak
(401). Mas a busca do portal roda **sem login**, sob uma API pública dedicada
`/jurisprudencia-nacional-backend/api/no-auth/{pesquisa,autocompletar,pesquisa/filtros}`.
Antes de concluir "precisa de token", capturar a rede da busca pública e olhar se há
um caminho `no-auth`/`public`/`anonimo`. O gate Keycloak costuma ser só das rotas
autenticadas (favoritos, alertas), não da consulta.

## 11. 403 de edge (CloudFront) na raiz HTML ≠ API bloqueada

`curl` de IP de datacenter pode levar 403 do CloudFront na **raiz HTML**, mas os
endpoints JSON da API respondem 200 server-side (o Worker Cloudflare também é
datacenter e funciona). Não concluir "bloqueado" por um 403 na home — testar o
**endpoint da API** diretamente com headers de navegador (UA, Accept, Referer, Origin).
Sintoma distintivo: corpo do 403 é HTML `Generated by cloudfront` (edge), não o JSON de
erro da aplicação.

## 12. Anti-abuso por endpoint → sessionId aleatório, pacing, e sondas ESPAÇADAS

O `/pesquisa` do Falcão bloqueia RAJADA com 403 `{"userMessage":"Tentativa invalida de
acesso ao sistema"}` — penalidade por janela longa, POR ENDPOINT (o `/autocompletar`
continua liberado). Duas consequências:

- **No cliente:** gerar um `sessionId` aleatório por chamada (o SPA usa algo como
  `_qdggajp`), mandar headers de navegador, e NÃO fazer retry agressivo em 403 —
  degradar com erro honesto ("aguarde e refaça"). Uso real (buscas esparsas) não dispara.
- **No recon:** a bateria diferencial de contagem (Fase 2) trava o próprio endpoint se
  disparada em rajada. Espaçar as sondas (poucas, com pausa) e aceitar que alguns motores
  não permitem varredura booleana exaustiva — documentar a sintaxe como parcial em vez de
  martelar. Validar `size`/`page` permitidos cedo (o Falcão recusa `size=2` com erro de
  negócio; 5/10/20 OK).

## 13. Contrato JSON de SPA tem armadilhas de shape (padrão TST)

Backend REST de SPA (JSON in/out) engana pelo "parece simples". No TST, o POST dava 400
mudo até acertar 3 detalhes que só a captura do body REAL revelou (não o chute):
`numeracaoUnica` é um **objeto** `{numero,digito,ano,orgao,tribunal,vara}` e não string;
campos de texto vazios vão como `null` (não `""`); campos de data são **omitidos** quando
vazios; e `tipos` não pode ser `[]`. **Regra:** capturar o body que o próprio SPA envia
(interceptar `fetch`/`XHR` no Chrome) e replicá-lo byte a byte antes de parametrizar.

## 14. Casa do artefato: `server.py` local OU Worker TS no produto

Esta skill produz por padrão um **`server.py` Python** (stdio, registrado em `.mcp.json` —
lições 1-8). Mas o produto **superjurista-produto** consome MCPs de precedente como
**Cloudflare Worker em TypeScript** (`origens/<nome>/`, MCP streamable-HTTP stateless):
`src/{index,mcp,ferramentas,<origem>,texto,tipos}.ts` + `wrangler.jsonc` + `deploy.ps1`.
Template canônico do porte: `origens/pesquisa-tnu`. As Fases 0-2 (recon, endpoints,
booleanos) são idênticas; muda só a Fase 3 (geração). Ao construir para o produto, ir
direto ao Worker TS (evita o passo Python→porte). **Deploy (pós-virada 07/2026): agêntico
via GitHub Actions** — `gh workflow run deploy.yml -f target=origens/<nome>`; o token vive
no cofre do GitHub (conta da empresa), nunca em disco (`docs/deploy-agentico.md`). **Passo
que se esquece:** registrar a pasta nova no `ci.yml` (matriz) E no `deploy.yml` (opções de
target + variável `ORIGENS`) — senão fica fora do CI e do deploy. Verificação pós-deploy
SEMPRE por `tools/call` (o edge serve `tools/list` stale). O `deploy.bat`/`.ps1` é legado.

## 15. "Sem captcha" ≠ "viável em Worker": anti-abuso por IP bloqueia datacenter (Falcão)

O mapa de viabilidade classifica por captcha/WAF, mas há uma 3ª categoria: **anti-abuso
por IP** que bloqueia faixas de datacenter. O Falcão (`pesquisa-jt`) NÃO tem captcha e
funcionou em `wrangler dev` e no recon inicial, mas **em produção o Cloudflare Worker foi
recusado no PRIMEIRO contato** ("Tentativa invalida de acesso") — o IP de egress do Worker
é datacenter, e a penalidade é longa (horas) e persistente. Lições:

- **Validar viabilidade a partir de um IP de DATACENTER** (não só do IP residencial do
  recon): fazer 1 chamada real de um Worker de teste (ou de um proxy cloud) antes de dar
  "VIÁVEL". O IP residencial pode ter grace period que o datacenter não tem.
- Se bloquear só o datacenter: mitigações = backoff longo, proxy residencial, ou rota
  Chrome MCP (real, IP residencial — como o caso TSE/hCaptcha na lição 7).
- NÃO martelar o endpoint no recon: cada rajada estende a penalidade e contamina o teste
  de produção depois (o mesmo IP fica sujo por horas).
