---
description: Pipeline inteligente - baixa processo especifico com selecao por LLM
argument-hint: <numero-processo> [--merge] [--converter]
allowed-tools: Bash, Read, Write, mcp__claude-in-chrome__*, Task
---

# /baixar-inteligente

Pipeline de download inteligente de processos do PJE com selecao por LLM.

## Argumentos

```
$ARGUMENTS = <numero-processo> [--merge] [--converter]

Flags opcionais:
  --merge      Junta todos os PDFs em arquivo unico
  --converter  Converte para TXT (requer --merge)

Exemplos:
  /baixar-inteligente 0822811-25.2019.4.05.8100
  /baixar-inteligente 0822811-25.2019.4.05.8100 --merge
  /baixar-inteligente 0822811-25.2019.4.05.8100 --merge --converter
```

---

## EXECUCAO OBRIGATORIA

### Etapa 0: Parse de argumentos

```python
args = "$ARGUMENTS".split()
NUMERO_PROCESSO = args[0]
FLAG_MERGE = "--merge" in args
FLAG_CONVERTER = "--converter" in args

if FLAG_CONVERTER and not FLAG_MERGE:
    FLAG_MERGE = True  # Ativa automaticamente

WORKSPACE = f"data/sentenca/{NUMERO_PROCESSO}"
```

Criar diretorio:
```bash
mkdir -p data/sentenca/NUMERO_PROCESSO
```

---

### Etapa 1: Verificar/Capturar sessao PJE (CONTEXTO ISOLADO)

Verificar se `pje_session.json` existe e e recente (< 8 horas).

Se invalido, usar skill `capturar-sessao-pje` que roda em contexto isolado:

```
Invocar skill: capturar-sessao-pje
```

A skill tenta Chrome MCP primeiro, e se falhar, pede HAR ao usuario.

**Checkpoint:** Arquivo `pje_session.json` existe?

---

### Etapa 2: Identificar ID do processo

Executar EXATAMENTE:
```bash
python .claude/skills/pje-download/scripts/buscar_processo_por_numero.py --cookies pje_session.json --numero NUMERO_PROCESSO
```

Capturar o ID_PROCESSO retornado.

---

### Etapa 3: Extrair indice completo

Executar EXATAMENTE:
```bash
python .claude/skills/pje-download/scripts/extrair_indice_completo.py --cookies pje_session.json --id-processo ID_PROCESSO --output WORKSPACE/indice_completo.json
```

**Checkpoint:** Arquivo contem lista de documentos?

---

### Etapa 4: Selecao inteligente (Task tool)

Usar Task tool para spawnar agente seletor:

```
Task tool:
  subagent_type: general-purpose
  prompt: |
    Leia o indice em WORKSPACE/indice_completo.json

    Aplique a heuristica "mentalidade de juiz":
    - NUCLEAR: Sempre incluir (peticao inicial, sentenca, laudo, embargos)
    - SUBSTANTIVO: Analisar descricao (parecer, manifestacao)
    - TEMPORAL: Incluir se recente (ultimos 6 meses)
    - EXCLUIR: So com certeza absoluta

    REGRA DE OURO: Na duvida, inclua.

    Salve a selecao em WORKSPACE/selecao_documentos.json
```

---

### Etapa 5: Download por ID

Executar EXATAMENTE:
```bash
python .claude/skills/pje-download/scripts/baixar_por_id.py --cookies pje_session.json --id-processo ID_PROCESSO --ids-file WORKSPACE/selecao_documentos.json --output-dir WORKSPACE/documentos/
```

---

### Etapa 6: Merge dos PDFs (se --merge)

PULAR se FLAG_MERGE = False

Executar script Python inline:
```python
from PyPDF2 import PdfMerger
from pathlib import Path

merger = PdfMerger()
pdf_dir = Path("WORKSPACE/documentos/")

pdfs = sorted(pdf_dir.glob("*.pdf"), key=lambda p: int(p.stem.split("_")[0]))

for pdf in pdfs:
    if not pdf.name.startswith("_"):
        merger.append(str(pdf))

merger.write("WORKSPACE/NUMERO_PROCESSO.pdf")
merger.close()
```

---

### Etapa 7: Conversao para TXT (se --converter)

PULAR se FLAG_CONVERTER = False

Executar EXATAMENTE:
```bash
python .claude/skills/converter-pdf/scripts/pdf_para_txt.py --input WORKSPACE/NUMERO_PROCESSO.pdf --output WORKSPACE/
```

---

### Etapa 8: Relatorio final

Informar baseado nas flags:

**Sempre:**
- Total de documentos no processo
- Total selecionados pelo LLM
- Total baixados com sucesso
- Caminhos dos arquivos

**Se --merge:**
- Tamanho do PDF merged em MB
- Arquivo: `NUMERO_PROCESSO.pdf`

**Se --converter:**
- Tamanho do TXT em KB
- Arquivo: `NUMERO_PROCESSO.txt`

---

## Saida por Modo

### Sem flags (PDFs separados)
```
WORKSPACE/
├── indice_completo.json
├── selecao_documentos.json
└── documentos/
    ├── 116090996_manifestacao_perito.pdf
    └── _download_por_id_log.json
```

### Com --merge
```
WORKSPACE/
├── ...
└── NUMERO_PROCESSO.pdf
```

### Com --merge --converter
```
WORKSPACE/
├── ...
├── NUMERO_PROCESSO.pdf
└── NUMERO_PROCESSO.txt
```
