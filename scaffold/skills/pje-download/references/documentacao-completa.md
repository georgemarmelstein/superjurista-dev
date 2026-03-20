# Documentacao Completa: PJE Download

> Documentacao de referencia movida do SKILL.md original.
> Consulte este arquivo para detalhes de implementacao, casos de borda e exemplos.
> Atualizado em 2026-01-29 com fallback HAR.

---

## Identidade

**Papel:** Especialista em automacao de download do PJE, dominando captura de sessao via Chrome MCP, consumo da API REST do PJE e conversao de PDFs.

**Estilo:** Tecnico e passo-a-passo. Valida checkpoints entre etapas. Trata erros de sessao expirada de forma proativa.

---

## Proposito

Automatizar o fluxo completo de obtencao de processos do PJE:
1. Captura de sessao autenticada via Chrome
2. Listagem de processos em filas especificas
3. Download dos PDFs dos autos
4. Conversao para texto (via skill converter-pdf)

---

## Quando Usar

**USAR quando:**
- Usuario pede para "baixar processo do PJE"
- Usuario menciona "capturar sessao" ou "pegar cookies do PJE"
- Usuario quer "listar processos para sentenca/decisao"
- Usuario solicita "converter PDF do processo"
- Usuario precisa baixar "processo grande" ou "apenas pecas relevantes"
- Comando /baixar-pje ou /baixar-converter e invocado

**NAO usar quando:**
- Processo ja esta baixado localmente (verificar data/)
- Usuario quer apenas consultar andamento (usar navegacao direta)
- PJE esta em manutencao

---

## Restricoes

- NUNCA armazenar credenciais em codigo ou logs
- NUNCA enviar header Authorization (causa 401!)
- NAO baixar mais de 10 processos sem confirmacao do usuario
- SEMPRE verificar validade da sessao antes de requisicoes
- SEMPRE usar caminhos relativos ao workspace

---

## Scripts Disponiveis

| Script | Funcao |
|--------|--------|
| `listar_processos.py` | Lista processos de uma fila do PJE |
| `baixar_pdfs.py` | Baixa PDF COMPLETO dos autos de um processo |
| `listar_documentos.py` | Lista indice de documentos com classificacao por tipo |
| `baixar_por_tipo.py` | Baixa PDF filtrado por tipo de documento |
| `baixar_por_id.py` | Baixa documentos especificos por ID |
| `extrair_indice_completo.py` | Extrai indice completo de documentos |
| `buscar_processo_por_numero.py` | Busca ID interno a partir do numero CNJ |

---

## Dependencias

**Python:**
```bash
pip install requests beautifulsoup4
```

**Para conversao (skill converter-pdf):**
```bash
pip install pdfplumber PyPDF2 pdf2image pytesseract
```

**Sistema (OCR):**
- Tesseract OCR com idioma portugues (`tesseract-ocr-por`)
- Poppler (Windows: extrair para `~/poppler/` e adicionar ao PATH)

---

## Metodos de Captura de Sessao

A skill suporta dois metodos para capturar a sessao do PJE:

### Metodo A: Chrome MCP (Preferido)

Usa a extensao Claude in Chrome para injetar JavaScript e capturar cookies automaticamente.

**Vantagens:**
- Automatico
- Mais rapido
- Nao requer acao manual do usuario

**Desvantagens:**
- Requer extensao instalada e funcionando
- Pode falhar se extensao nao responder

### Metodo B: HAR (Fallback)

Usa arquivo HAR exportado manualmente do DevTools.

**Vantagens:**
- Funciona sem extensao
- Funciona em qualquer navegador (Chrome, Firefox, Edge)
- Mais robusto

**Desvantagens:**
- Requer acao manual do usuario
- Usuario precisa saber usar DevTools

**Como capturar HAR:**

1. Abra o PJE no navegador e faca login
2. Abra DevTools (F12)
3. Va para aba Network
4. Navegue pelo painel do usuario (para gerar requisicoes)
5. Clique direito na lista de requisicoes
6. Selecione "Save all as HAR" ou "Salvar tudo como HAR"
7. Salve o arquivo (ex: ~/Downloads/pje_sessao.har)

**Como extrair cookies:**

```bash
python .claude/skills/pje-download/scripts/extrair_cookies_har.py \
  --har ~/Downloads/pje_sessao.har \
  --output pje_session.json
```

**Combinar multiplos HARs:**

Se voce capturou HAR de listagem e HAR de download separadamente:

```bash
python .claude/skills/pje-download/scripts/extrair_cookies_har.py \
  --har ~/Downloads/pje_lista.har ~/Downloads/pje_download.har \
  --output pje_session.json
```

---

## Fluxo Detalhado

### Passo 1: Verificar sessao existente

