---
name: converter-pdf
description: Converte PDFs judiciais para TXT via OCR. Use com /baixar-converter.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Write
---

# Converter PDF para Texto

REGRA ABSOLUTA: Execute o script existente. NAO crie codigo novo.

## Script

```bash
python .claude/skills/converter-pdf/scripts/pdf_para_txt.py \
  --input CAMINHO_PDF \
  --output DIRETORIO_SAIDA
```

## Argumentos

| Argumento | Obrigatorio | Descricao |
|-----------|-------------|-----------|
| `--input` | Sim | Arquivo PDF ou diretorio |
| `--output` | Nao | Diretorio de saida (padrao: ./textos) |
| `--limite` | Nao | Maximo de arquivos (0 = todos) |
| `--digital` | Nao | Usar pdfplumber ao inves de OCR |

## Exemplos

### Converter um PDF
```bash
python .claude/skills/converter-pdf/scripts/pdf_para_txt.py \
  --input data/sentenca/0807674-42.2015.4.05.8100/0807674-42.2015.4.05.8100.pdf \
  --output data/sentenca/0807674-42.2015.4.05.8100/
```

### Converter em lote
```bash
python .claude/skills/converter-pdf/scripts/pdf_para_txt.py \
  --input data/sentenca/ \
  --output data/sentenca/ \
  --limite 10
```

### PDF digital (mais rapido)
```bash
python .claude/skills/converter-pdf/scripts/pdf_para_txt.py \
  --input documento.pdf \
  --output ./textos \
  --digital
```

## Retorno Esperado

Retorne APENAS:
- Status (sucesso/erro)
- Caminho do arquivo TXT gerado
- Estatisticas resumidas (paginas, caracteres, reducao %)

NAO inclua:
- Output completo do script
- Conteudo do texto extraido

## Documentacao

Para casos de borda e detalhes tecnicos, consulte:
`references/documentacao-completa.md`
