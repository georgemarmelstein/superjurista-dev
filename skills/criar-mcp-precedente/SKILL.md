---
name: criar-mcp-precedente
description: >
  Use when creating MCP servers for court jurisprudence searches — Brazilian tribunals
  and international courts (proven on CJF, TCU, TJSC/eProc and HUDOC/ECHR). Focuses on
  scraping techniques (JSF/AJAX, HTML parsing, undocumented JSON APIs) for courts without
  public REST APIs. Includes automatic boolean syntax discovery and routing: scraping MCP
  vs mcp-builder (documented REST) vs Chrome-MCP skill (per-request CAPTCHA).
  Keywords: mcp tribunal, jurisprudência, scraping, precedentes, criar mcp, corte internacional.
---

# criar-mcp-precedente

<identidade>
  <papel>Arquiteto de MCPs para busca de precedentes judiciais</papel>
  <dominio>Web scraping jurídico, APIs de tribunais, sintaxe booleana</dominio>
  <estilo>Sistemático, iterativo, com validação empírica</estilo>
</identidade>

<proposito>
  <objetivo>Criar MCPs standalone para busca de jurisprudência em tribunais brasileiros e cortes internacionais</objetivo>
  <razao>Tribunais usam sistemas heterogêneos (JSF, AJAX, APIs não documentadas) que exigem engenharia reversa</razao>
  <resultado>MCP funcional com tools buscar_*, gerar_relatorio_*, listar_* e documentação de sintaxe booleana</resultado>
</proposito>

<quando_usar>
  <gatilhos>
    Use quando:
    - Usuário quer criar MCP para tribunal sem API documentada
    - Precisa fazer scraping de página de jurisprudência
    - Quer descobrir sintaxe booleana de um tribunal
    - Tribunal usa JSF/AJAX ou formulários complexos
  </gatilhos>

  <exclusoes>
    NÃO use quando:
    - Tribunal tem API REST documentada (usar mcp-builder)
    - Apenas quer fazer buscas pontuais (usar MCPs existentes)
    - Tribunal já tem MCP implementado no projeto
    - Portal exige CAPTCHA por requisição (reCAPTCHA/hCaptcha) — a rota comprovada é
      criar uma SKILL que busca via Chrome MCP, não um MCP server (caso real:
      jurisprudencia-eleitoral para o SJUR/TSE)
  </exclusoes>

  <keywords>
    Palavras-chave: criar mcp, novo tribunal, scraping jurisprudência,
    descobrir booleanos, jurisprudência tribunal, mcp precedentes
  </keywords>
</quando_usar>

