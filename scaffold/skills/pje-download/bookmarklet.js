// Bookmarklet para capturar sessao do PJE
// Como usar:
// 1. Crie um novo favorito no Chrome
// 2. No campo URL, cole o codigo abaixo (tudo em uma linha)
// 3. Quando estiver logado no PJE, clique no favorito
// 4. Arquivo JSON sera baixado automaticamente

// CODIGO DO BOOKMARKLET (cole como URL do favorito):
// javascript:(function(){var c=document.cookie;var ts=Date.now();var h={cookies:{},headers_api:{"X-pje-legacy-app":"pje-trf5-1g"},cookie_download:c,extraido_em:new Date().toISOString(),metodo:"bookmarklet"};c.split(";").forEach(function(p){var kv=p.trim().split("=");if(kv[0])h.cookies[kv[0]]=kv[1]||""});h.headers_api["X-pje-cookies"]=c;var loc=prompt("Digite o X-pje-usuario-localizacao (numero da sua localizacao):","166702");if(loc)h.headers_api["X-pje-usuario-localizacao"]=loc;var json=JSON.stringify(h,null,2);var blob=new Blob([json],{type:"application/json"});var url=URL.createObjectURL(blob);var a=document.createElement("a");a.href=url;a.download="pje_session_"+ts+".json";document.body.appendChild(a);a.click();document.body.removeChild(a);URL.revokeObjectURL(url);alert("Arquivo baixado: pje_session_"+ts+".json\n\nMova para a pasta do projeto superjurista/")})();

// VERSAO LEGIVEL (para entender o codigo):
(function() {
    var cookies = document.cookie;
    var ts = Date.now();  // Timestamp para nome unico

    var session = {
        cookies: {},
        headers_api: {
            "X-pje-legacy-app": "pje-trf5-1g"
        },
        cookie_download: cookies,
        extraido_em: new Date().toISOString(),
        metodo: "bookmarklet"
    };

    // Parse cookies
    cookies.split(";").forEach(function(pair) {
        var kv = pair.trim().split("=");
        if (kv[0]) {
            session.cookies[kv[0]] = kv[1] || "";
        }
    });

    // X-pje-cookies e a string completa de cookies
    session.headers_api["X-pje-cookies"] = cookies;

    // Pedir localizacao do usuario (esse valor muda por usuario)
    var localizacao = prompt(
        "Digite o X-pje-usuario-localizacao (numero da sua localizacao):",
        "166702"
    );

    if (localizacao) {
        session.headers_api["X-pje-usuario-localizacao"] = localizacao;
    }

    var json = JSON.stringify(session, null, 2);

    // Criar blob e fazer download (com nome unico)
    var blob = new Blob([json], {type: 'application/json'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'pje_session_' + ts + '.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    alert('Arquivo baixado: pje_session_' + ts + '.json\n\nMova para a pasta do projeto superjurista/');
})();
