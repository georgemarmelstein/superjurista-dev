// Bookmarklet para capturar sessao do PJE - TRF5
// Como usar:
// 1. Crie um novo favorito no Chrome
// 2. No campo URL, cole o codigo do bookmarklet.min.txt (tudo em uma linha)
// 3. Quando estiver logado no PJE, clique no favorito
// 4. Arquivo JSON sera baixado automaticamente

// VERSAO LEGIVEL (para entender o codigo):
(function() {
    var cookies = document.cookie;
    var ts = Date.now();

    // Auto-descoberta via objeto global do PJE (se disponivel)
    var constantes = (window.PJe && window.PJe.CONSTANTES) ? window.PJe.CONSTANTES : {};
    var appName = constantes.PJE_APP_NAME || "pje-trf5-1g";
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
            "166702"
        );
        if (loc) session.headers_api["X-pje-usuario-localizacao"] = loc;
    }

    // Download automatico
    var json = JSON.stringify(session, null, 2);
    var blob = new Blob([json], {type: 'application/json'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'pje_session_trf5-1g_' + ts + '.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    alert('Baixado: pje_session_trf5-1g_' + ts + '.json\n\nMova para a pasta do projeto.');
})();
