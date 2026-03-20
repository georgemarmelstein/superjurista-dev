# Playbook: Baixar Processos do PJE

Este documento descreve o processo completo para baixar processos conclusos do PJE TRF5.

## Visao Geral

O fluxo de download de processos do PJE envolve tres etapas principais:

1. **Autenticacao**: Extrair cookies e tokens de sessao
2. **Listagem**: Obter lista de processos conclusos para sentenca ou decisao
3. **Download**: Baixar PDFs dos autos e extrair texto

## Arquitetura de Autenticacao do PJE

O PJE utiliza dois sistemas de autenticacao paralelos:

| Sistema | Uso | Headers/Cookies |
|---------|-----|-----------------|
| **API REST** | Listar processos, obter codigo de acesso | Authorization (JWT), X-pje-cookies, X-pje-usuario-localizacao |
| **Sessao JSF** | Navegar paginas, fazer download | JSESSIONID, trf5017e3f72, ViewState |

**IMPORTANTE**: Os cookies de sessao JSF expiram rapidamente (~30 minutos de inatividade).

## Passo a Passo

### 1. Capturar HAR no Firefox

1. Abra o Firefox e acesse o PJE: https://pje1g.trf5.jus.br
2. Faca login com certificado digital
3. Abra o DevTools (F12) → aba Network
4. **Para listagem**: Navegue ate o Painel do Usuario e aguarde carregar
5. **Para download**: Clique em um processo e solicite o download de autos
6. Clique com botao direito na lista de requisicoes → "Save All As HAR"
7. Salve em `~/Downloads/` com nome descritivo (ex: `pje_lista_YYYY-MM-DD.har`)

### 2. Extrair Cookies

```bash
# Combinar HARs de lista e download (recomendado)
python src/auth/extrair_cookies.py \
    --har "~/Downloads/pje_lista.har" "~/Downloads/pje_download.har" \
    --output "data/1_extracao/input/cookies.json"
```

Saida esperada:
```
[INFO] Processando 2 arquivo(s) HAR...
[OK] Cookies essenciais encontrados

[INFO] Cookies encontrados: 3
  - trf5017e3f72
  - dtCookie
  - JSESSIONID

[INFO] Headers encontrados: 3
  - Authorization
  - X-pje-cookies
  - X-pje-usuario-localizacao

[OK] Cookies salvos em: data\1_extracao\input\cookies.json
```

### 3. Listar Processos Conclusos

```bash
# Modo sentenca (padrao)
python src/api/listar_processos.py \
    --cookies "data/1_extracao/input/cookies.json" \
    --modo sentenca \
    --ordem crescente \
    --output "data/1_extracao/input/processos_sentenca.json"

# Modo decisao
python src/api/listar_processos.py \
    --cookies "data/1_extracao/input/cookies.json" \
    --modo decisao \
    --ordem crescente \
    --output "data/1_extracao/input/processos_decisao.json"
```

Saida esperada:
```
[INFO] Modo: SENTENCA
[INFO] Buscando processos da tarefa: Elaboracao de sentenca - Minutar
[INFO] Encontrados 87 processos
[OK] 87 processos salvos em: data\1_extracao\input\processos_sentenca.json
```

### 4. Baixar PDFs

```bash
python src/api/baixar_pdfs.py \
    --cookies "data/1_extracao/input/cookies.json" \
    --processos "data/1_extracao/input/processos_sentenca.json" \
    --output "data/1_extracao/pdfs" \
    --ordem crescente \
    --delay 2.0
```

**IMPORTANTE**: O download requer sessao JSF ativa. Se os cookies expiraram, capture um novo HAR.

### 5. Extrair Texto (Triagem Inteligente)

```bash
python src/processing/extrair_com_triagem.py \
    --pasta "data/1_extracao/pdfs" \
    --output "data/1_extracao/textos" \
    --salvar-triagem
```

## Solucao de Problemas

### Erro 401 na API REST

**Sintoma**: `[ERRO] API retornou status 401`

**Causa**: Token JWT expirado ou headers REST ausentes

**Solucao**:
1. Verifique se o HAR foi capturado na pagina de listagem (nao em pagina estatica)
2. Gere novo HAR navegando no painel do usuario
3. Combine com HAR de download: `--har "lista.har" "download.har"`

### Resposta HTML ao inves de PDF

**Sintoma**: `[ERRO] Formato inesperado: text/html`

**Causa**: Sessao JSF expirada ou ViewState invalido

**Solucao**:
1. Os cookies de sessao JSF expiram em ~30 minutos
2. Capture novo HAR enquanto a sessao esta ativa
3. Execute o download imediatamente apos capturar o HAR

### Pagina de Erro (error.seam)

**Sintoma**: HTML de debug mostra `action="/pje/error.seam"`

**Causa**: Sessao valida mas requisicao mal formada

**Solucao**:
1. O JSESSIONID pode ter sido reciclado
2. Gere novo HAR fazendo um download manual primeiro
3. Use os cookies do HAR de download

## Estrutura de Arquivos

```
data/1_extracao/
├── input/
│   ├── cookies.json          # Cookies e headers extraidos
│   ├── processos_sentenca.json  # Lista de processos (sentenca)
│   └── processos_decisao.json   # Lista de processos (decisao)
├── pdfs/
│   └── {numero_cnj}.pdf      # PDFs baixados
└── textos/
    └── {numero_cnj}.txt      # Textos extraidos
```

## Formato do Arquivo de Cookies

```json
{
  "cookies": {
    "trf5017e3f72": "...",
    "dtCookie": "...",
    "JSESSIONID": "..."
  },
  "headers": {
    "Authorization": "Bearer eyJ...",
    "X-pje-cookies": "...",
    "X-pje-usuario-localizacao": "..."
  },
  "extraido_em": "2025-12-25T17:45:36"
}
```

## Comandos Rapidos

```bash
# Fluxo completo via slash command
/baixar_processos sentenca 10

# Com triagem
/baixar_processos sentenca --com-triagem

# Apenas listar (sem baixar)
/baixar_processos sentenca --apenas-listar

# Forcar Vision API para OCR
/baixar_processos sentenca 5 --vision
```

## Limitacoes Conhecidas

1. **Expiracao rapida**: Cookies JSF expiram em ~30 minutos
2. **Dependencia de navegador**: Requer captura manual de HAR
3. **Rate limiting**: Delay de 2s entre downloads recomendado
4. **Processos volumosos**: PDFs com >400 paginas podem demorar

## Proximos Passos Apos Download

Apos baixar e extrair os textos:

1. **Orquestrar analise completa**:
   ```bash
   /orquestrar {numero_processo}
   ```

2. **Analisar processo individual**:
   ```bash
   /firac {numero_processo}
   /sentenca {numero_processo}
   ```

3. **Verificar status**:
   ```bash
   /status {numero_processo}
   ```

## Historico de Alteracoes

| Data | Alteracao |
|------|-----------|
| 2025-12-25 | Versao inicial do playbook |

---

*Gerado automaticamente pelo Claude Code*
