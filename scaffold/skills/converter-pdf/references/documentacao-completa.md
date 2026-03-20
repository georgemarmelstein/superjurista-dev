# Documentacao Completa: Converter PDF

> Documentacao de referencia movida do SKILL.md original.
> Consulte este arquivo para detalhes de implementacao, casos de borda e exemplos.

---

## Identidade

**Papel:** Especialista em extracao de texto de PDFs judiciais via OCR, com limpeza de poluicao tipica do sistema PJE.

**Estilo:** Tecnico e orientado a qualidade. Reporta metricas de extracao. Alerta sobre problemas de qualidade.

---

## Proposito

Extrair texto de PDFs de processos judiciais com alta qualidade:
1. OCR como metodo padrao (Tesseract) - melhor para escaneados
2. Extracao digital opcional (--digital) - mais rapida para PDFs nativos
3. Limpeza de poluicao tipica do PJE (rodapes, URLs, assinaturas)
4. Geracao de TXT estruturado com metadados de qualidade

---

## Quando Usar

**USAR quando:**
- Apos baixar processos do PJE (skill pje-download)
- Precisar processar PDFs de processos para analise por LLM
- Converter documentos escaneados em texto pesquisavel
- Comando /baixar-converter solicita conversao

**NAO usar quando:**
- Arquivo ja esta em formato TXT
- PDF nao e de processo judicial

---

## Restricoes

- NAO modificar os PDFs originais
- NAO processar arquivos maiores que 1GB
- SEMPRE preservar estrutura de paginas no output
- SEMPRE incluir metadados de qualidade no cabecalho
- SEMPRE usar UTF-8 com acentos corretos no output
- ALERTAR quando reducao de poluicao > 40%

---

## Argumentos do Script

| Argumento | Obrigatorio | Descricao |
|-----------|-------------|-----------|
| --input | Sim | Diretorio com PDFs ou arquivo individual |
| --output | Nao | Diretorio de saida (padrao: ./textos) |
| --limite | Nao | Quantidade maxima de arquivos (0 = todos) |
| --digital | Nao | Usar extracao digital (pdfplumber) em vez de OCR |

---

## Dependencias

**Python:**
```bash
pip install pdfplumber pdf2image pytesseract
```

**Sistema (OCR):**

Windows:
- Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
  - Incluir idioma portugues (por.traineddata)
- Poppler: https://github.com/oschwartz10612/poppler-windows/releases
  - Adicionar ao PATH ou definir POPPLER_PATH

Linux:
```bash
sudo apt install tesseract-ocr tesseract-ocr-por poppler-utils
```

---

## Metodos de Extracao

| Metodo | Quando Usar | Vantagens |
|--------|-------------|-----------|
| OCR (Tesseract) | Padrao - documentos escaneados | Unico para imagens |
| pdfplumber | --digital - PDFs nativos | Mais rapido |

**Por que OCR como padrao?**
Processos judiciais frequentemente contem:
- Peticoes escaneadas
- Documentos anexados (RG, contracheques, laudos)
- Procuracoes assinadas manualmente
- Certidoes e oficios digitalizados

A extracao digital falha silenciosamente nesses casos.

---

## Metricas de Qualidade

| Metrica | Descricao | Valor Tipico |
|---------|-----------|--------------|
| Paginas | Total processadas | Varia |
| Caracteres bruto | Antes da limpeza | Varia |
| Caracteres limpo | Apos limpeza | Varia |
| Reducao | % de poluicao removida | 15-25% |

Uma reducao > 40% pode indicar problema na extracao.

---

## Casos de Borda

| Problema | Causa | Solucao |
|----------|-------|---------|
| Texto vazio | Tesseract nao instalado | Instalar Tesseract OCR |
| Caracteres estranhos | Encoding errado | Verificar idioma do Tesseract |
| OCR muito lento | Muitas paginas | Processar em lotes menores |
| Tesseract nao encontrado | Path incorreto | Verificar instalacao e PATH |
| Poppler error | Windows sem Poppler | Instalar Poppler |
| Reducao > 40% | Extracao problematica | Verificar PDF original |

---

## Estrutura de Saida

Cada arquivo TXT gerado inclui cabecalho com metadados:

```
# Texto Extraido de Processo Judicial
# Arquivo origem: 0807674-42.2015.4.05.8100.pdf
# Data extracao: 2026-01-19T10:30:00
# Metodo: OCR (Tesseract)
# Paginas: 45
# Caracteres (bruto): 125000
# Caracteres (limpo): 98000
# Reducao: 21.6%

============================================================
[PAGINA 1]
============================================================

PODER JUDICIARIO
JUSTICA FEDERAL DE PRIMEIRA INSTANCIA
...
```

---

## Exemplos de Uso

### OCR (padrao)
```bash
python .claude/skills/converter-pdf/scripts/pdf_para_txt.py \
  --input data/sentenca/0807674-42.2015.4.05.8100/0807674-42.2015.4.05.8100.pdf \
  --output data/sentenca/0807674-42.2015.4.05.8100/
```

### Extracao rapida (PDFs digitais)
```bash
python .claude/skills/converter-pdf/scripts/pdf_para_txt.py \
  --input documento_digital.pdf \
  --output ./textos \
  --digital
```

### Processamento em lote
```bash
python .claude/skills/converter-pdf/scripts/pdf_para_txt.py \
  --input data/sentenca/ \
  --output data/sentenca/ \
  --limite 10
```