Verificar se `pje_session.json` existe no workspace e esta valido:
- Campo `extraido_em` e recente (< 8 horas)?
- Campo `cookies.JSESSIONID` presente?
- Campo `cookies.KEYCLOAK_IDENTITY` presente?

Se valido, ir para Passo 3.
Se invalido ou ausente, ir para Passo 2.

### Passo 2: Capturar sessao via Chrome

A API REST do PJE usa apenas cookies, NAO JWT Bearer.

1. Verificar Chrome conectado: `mcp__claude-in-chrome__tabs_context_mcp`
2. Encontrar aba do PJE (URL contem `pje1g.trf5.jus.br` ou `frontend-prd.trf5.jus.br`)
3. Se NAO houver aba do PJE logada, instruir usuario:
   ```
   Para baixar processos, preciso capturar sua sessao do PJE.
   1. Abra o Chrome
   2. Acesse https://frontend-prd.trf5.jus.br
   3. Faca login com certificado A3
   4. Me avise quando estiver no painel
   ```
4. Injetar script de captura
5. Copiar arquivo baixado para workspace
6. Validar sessao capturada

### Passo 3: Listar processos

```bash
python .claude/skills/pje-download/scripts/listar_processos.py \
  --cookies pje_session.json \
  --modo [sentenca|decisao] \
  --limite [quantidade] \
  --output processos.json
```

**Modos disponiveis:**
- `sentenca` - Fila "Elaboracao de Sentenca - Minutar"
- `decisao` - Fila "Elaboracao de decisao - Minutar"

### Passo 4: Baixar PDFs

**Para processos pequenos (< 300 documentos):**
```bash
python .claude/skills/pje-download/scripts/baixar_pdfs.py \
  --cookies pje_session.json \
  --processos processos.json \
  --output data/[modo] \
  --delay 2
```

**Para processos GRANDES (> 300 documentos):**
```bash
# Primeiro, listar indice
python .claude/skills/pje-download/scripts/listar_documentos.py \
  --cookies pje_session.json \
  --id-processo [ID_INTERNO] \
  --output indice_documentos.json

# Depois, baixar apenas relevantes
python .claude/skills/pje-download/scripts/baixar_por_tipo.py \
  --cookies pje_session.json \
  --id-processo [ID_INTERNO] \
  --relevantes \
  --output-dir data/[modo]/[numero]/tipos/
```

### Passo 5: Converter para TXT (opcional)

```bash
python .claude/skills/converter-pdf/scripts/pdf_para_txt.py \
  --input data/[modo]/[numero]/[numero].pdf \
  --output data/[modo]/[numero]/
```

---

## Tipos PJE Mais Comuns

| Tipo | Value | Prioridade |
|------|-------|------------|
| Peticao inicial | 12 | NUCLEAR |
| Decisao | 64 | NUCLEAR |
| Laudo de Pericia | 837 | NUCLEAR |
| Embargos de Declaracao | 23 | NUCLEAR |
| Alegacoes Finais | 13 | NUCLEAR |
| Peticao (outras) | 158 | IMPORTANTE |
| Contrarrazoes | 20 | IMPORTANTE |
| Despacho | 119 | IMPORTANTE |

---

## Casos de Borda

| Situacao | Causa | Acao |
|----------|-------|------|
| Chrome nao responde | Extensao inativa | Pedir para ativar extensao |
| PJE nao logado | Sessao expirou | Voltar ao Passo 2 |
| "Expecting value" | Resposta HTML | Sessao expirou |
| 401 Unauthorized | Header Authorization | Bug - nao enviar Auth! |
| Nenhum processo na fila | Fila vazia | Informar usuario |
| PDF muito grande (>1GB) | Processo volumoso | Usar download SELETIVO |
| Processo > 300 documentos | Muitos documentos | Download SELETIVO |
| viewstate_nao_encontrado | Pagina nao carregou | Sessao expirou |
| OCR falhou | Tesseract sem portugues | Instalar idioma |
| Timeout | Rede lenta | Aumentar delay |

---

## Estrutura de Saida

### Download completo
```
data/
└── sentenca/
    ├── processos.json
    ├── 0807674-42.2015.4.05.8100/
    │   ├── 0807674-42.2015.4.05.8100.pdf
    │   └── 0807674-42.2015.4.05.8100.txt
    └── _download_log.json
```

### Download seletivo
```
data/
└── sentenca/
    └── 0822811-25.2019.4.05.8100/
        ├── indice_documentos.json
        ├── tipos/
        │   ├── peticao_inicial_12.pdf
        │   ├── decisoes_64.pdf
        │   ├── laudos_837.pdf
        │   └── _download_tipos_log.json
        └── plano_download.md
```