<instrucoes>

  <passo numero="0" nome="Análise inicial e configuração">
    ## Fase 0: Análise Inicial

    ### 0.1 Coletar URL do tribunal
    Solicitar ao usuário a URL da página de busca de jurisprudência.

    ### 0.2 Perguntar localização do MCP
    Usar AskUserQuestion:
    ```
    Onde deseja criar o MCP?

    1. Projeto atual (.claude/mcp-servers/[nome]/)
       → Disponível apenas neste projeto

    2. Global (~/.claude/mcp-servers/[nome]/)
       → Disponível em todos os projetos

    3. Diretório customizado
       → Informar caminho
    ```

    Em qualquer opção, o arquivo pode viver onde o usuário preferir — o que ativa o MCP
    é o REGISTRO no `.mcp.json` da raiz do projeto, com caminho ABSOLUTO do server.py
    (ver Fase 3.4). NÃO registrar em settings.json: config de MCP ali é padrão antigo
    e quebra silenciosamente (o servidor simplesmente não aparece).

    ### 0.3 Analisar tipo de API
    Usar WebFetch na URL para detectar:

    **Sinais de API REST aberta (→ recomendar mcp-builder):**
    - Documentação Swagger/OpenAPI visível
    - Endpoints /api/v1/ retornando JSON puro
    - Headers CORS permissivos
    - Sem ViewState/CSRF tokens

    **Sinais de scraping necessário (→ continuar):**
    - Formulários JSF (javax.faces.ViewState)
    - AJAX com tokens CSRF
    - Respostas em HTML/XML parcial
    - Session cookies obrigatórios

    **Sinais de bloqueio insuperável (→ abortar ou Chrome MCP):**
    - reCAPTCHA v3 invisível (script google.com/recaptcha com `size=invisible`)
    - reCAPTCHA v2 (checkbox "Não sou um robô")
    - hCaptcha ou outros CAPTCHAs comportamentais
    - Cloudflare Bot Protection

    ### 0.4 Decisão de roteamento

    **Se API REST aberta detectada:**
    ```
    "Detectei uma API REST documentada. Recomendo usar a skill mcp-builder.

    Repositório: https://github.com/anthropics/anthropic-tools

    Deseja que eu instale a mcp-builder?"
    ```

    **Se CAPTCHA por requisição detectado (reCAPTCHA v3/v2, hCaptcha):**
    ```
    "Este portal exige um token de CAPTCHA a cada busca — bloqueio insuperável
    para um MCP server em Python puro.

    Opções:
    1. SKILL via Chrome MCP (rota comprovada) — em vez de MCP server, criar uma
       skill que roda a busca DENTRO do navegador real: o CAPTCHA gera o token
       normalmente porque há um Chrome de verdade. Modelo vivo:
       .claude/skills/jurisprudencia-eleitoral (SJUR/TSE, hCaptcha invisível,
       token de uso único por requisição, hcaptcha.reset() + retry).
    2. Endpoints parcialmente abertos — antes de desistir, verificar se PARTE da
       superfície dispensa CAPTCHA (no TSE, o download do inteiro teor em PDF é
       aberto: só a busca é protegida). Um MCP híbrido pode cobrir a parte aberta.
    3. Desistir — portal inviável.

    O CAPTCHA comportamental analisa mouse, teclado e tempo, e gera tokens que
    não podem ser replicados programaticamente."
    ```

    Se não houver bloqueios, continuar para Fase 1.
  </passo>

  <passo numero="1" nome="Descoberta de endpoints">
    ## Fase 1: Descoberta de Endpoints

    Usar estratégias em ordem de preferência:

    ### Estratégia A: Chrome MCP (preferida)

    Se Chrome MCP disponível:
    1. `mcp__claude-in-chrome__tabs_create_mcp` - criar aba
    2. `mcp__claude-in-chrome__navigate` - ir para página de busca
    3. `mcp__claude-in-chrome__read_network_requests` - iniciar captura
    4. `mcp__claude-in-chrome__javascript_tool` - executar busca de teste
    5. Analisar requests capturados

    Extrair:
    - URL do endpoint
    - Method (GET/POST)
    - Headers obrigatórios
    - Formato do body (JSON, form-urlencoded, multipart)
    - Tokens/ViewState se houver

    ### Estratégia B: Análise de HAR (fallback)

    Se Chrome MCP indisponível:
    1. Solicitar arquivo HAR ao usuário:
       ```
       "Exporte o HAR via Chrome DevTools:
       1. Abra F12 > aba Network
       2. Faça uma busca no site
       3. Botão direito na lista > Save all as HAR"
       ```
    2. Ler arquivo HAR com Read tool
    3. Filtrar requests POST para endpoints de busca
    4. Extrair padrões

    ### Estratégia C: WebFetch + Análise HTML (mínimo)

    Se nenhuma opção anterior:
    1. WebFetch na URL do tribunal
    2. Analisar estrutura do formulário (campos, action, hidden fields)
    3. Inferir endpoint
    4. Se muito JS-dependente, solicitar HAR

    ### Output da Fase 1

    ```python
    endpoint_info = {
        "url": "https://tribunal.jus.br/api/pesquisa",
        "method": "POST",
        "content_type": "application/json",
        "requires_session": True,
        "session_url": "https://tribunal.jus.br/login",
        "headers": ["User-Agent", "Accept", "X-Requested-With"],
        "body_template": {"query": "", "pagina": 0, "tamanho": 20},
        "response_format": "json",  # ou "html" ou "xml"
    }
    ```
  </passo>

  <passo numero="2" nome="Descoberta de booleanos">
    ## Fase 2: Descoberta de Booleanos

    ### 2.1 Buscar documentação oficial

    WebSearch:
    - "site:[tribunal].jus.br operadores busca"
    - "site:[tribunal].jus.br manual pesquisa jurisprudência"
    - "site:[tribunal].jus.br sintaxe busca avançada"

    Se encontrar → extrair e validar com testes
    Se não → ir direto para testes empíricos

    ### 2.2 Testes empíricos sistemáticos

    Query base: termo comum (ex: "aposentadoria", "contrato")

    | Categoria     | Variações a testar                              |
    |---------------|------------------------------------------------|
    | AND           | E, e, AND, and, +, (implícito sem operador)    |
    | OR            | OU, ou, OR, or, \|                              |
    | NOT           | NAO, nao, NOT, not, -, !                       |
    | Frase exata   | "termo composto", 'termo composto'             |
    | Hífen         | auxílio-doença, "auxílio-doença", auxílio doença|
    | Wildcard suf. | aposentad$, aposentad*                         |
    | Wildcard pref.| $doença, *doença                               |
    | Wildcard ambos| $termo$, *termo*                               |
    | Proximidade   | ADJ, adj, PROX, prox, NEAR, ADJ5, PROX/3       |

    ### 2.3 Lógica de análise

    Para cada variação:
    1. Executar busca (via endpoint descoberto ou WebFetch)
    2. Contar resultados
    3. Comparar com busca base

    Interpretação:
    - Contagem > 0 e diferente da base → operador funciona
    - Contagem = 0 → não funciona ou erro sintaxe
    - Contagem igual à base → operador ignorado

    ### 2.4 Gerar tabela de operadores

    Exemplo de output (case varia por tribunal):

    ```markdown
    | Operador    | Sintaxe   | Case       | Exemplo                              |
    |-------------|-----------|------------|--------------------------------------|
    | AND         | e         | minúsculo  | pensão e morte                       |
    | OR          | ou        | minúsculo  | bpc ou loas                          |
    | NOT         | nao       | minúsculo  | servidor nao militar                 |
    | Frase exata | "..."     | -          | "pensão por morte"                   |
    | Hífen       | preservar | -          | auxílio-doença                       |
    | Wildcard    | $         | sufixo     | aposentad$ → aposentadoria, aposentado|
    | Wildcard    | $         | prefixo    | $doença → auxílio-doença             |
    | Proximidade | adj       | minúsculo  | contrato adj administrativo          |
    ```
  </passo>

  <passo numero="3" nome="Geração do MCP">
    ## Fase 3: Geração do MCP

    ### 3.1 Estrutura de arquivos

    No destino escolhido pelo usuário:
    ```
    [nome-tribunal]/
    ├── server.py          # Servidor MCP standalone
    ├── requirements.txt   # Dependências Python
    └── README.md          # Instruções e sintaxe
    ```

    ### 3.2 Gerar server.py

    Usar template em: references/template-server.py

    Substituir placeholders:
    - [NOME_TRIBUNAL] → nome do tribunal
    - [URL_DESCOBERTA] → endpoint da Fase 1
    - [CONTENT_TYPE] → formato descoberto
    - [TABELA_BOOLEANOS] → tabela da Fase 2
    - [IMPLEMENTACAO_SESSAO] → se requires_session
    - [IMPLEMENTACAO_EXTRACAO] → baseado em response_format

    Regras aprendidas em campo (detalhes em references/licoes-de-campo.md):
    - Implementar a busca UMA vez, na `_fazer_busca()` compartilhada — buscar_* e
      gerar_relatorio_* apenas a chamam (nos 3 MCPs reais do projeto é assim).
    - Portal com charset legado (eProc e sistemas antigos servem iso-8859-1):
      fixar `response.encoding` explicitamente, senão acentos viram mojibake.
    - Paginação: quando o portal pagina, iterar até max_resultados reaproveitando
      cookies da primeira resposta (padrão TJSC).
    - Portal com múltiplas bases (acórdãos/súmulas/normas, padrão TCU): parâmetro
      `base` com `Literal[...]`, um extractor por base, e a 3ª tool vira
      `listar_bases_*` em vez de `listar_filtros_*`.
    - API com linguagem de query própria (padrão HUDOC): construir a query por
      funções dedicadas (`_construir_query`, `_or_filter`), nunca por concatenação
      solta na tool.

    ### 3.3 Gerar requirements.txt

    ```
    mcp>=1.0.0
    httpx>=0.25.0
    pydantic>=2.0.0
    beautifulsoup4>=4.12.0  # se scraping HTML
    tenacity>=8.0.0         # se retry necessário
    ```

    ### 3.4 Gerar README.md

    Incluir:
    - Instruções de instalação
    - Como registrar no `.mcp.json` da raiz do projeto (caminho absoluto):
      ```json
      {
        "mcpServers": {
          "[nome-tribunal]": {
            "command": "python",
            "args": ["C:\\caminho\\absoluto\\para\\[nome-tribunal]\\server.py"]
          }
        }
      }
      ```
    - Tabela completa de sintaxe booleana
    - Exemplos de uso das tools

    ### 3.5 Testar MCP

    1. Verificar sintaxe: `python -m py_compile server.py`
    2. Se possível, fazer busca de teste
    3. Validar output XML/Markdown
    4. Registrar no `.mcp.json` e lembrar: o servidor só carrega em sessão nova
  </passo>

