---
name: criar-mcp-precedente
description: >
  Use when creating MCP servers for Brazilian court jurisprudence searches.
  Focuses on scraping techniques (JSF/AJAX, HTML parsing) for tribunals without
  public REST APIs. Includes automatic boolean syntax discovery.
  Keywords: mcp tribunal, jurisprudência, scraping, precedentes, criar mcp.
---

# criar-mcp-precedente

<identidade>
  <papel>Arquiteto de MCPs para busca de precedentes judiciais</papel>
  <dominio>Web scraping jurídico, APIs de tribunais, sintaxe booleana</dominio>
  <estilo>Sistemático, iterativo, com validação empírica</estilo>
</identidade>

<proposito>
  <objetivo>Criar MCPs standalone para busca de jurisprudência em tribunais brasileiros</objetivo>
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
    - Tribunal usa reCAPTCHA v3 (bloqueio insuperável para scraping)
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

    **Se reCAPTCHA v3 detectado:**
    ```
    "Este tribunal usa reCAPTCHA v3 invisível, que é um bloqueio insuperável
    para scraping automatizado.

    Opções:
    1. Chrome MCP - Automatizar navegador real (único caminho viável)
    2. Desistir - Tribunal não é viável para MCP de scraping

    O reCAPTCHA v3 analisa comportamento do usuário (mouse, teclado, tempo)
    e gera tokens que não podem ser replicados programaticamente."
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
    - Como adicionar ao settings.json
    - Tabela completa de sintaxe booleana
    - Exemplos de uso das tools

    ### 3.5 Testar MCP

    1. Verificar sintaxe: `python -m py_compile server.py`
    2. Se possível, fazer busca de teste
    3. Validar output XML/Markdown
  </passo>

</instrucoes>

<conhecimento>
  ## Padrões de Tribunais Brasileiros

  ### Tipos de sistemas encontrados

  | Tipo | Exemplo | Características |
  |------|---------|-----------------|
  | JSF/AJAX | CJF | ViewState, Faces-Request, partial/ajax |
  | API REST | JurisDF/TJDFT | JSON puro, endpoints /api/v1/ |
  | API + Auth | JULIA/TRF5 | REST com login obrigatório |
  | ASP.NET | Alguns TJs | __VIEWSTATE, __EVENTVALIDATION |
  | reCAPTCHA v3 | TJSP (e-SAJ) | **BLOQUEIO INSUPERÁVEL** - requer Chrome MCP |

  ### Padrão de tools (obrigatório)

  Todo MCP gerado DEVE ter estas 3 tools:

  1. `buscar_[tribunal]` → Retorna XML estruturado
  2. `gerar_relatorio_[tribunal]` → Retorna Markdown formatado
  3. `listar_filtros_[tribunal]` → Lista parâmetros disponíveis

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
  - references/exemplo-jurisdf.md (API REST)
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

  **Única solução viável: Chrome MCP**
  - Automatiza navegador real do usuário
  - reCAPTCHA v3 funciona normalmente (humano está presente)
  - Limitação: requer Chrome aberto e extensão instalada

  ### Outros Bloqueadores

  | Tipo | Identificação | Viabilidade |
  |------|---------------|-------------|
  | reCAPTCHA v2 | Checkbox "Não sou robô" | Inviável sem Chrome |
  | hCaptcha | `hcaptcha.com/1/api.js` | Inviável sem Chrome |
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
       - Chrome MCP: Único caminho viável (automatiza navegador real)
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

  <exemplo tipo="detecta_api_rest">
    **Usuário:** Criar MCP para o TJDFT

    **Claude:**
    1. [WebFetch em jurisdf.tjdft.jus.br]
    2. Detectei uma API REST documentada em /api/v1/pesquisa
    3. Recomendo usar a skill mcp-builder que é otimizada para APIs REST.
    4. Repositório: https://github.com/anthropics/anthropic-tools
    5. Deseja que eu instale a mcp-builder?
  </exemplo>
</exemplos>
