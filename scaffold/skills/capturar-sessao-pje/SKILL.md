---
name: capturar-sessao-pje
description: Captura sessao do PJE via Chrome MCP com login automatico. Use antes de baixar processos.
context: fork
agent: general-purpose
allowed-tools: Bash Read Write mcp__claude-in-chrome__tabs_context_mcp mcp__claude-in-chrome__tabs_create_mcp mcp__claude-in-chrome__javascript_tool mcp__claude-in-chrome__navigate mcp__claude-in-chrome__form_input mcp__claude-in-chrome__computer mcp__claude-in-chrome__read_page
---

# Capturar Sessao PJE

<identidade>
Especialista em automacao de captura de sessao do PJE TRF5 via Chrome MCP.
</identidade>

<proposito>
Automatizar o login no PJE e captura de cookies de sessao para uso pelos scripts de listagem e download de processos.
</proposito>

---

## Metodos de Captura (em ordem de preferencia)

| Path | Metodo | Quando usar | Tempo |
|------|--------|-------------|-------|
| 1 | **Bookmarklet** | Usuario ja logado, bookmarklet instalado | ~5s |
| 2 | **Chrome MCP + JS** | Precisa automatizar login, Chrome MCP disponivel | ~30s |
| 3 | **HAR manual** | Bookmarklet falha (HttpOnly, CSP) ou Chrome MCP indisponivel | ~5-10min |

### Path 1: Bookmarklet (preferido)

Se o usuario ja tiver o bookmarklet instalado no navegador:

1. Verificar que esta logado no PJE
2. Pedir que clique no bookmarklet
3. Copiar arquivo baixado para o projeto:

```bash
ARQUIVO=$(ls -t ~/Downloads/pje_session_*.json 2>/dev/null | head -1)
if [ -n "$ARQUIVO" ]; then
    cp "$ARQUIVO" pje_session.json
    echo "[OK] $(basename $ARQUIVO) -> pje_session.json"
else
    echo "[ERRO] Nenhum pje_session_*.json encontrado em Downloads"
fi
```

4. Validar sessao:

```bash
python -c "
import json
d = json.load(open('pje_session.json'))
cookies = d.get('cookies', {})
headers = d.get('headers_api', {})
has_session = 'JSESSIONID' in cookies or 'JSESSIONID' in d.get('cookie_download', '')
has_xpje = 'X-pje-cookies' in headers and len(headers['X-pje-cookies']) > 50
if has_session and has_xpje:
    print('[OK] Sessao completa (listagem + download)')
elif has_session:
    print('[AVISO] Sessao parcial')
else:
    print('[ERRO] Sessao invalida')
"
```

Se o bookmarklet nao estiver instalado, orientar o usuario a instalar:
1. Abrir `.claude/skills/pje-download/bookmarklet.min.txt`
2. Copiar TODO o conteudo (comeca com `javascript:`)
3. No Chrome: Favoritos > Gerenciar favoritos > Adicionar favorito
4. Nome: "PJE Session"
5. URL: colar o conteudo copiado

Se o bookmarklet falhar, usar Path 2 ou Path 3.

---

## Credenciais

As credenciais estao em `.env` na raiz do projeto (arquivo NAO versionado):

```env
PJE_CPF=seu_cpf_aqui
PJE_SENHA=sua_senha_aqui
```

Para ler (se necessario preencher manualmente):
```bash
source .env 2>/dev/null || true
echo $PJE_CPF
```

---

## Path 2: Fluxo Chrome MCP

### Etapa 1: Verificar Chrome MCP

```
mcp__claude-in-chrome__tabs_context_mcp
```

Se Chrome MCP nao disponivel, ir para Metodo Fallback.

### Etapa 2: Verificar aba PJE existente

Se ja houver aba com URL contendo `pje1g.trf5.jus.br` E `QuadroAviso` ou `painel`:
- Usuario JA esta logado
- Pular para Etapa 5 (captura de sessao)

### Etapa 3: Criar aba e navegar

```
mcp__claude-in-chrome__tabs_create_mcp
mcp__claude-in-chrome__navigate -> https://pje1g.trf5.jus.br/pje/login.seam
mcp__claude-in-chrome__computer (action: wait, duration: 2)
```

### Etapa 4: Login

O Chrome geralmente preenche automaticamente via autofill. Verificar com screenshot:

```
mcp__claude-in-chrome__computer (action: screenshot)
```

**Se campos preenchidos (autofill):**
- Clicar no botao ENTRAR

**Se campos vazios:**
- Ler credenciais do .env
- Preencher CPF e senha manualmente via form_input ou computer+type
- Clicar no botao ENTRAR

