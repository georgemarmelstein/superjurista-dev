# Lições de Campo — MCPs reais criados com esta skill

Registro das técnicas que os MCPs reais exigiram além do template base. Fontes:
`tcu-jurisprudencia` (02/2026), `tjsc-eproc` (03/2026), `hudoc-echr` (07/2026) e o caso
TSE/SJUR (07/2026, resolvido como skill Chrome MCP, não como MCP server).

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
