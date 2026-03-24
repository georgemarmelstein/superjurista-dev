---
titulo: Template de Bookmarklet para Captura de Sessao PJE
---

# Template de Bookmarklet para Captura de Sessao PJE

Bookmarklet parametrizavel para capturar sessao do PJE de qualquer tribunal.
Metodo preferido por ser rapido (~5 segundos) e nao depender de ferramentas externas.

## Placeholders

| Placeholder | Descricao | Onde descobrir | Exemplo (TRF5) |
|-------------|-----------|----------------|-----------------|
| `{{PJE_APP_NAME}}` | Valor do header `X-pje-legacy-app` | HAR: filtrar headers por `X-pje` | `pje-trf5-1g` |
| `{{TRIBUNAL_ID}}` | Sigla curta do tribunal + instancia | Dominio do PJE | `trf5-1g` |
| `{{LOCALIZACAO_DEFAULT}}` | ID numerico da lotacao do usuario | HAR: header `X-pje-usuario-localizacao`, ou `""` se desconhecido | `166702` |

**Nota sobre auto-descoberta:** O PJE injeta `window.PJe.CONSTANTES` na pagina com valores
especificos do tribunal (`PJE_APP_NAME`, `ID_USUARIO_LOCALIZACAO`, `WEB_ROOT`, `INSTANCIA`,
`VERSAO_LEGACY`). O bookmarklet tenta ler esses valores em tempo de execucao. Se o objeto
existir, os placeholders servem apenas como fallback. Se nao existir (tribunais mais antigos),
os placeholders sao usados diretamente.

---

## Template Legivel

```javascript
// Bookmarklet para capturar sessao do PJE - {{TRIBUNAL_ID}}
// Instrucoes:
// 1. Crie um favorito no Chrome
// 2. No campo URL, cole o codigo minificado (secao abaixo)
// 3. Quando logado no PJE, clique no favorito
// 4. Arquivo JSON sera baixado automaticamente

(function() {
    var cookies = document.cookie;
    var ts = Date.now();

    // Auto-descoberta via objeto global do PJE (se disponivel)
    var constantes = (window.PJe && window.PJe.CONSTANTES) ? window.PJe.CONSTANTES : {};
    var appName = constantes.PJE_APP_NAME || "{{PJE_APP_NAME}}";
    var localizacao = constantes.ID_USUARIO_LOCALIZACAO || null;

    var session = {
        extraido_em: new Date().toISOString(),
        metodo: "bookmarklet",
        base_url: window.location.origin,
        cookies: {},
        headers_api: {
            "X-pje-legacy-app": appName,
            "X-pje-cookies": cookies
        },
        cookie_download: cookies,
        pje_info: {
            web_root: constantes.WEB_ROOT || "",
            instancia: constantes.INSTANCIA || "",
            versao: constantes.VERSAO_LEGACY || ""
        }
    };

    // Parse cookies em dicionario
    cookies.split(";").forEach(function(pair) {
        var idx = pair.trim().indexOf("=");
        if (idx > 0) {
            session.cookies[pair.trim().slice(0, idx)] = pair.trim().slice(idx + 1);
        }
    });

    // Localizacao: auto-descoberta ou prompt
    if (localizacao) {
        session.headers_api["X-pje-usuario-localizacao"] = localizacao;
    } else {
        var loc = prompt(
            "X-pje-usuario-localizacao (numero da sua lotacao):",
            "{{LOCALIZACAO_DEFAULT}}"
        );
        if (loc) session.headers_api["X-pje-usuario-localizacao"] = loc;
    }

    // Download automatico
    var json = JSON.stringify(session, null, 2);
    var blob = new Blob([json], {type: 'application/json'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'pje_session_{{TRIBUNAL_ID}}_' + ts + '.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    alert('Baixado: pje_session_{{TRIBUNAL_ID}}_' + ts + '.json\n\nMova para a pasta do projeto.');
})();
```

---

## Template Minificado

Codigo pronto para colar como URL de favorito (substituir placeholders antes):

