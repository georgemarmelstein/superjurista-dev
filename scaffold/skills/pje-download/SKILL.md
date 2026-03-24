---
name: pje-download
description: Baixa processos do PJE via API REST. Use com /baixar-pje ou /baixar-converter.
context: fork
agent: general-purpose
allowed-tools: Bash, Read, Write
---

# PJE Download

REGRA ABSOLUTA: Execute os scripts existentes. NAO crie codigo novo.

## Captura de Sessao

**Metodo preferido: Bookmarklet** (~5 segundos)
- Instalar: copiar conteudo de `bookmarklet.min.txt` como URL de um favorito no Chrome
- Usar: clicar no favorito quando logado no PJE
- Copiar arquivo baixado: `cp ~/Downloads/pje_session_trf5-1g_*.json pje_session.json`

**Fallback: HAR** (quando bookmarklet nao funciona)
- Usar script `extrair_cookies_har.py` (ver abaixo)

---

## Scripts Disponiveis

| Script | Comando |
|--------|---------|
| Extrair cookies HAR | `python .claude/skills/pje-download/scripts/extrair_cookies_har.py` |
| Listar processos | `python .claude/skills/pje-download/scripts/listar_processos.py` |
| Baixar PDFs completos | `python .claude/skills/pje-download/scripts/baixar_pdfs.py` |
| Baixar por tipo | `python .claude/skills/pje-download/scripts/baixar_por_tipo.py` |
| Listar documentos | `python .claude/skills/pje-download/scripts/listar_documentos.py` |
| Buscar por numero | `python .claude/skills/pje-download/scripts/buscar_processo_por_numero.py` |
| Extrair indice | `python .claude/skills/pje-download/scripts/extrair_indice_completo.py` |
| Baixar por ID | `python .claude/skills/pje-download/scripts/baixar_por_id.py` |

## Comandos Prontos

### Extrair cookies de HAR (fallback)
```bash
python .claude/skills/pje-download/scripts/extrair_cookies_har.py \
  --har ~/Downloads/pje_sessao.har \
  --output pje_session.json
```

### Listar processos de uma fila
```bash
python .claude/skills/pje-download/scripts/listar_processos.py \
  --cookies pje_session.json \
  --modo sentenca \
  --limite 5 \
  --output processos.json
```

### Baixar PDFs completos
```bash
python .claude/skills/pje-download/scripts/baixar_pdfs.py \
  --cookies pje_session.json \
  --processos processos.json \
  --output data/sentenca \
  --delay 2
```

### Download seletivo (processos grandes)
```bash
python .claude/skills/pje-download/scripts/baixar_por_tipo.py \
  --cookies pje_session.json \
  --id-processo ID_AQUI \
  --relevantes \
  --output-dir data/sentenca/NUMERO/tipos/
```

---

## Navegacao Avancada

O script `listar_processos.py` suporta filtros avancados. Para ver todos:

```bash
python .claude/skills/pje-download/scripts/listar_processos.py --help
```

### Filtros Disponiveis

| Filtro | Descricao | Exemplo |
|--------|-----------|---------|
| `--tags` | Filtrar por etiquetas | `--tags URGENTE LIMINAR` |
| `--sem-etiqueta` | Processos sem etiqueta | `--sem-etiqueta` |
| `--prioridade` | Prioritarios (idosos, etc) | `--prioridade` |
| `--sigiloso` | Processos sigilosos | `--sigiloso` |
| `--liminar` | Com pedido de liminar | `--liminar` |
| `--nao-conferidos` | Novos (nao conferidos) | `--nao-conferidos` |
| `--nao-lidos` | Nao lidos | `--nao-lidos` |
| `--polo-ativo` | Nome do autor | `--polo-ativo "JOAO"` |
| `--polo-passivo` | Nome do reu | `--polo-passivo INSS` |
| `--assunto` | Texto no assunto | `--assunto aposentadoria` |
| `--classe` | ID da classe judicial | `--classe 1238` |

### Exemplos de Uso Avancado

**Processos prioritarios de idosos:**
```bash
python listar_processos.py --cookies pje_session.json --modo sentenca --prioridade --limite 10
```

**Processos urgentes com liminar:**
```bash
python listar_processos.py --cookies pje_session.json --modo decisao --tags URGENTE --liminar
```

**Processos contra o INSS:**
```bash
python listar_processos.py --cookies pje_session.json --modo sentenca --polo-passivo INSS
```

**Processos novos nao triados:**
```bash
python listar_processos.py --cookies pje_session.json --modo sentenca --sem-etiqueta --nao-conferidos
```

---

## Retorno Esperado

Retorne APENAS:
- Status de cada etapa (sucesso/erro)
- Caminhos dos arquivos gerados
- Quantidade de processos/documentos
- Erros encontrados (se houver)

NAO inclua:
- Output completo dos scripts
- Logs detalhados
- Conteudo dos arquivos

---

## Documentacao

Para casos de borda e detalhes tecnicos, consulte:
- `references/documentacao-completa.md` - Fluxos e troubleshooting
- `references/pje-estrutura-tarefas.md` - Tarefas disponiveis no PJE
- `references/pje-etiquetas-filtros.md` - Lista completa de filtros
- `references/pje-navegacao-avancada.md` - Receitas de uso avancado