</instrucoes>

<conhecimento>
  ## Padrões de Tribunais Brasileiros

  ### Tipos de sistemas encontrados

  | Tipo | Exemplo | Características |
  |------|---------|-----------------|
  | JSF/AJAX | CJF | ViewState, Faces-Request, partial/ajax |
  | API JSON não documentada | TCU, HUDOC (CEDH) | JSON puro descoberto via Network tab; às vezes com linguagem de query própria e múltiplas bases |
  | API REST documentada | JurisDF/TJDFT (descontinuada) | JSON + /api/v1/ → recomendar mcp-builder |
  | API + Auth | JULIA/TRF5 | REST com login obrigatório |
  | HTML legado (eProc) | TJSC | POST form-urlencoded, resposta HTML em iso-8859-1, paginação por endpoint AJAX próprio |
  | ASP.NET | Alguns TJs | __VIEWSTATE, __EVENTVALIDATION |
  | CAPTCHA por requisição | TSE (SJUR, hCaptcha), TJSP (e-SAJ, reCAPTCHA v3) | **BLOQUEIO para MCP** — rota: skill via Chrome MCP |

  ### Padrão de tools (obrigatório)

  Todo MCP gerado DEVE ter estas 3 tools:

  1. `buscar_[tribunal]` → Retorna XML estruturado
  2. `gerar_relatorio_[tribunal]` → Retorna Markdown formatado
  3. `listar_filtros_[tribunal]` → Lista parâmetros disponíveis
     (variação legítima: `listar_bases_[tribunal]` quando o portal tem múltiplas
     bases pesquisáveis — padrão TCU: acórdãos, jurisprudência selecionada, normas)

  ### Formato XML de saída

  ```xml
  <jurisprudencia_[tribunal] total="N">
    <item indice="1">
      <tipo>Acórdão</tipo>
      <numero>0001234-56.2024.8.07.0000</numero>
      <orgao>1ª Turma Cível</orgao>
      <relator>Des. Nome Sobrenome</relator>
      <data>15/01/2024</data>
      <conteudo>Ementa do julgado...</conteudo>
      <fonte>https://link.para.inteiro.teor</fonte>
    </item>
  </jurisprudencia_[tribunal]>
  ```

  ### Referências de implementação

  Ver exemplos reais em:
  - references/exemplo-cjf.md (scraping JSF/AJAX)
  - references/exemplo-jurisdf.md (API REST — serviço descontinuado; padrão continua válido)
  - references/licoes-de-campo.md (lições dos MCPs reais: TCU, TJSC/eProc, HUDOC, o caso TSE e os trabalhistas TST/Falcão — LER antes de construir)
  - references/template-server.py (template base)
  - references/sintaxe-booleanos.md (guia de descoberta)

  ## Bloqueadores de Scraping

  ### reCAPTCHA v3 (Bloqueio Insuperável)

  **Identificação no HAR/HTML:**
  - URL: `google.com/recaptcha/api.js?render=SITE_KEY`
  - Parâmetros: `size=invisible`, `execute-ms=30000`
  - POST requer: `recaptcha_response_token` (token de ~1200 chars)

  **Por que é insuperável:**
  1. Token gerado por JavaScript do Google no navegador real
  2. Analisa comportamento: movimento do mouse, tempo de digitação, histórico
  3. Score de 0.0 a 1.0 - bots recebem score baixo e são bloqueados
  4. Não existe forma legítima de gerar tokens programaticamente

  **Tribunais conhecidos com reCAPTCHA v3:**
  - TJSP (e-SAJ): `6LcXJIAbAAAAAOwprTGEEYwRSe-HMYD-Ys0pSR6f`

  **Solução comprovada: SKILL via Chrome MCP (não um MCP server)**
  - Automatiza o navegador real do usuário — o CAPTCHA gera o token normalmente
    porque há um humano/Chrome de verdade presente
  - Caso real implementado: skill `jurisprudencia-eleitoral` para o SJUR/TSE
    (hCaptcha invisível, token de uso único por busca): a skill navega até o SPA,
    espera `window.hcaptcha` carregar, executa a busca via `javascript_tool` e
    faz `hcaptcha.reset()` + retry (até 3x) para cada nova requisição
  - Dica antes de desistir: mapear a superfície ABERTA do portal — no TSE, o
    download do inteiro teor (PDF) dispensa CAPTCHA; só a busca é protegida
  - Limitação: requer Chrome aberto e extensão instalada

  ### Outros Bloqueadores

  | Tipo | Identificação | Viabilidade |
  |------|---------------|-------------|
  | reCAPTCHA v2 | Checkbox "Não sou robô" | Inviável sem Chrome → skill Chrome MCP |
  | hCaptcha | `hcaptcha.com/1/api.js` ou `window.hcaptcha` no SPA | Inviável sem Chrome → skill Chrome MCP (caso TSE) |
  | Cloudflare | `cf-ray`, `__cf_bm` cookie | Às vezes contornável |
  | WAF genérico | 403/429 após poucas requests | Rate limiting ajuda |
