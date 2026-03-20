---
description: Baixa processos do PJE e converte para TXT
argument-hint: [quantidade] [modo: sentenca|decisao]
allowed-tools: Bash, Read, Write, mcp__claude-in-chrome__*
---

# /baixar-converter

Baixa processos do PJE E converte para TXT.

## Argumentos

```
$1 = quantidade (padrao: 1)
$2 = modo (padrao: sentenca)
```

---

## EXECUCAO OBRIGATORIA

### Etapa 1: Capturar sessao (CONTEXTO ISOLADO)

Usar skill `capturar-sessao-pje` que roda em contexto isolado:

```
Invocar skill: capturar-sessao-pje
```

A skill tenta Chrome MCP primeiro, e se falhar, pede HAR ao usuario.

**Checkpoint:** Arquivo `pje_session.json` existe?

Se a skill retornar falha, PARAR e informar usuario

---

### Etapa 2: Listar processos

Executar EXATAMENTE:
```bash
python .claude/skills/pje-download/scripts/listar_processos.py --cookies pje_session.json --modo $2 --limite $1 --output processos.json
```

**Checkpoint:** Arquivo `processos.json` existe e contem processos?

Se erro "Expecting value" → Sessao expirou, voltar a Etapa 1.

---

### Etapa 3: Baixar PDFs

Executar EXATAMENTE:
```bash
python .claude/skills/pje-download/scripts/baixar_pdfs.py --cookies pje_session.json --processos processos.json --output data/$2 --delay 2
```

**Checkpoint:** PDFs baixados em `data/$2/`?

---

### Etapa 4: Converter para TXT

Para CADA processo baixado, executar EXATAMENTE:
```bash
python .claude/skills/converter-pdf/scripts/pdf_para_txt.py --input data/$2/[NUMERO]/[NUMERO].pdf --output data/$2/[NUMERO]/
```

Substituir [NUMERO] pelo numero real do processo.

**Checkpoint:** Arquivos .txt gerados?

---

### Etapa 5: Relatorio

Informar:
- Quantidade de processos baixados
- Quantidade de PDFs convertidos
- Caminhos dos arquivos
- Estatisticas de conversao (paginas, caracteres)

---

## Saida Esperada

```
data/[modo]/
├── processos.json
├── _download_log.json
└── [numero-processo]/
    ├── [numero].pdf
    ├── [numero].txt
    └── conversao_log.json
```