```
javascript:(function(){var c=document.cookie;var ts=Date.now();var k=(window.PJe&&window.PJe.CONSTANTES)?window.PJe.CONSTANTES:{};var app=k.PJE_APP_NAME||"{{PJE_APP_NAME}}";var loc=k.ID_USUARIO_LOCALIZACAO||null;var s={extraido_em:new Date().toISOString(),metodo:"bookmarklet",base_url:window.location.origin,cookies:{},headers_api:{"X-pje-legacy-app":app,"X-pje-cookies":c},cookie_download:c,pje_info:{web_root:k.WEB_ROOT||"",instancia:k.INSTANCIA||"",versao:k.VERSAO_LEGACY||""}};c.split(";").forEach(function(p){var i=p.trim().indexOf("=");if(i>0)s.cookies[p.trim().slice(0,i)]=p.trim().slice(i+1)});if(loc){s.headers_api["X-pje-usuario-localizacao"]=loc}else{var l=prompt("X-pje-usuario-localizacao (numero da sua lotacao):","{{LOCALIZACAO_DEFAULT}}");if(l)s.headers_api["X-pje-usuario-localizacao"]=l}var b=new Blob([JSON.stringify(s,null,2)],{type:"application/json"});var u=URL.createObjectURL(b);var a=document.createElement("a");a.href=u;a.download="pje_session_{{TRIBUNAL_ID}}_"+ts+".json";document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(u);alert("Baixado: pje_session_{{TRIBUNAL_ID}}_"+ts+".json")})();
```

---

## Instrucoes para o Agente Gerador

Ao gerar o bookmarklet para um novo tribunal:

1. **Substituir placeholders** com valores descobertos nos passos de analise de HAR:
   - `{{PJE_APP_NAME}}` -> valor de `X-pje-legacy-app` encontrado no HAR
   - `{{TRIBUNAL_ID}}` -> sigla derivada do dominio (ex: `trf1-1g`, `trt15`, `tjsp`)
   - `{{LOCALIZACAO_DEFAULT}}` -> valor de `X-pje-usuario-localizacao` do HAR, ou `""` se nao encontrado

2. **Gerar dois arquivos** na pasta da skill:
   - `bookmarklet.js` - versao legivel com comentarios e instrucoes
   - `bookmarklet.min.txt` - versao minificada pronta para colar como URL de favorito

3. **Validar** que o codigo minificado e sintaticamente valido (sem quebras de linha, aspas balanceadas)

4. **Testar mentalmente** o fluxo:
   - Se `window.PJe.CONSTANTES` existir -> app name e localizacao sao preenchidos automaticamente
   - Se nao existir -> usa fallback do placeholder e prompt para localizacao
   - `document.cookie` captura cookies nao-HttpOnly (suficiente para maioria dos PJEs)

5. **Documentar no SKILL.md da skill gerada** como instalar o bookmarklet no navegador

---

## Formato do sessao.json Gerado

O bookmarklet produz um JSON com os campos comuns listados abaixo. Este formato
nao e um contrato rigido: o agente que cria a skill para um novo tribunal deve
verificar o que os scripts Python desse tribunal realmente consomem (via `Read`
nos scripts) e adaptar o bookmarklet se necessario.

**Campos comuns:**
| Campo | Tipo | Uso |
|-------|------|-----|
| `cookies` | `{string: string}` | Dicionario de cookies parseados |
| `headers_api` | `{string: string}` | Headers para API REST (`X-pje-*`) |
| `cookie_download` | `string` | String bruta de cookies para header `Cookie` |
| `base_url` | `string` | Origem do tribunal (`window.location.origin`) |
| `extraido_em` | `string` ISO-8601 | Timestamp da captura |
| `metodo` | `string` | Sempre `"bookmarklet"` |
| `pje_info` | `{string: string}` | Metadados do PJe (se `CONSTANTES` existir) |

**Campo critico para validacao:** `headers_api["X-pje-cookies"]` deve ser nao-vazio.
Este e o unico campo verificado pelo comando `/baixar-pje` na Etapa 0.

---

## Quando o Bookmarklet NAO Funciona

| Cenario | Sintoma | Solucao |
|---------|---------|---------|
| Cookies HttpOnly | `document.cookie` retorna string vazia ou incompleta | Usar HAR (captura na camada de rede) |
| CSP bloqueando inline JS | Bookmarklet nao executa | Usar console do DevTools ou HAR |
| `window.PJe` nao existe | Fallback para placeholder funciona, mas localizacao requer prompt | Normal em PJEs mais antigos |
| Tribunal usa autenticacao diferente | JSON gerado nao tem cookies esperados | Investigar via HAR e adaptar bookmarklet |