</conhecimento>

<restricoes>
  <nunca>
    - Gerar MCP que dependa de shared/base_juridica.py (deve ser standalone)
    - Pular a fase de descoberta de booleanos
    - Assumir sintaxe sem testar empiricamente
    - Criar MCP sem as 3 tools padrão (buscar, relatorio, listar)
    - Hardcodar credenciais no código
  </nunca>

  <sempre>
    - Perguntar onde criar o MCP antes de gerar
    - Testar case sensitivity dos operadores (MAIÚSCULO e minúsculo)
    - Testar wildcards em prefixo E sufixo
    - Incluir tabela de booleanos na docstring da tool buscar_*
    - Gerar README.md com instruções completas
    - Registrar no `.mcp.json` da raiz do projeto (caminho absoluto), nunca em settings.json
    - Implementar a busca UMA vez (`_fazer_busca` compartilhada entre buscar_* e gerar_relatorio_*)
    - Fixar `response.encoding` quando o portal servir charset legado (ex.: iso-8859-1 no eProc)
    - Recomendar mcp-builder se detectar API REST aberta
  </sempre>
</restricoes>

<exemplos>
  <exemplo tipo="recaptcha_detectado">
    **Usuário:** Quero criar um MCP para o TJSP

    **Claude:**
    1. Qual a URL da página de jurisprudência?
    2. [Usuário: https://esaj.tjsp.jus.br/cjsg/]
    3. [WebFetch na URL → detecta reCAPTCHA v3]
    4. Este tribunal usa reCAPTCHA v3 invisível (chave: 6LcXJIAb...).
       Este é um bloqueio insuperável para scraping automatizado.

       O reCAPTCHA v3 analisa comportamento do usuário e gera tokens
       que não podem ser replicados programaticamente.

       Opções:
       - Skill via Chrome MCP: rota comprovada (modelo: jurisprudencia-eleitoral/TSE)
       - Verificar endpoints parcialmente abertos (inteiro teor às vezes dispensa CAPTCHA)
       - Desistir: TJSP não é viável para MCP de scraping tradicional

       Sintaxe booleana descoberta (para referência):
       - E, OU, NÃO (case insensitive)
       - ? (wildcard de 1 caractere)
       - "..." (frase exata, máx 5 palavras)
  </exemplo>

  <exemplo tipo="fluxo_completo">
    **Usuário:** Quero criar um MCP para o CJF

    **Claude:**
    1. Qual a URL da página de jurisprudência?
    2. [Usuário: https://www2.cjf.jus.br/jurisprudencia/unificada/]
    3. Onde deseja criar o MCP? (AskUserQuestion)
    4. [Usuário: Projeto atual]
    5. [WebFetch na URL → detecta JSF com ViewState, sem CAPTCHA]
    6. Vou descobrir os endpoints via análise...
    7. [Executa Fase 1 → encontra endpoint de busca]
    8. Agora vou testar a sintaxe booleana...
    9. [Executa Fase 2 → descobre: E/OU MAIÚSCULO, ADJ, PROX]
    10. Gerando MCP em .claude/mcp-servers/cjf/
    11. [Cria server.py, requirements.txt, README.md]
    12. MCP criado! Adicione ao settings.json conforme README.
  </exemplo>

  <exemplo tipo="detecta_api_json_nao_documentada">
    **Usuário:** Criar MCP para o TCU

    **Claude:**
    1. [Chrome MCP: read_network_requests durante uma busca no portal]
    2. Detectei uma API JSON não documentada (POST retornando JSON puro), com
       três bases distintas: acórdãos, jurisprudência selecionada e normas.
    3. Sem CAPTCHA e sem login → viável para MCP de scraping.
    4. Gero o MCP com parâmetro `base` (Literal), um extractor por base e a
       terceira tool como `listar_bases_tcu`.
  </exemplo>

  <exemplo tipo="detecta_api_rest_documentada">
    **Usuário:** Criar MCP para um tribunal com Swagger público

    **Claude:**
    1. [WebFetch na URL → documentação OpenAPI visível]
    2. Detectei uma API REST documentada.
    3. Recomendo usar a skill mcp-builder, otimizada para APIs REST
       (repositório oficial de skills da Anthropic: github.com/anthropics/skills).
    4. Deseja que eu siga com a mcp-builder?
  </exemplo>
</exemplos>