```
mcp__claude-in-chrome__computer (action: left_click, coordinate: [x, y do botao ENTRAR])
mcp__claude-in-chrome__computer (action: wait, duration: 4)
```

**Verificar login:**
- URL deve conter `QuadroAviso` ou `painel`
- Se ainda na pagina de login, verificar erro e reportar

### Etapa 5: Capturar sessao via JavaScript

Injetar o script que usa a API do PJe:

```javascript
(function() {
    var cookieNames = ['KEYCLOAK_IDENTITY', 'KEYCLOAK_SESSION', 'JSESSIONID',
                       'trf5017e3f72', 'dtCookie', 'PJELEGACYStickySessionRule',
                       'ROUTER_ID', 'PJE-TRF5-1G-StickySessionRule'];
    var cookies = {};
    for (var name of cookieNames) {
        var val = window.PJe && window.PJe.getCookie ? window.PJe.getCookie(name) : null;
        if (val) cookies[name] = val;
    }

    var constantes = window.PJe && window.PJe.CONSTANTES ? window.PJe.CONSTANTES : {};
    var ts = Date.now();

    var session = {
        extraido_em: new Date().toISOString(),
        metodo: "chrome-mcp-auto",
        cookies: cookies,
        headers_api: {
            "X-pje-legacy-app": constantes.PJE_APP_NAME || "pje-trf5-1g",
            "X-pje-usuario-localizacao": constantes.ID_USUARIO_LOCALIZACAO || "",
            "X-pje-cookies": document.cookie
        },
        cookie_download: document.cookie,
        pje_info: {
            web_root: constantes.WEB_ROOT || "",
            instancia: constantes.INSTANCIA || "",
            versao: constantes.VERSAO_LEGACY || ""
        }
    };

    var blob = new Blob([JSON.stringify(session, null, 2)], {type: 'application/json'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'pje_session_' + ts + '.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    'Download iniciado: pje_session_' + ts + '.json';
})();
```

### Etapa 6: Copiar arquivo para projeto

```bash
# Encontrar arquivo mais recente
ARQUIVO=$(ls -t ~/Downloads/pje_session_*.json 2>/dev/null | head -1)

if [ -n "$ARQUIVO" ]; then
    cp "$ARQUIVO" pje_session.json
    echo "[OK] Sessao copiada para pje_session.json"
else
    echo "[ERRO] Arquivo nao encontrado em Downloads"
fi
```

### Etapa 7: Validar sessao

```bash
python -c "
import json
d = json.load(open('pje_session.json'))
cookies = d.get('cookies', {})
headers = d.get('headers_api', {})
has_session = 'JSESSIONID' in cookies or 'JSESSIONID' in d.get('cookie_download', '')
has_xpje = 'X-pje-cookies' in headers and len(headers['X-pje-cookies']) > 50
if has_session and has_xpje:
    print('[OK] Sessao completa (listagem + download)')
elif has_session:
    print('[AVISO] Sessao parcial')
else:
    print('[ERRO] Sessao invalida')
"
```

---

## Path 3: Metodo Fallback - HAR Manual

Se Chrome MCP nao estiver disponivel:

```
Preciso do arquivo HAR para capturar a sessao do PJE.

1. Abra o PJE no navegador: https://pje1g.trf5.jus.br/pje/login.seam
2. Faca login com CPF e senha
3. Abra DevTools (F12) -> aba Network
4. Navegue pelo painel (clique em Minhas Tarefas)
5. Clique direito na lista de requisicoes -> "Save all as HAR"
6. Me informe o caminho do arquivo salvo
```

Apos receber o caminho:
```bash
python .claude/skills/pje-download/scripts/extrair_cookies_har.py \
  --har "CAMINHO_DO_HAR" \
  --output pje_session.json
```

---

## Cookies Necessarios

| Cookie | Funcao | Capturado por |
|--------|--------|---------------|
| JSESSIONID | Sessao JSF | JavaScript |
| KEYCLOAK_IDENTITY | Autenticacao SSO | JavaScript |
| PJE-TRF5-1G-StickySessionRule | Load balancer | JavaScript |
| ROUTER_ID | Roteamento | JavaScript |
| trf5017e3f72 | Token interno | JavaScript |
| X-pje-cookies (header) | String completa | document.cookie |

---

## Retorno

Retorne APENAS:
- Status: sucesso/falha
- Metodo usado: chrome-mcp-auto / chrome-mcp-manual / har
- Cookies principais encontrados (apenas nomes)
- Caminho do arquivo: pje_session.json

NAO retorne:
- Valores dos cookies
- Credenciais
- Logs detalhados
