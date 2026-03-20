# Referencia: Refatoracao de Skills com context: fork

> Data: 2026-01-29
> Versao: 2.7
> Skills afetadas: pje-download, converter-pdf

---

## Contexto

As skills `pje-download` e `converter-pdf` foram refatoradas para resolver dois problemas:

1. **Poluicao de contexto**: Output verboso dos scripts enchia a conversa principal
2. **Modelo "perdido"**: Claude recriava scripts ao inves de usar os existentes

---

## Diagnostico Original

### Problema 1: Skills muito ricas

| Skill | Linhas (antes) | Conteudo |
|-------|----------------|----------|
| pje-download | 318 | 6 passos, 9 casos de borda, 3 exemplos... |
| converter-pdf | 225 | 4 passos, 6 casos de borda, 4 exemplos... |

Quando carregadas, 543 linhas de instrucoes entravam no contexto.

### Problema 2: Commands delegativos

```markdown
## Execucao
Siga os passos da skill `pje-download`
```

O command dizia "siga a skill" mas nao referenciava scripts diretamente.

### Problema 3: Liberdade de interpretacao

O modelo tinha liberdade demais para interpretar as instrucoes, levando a:
- Criacao de scripts novos ao inves de usar existentes
- Demora na execucao
- Comportamento inconsistente

---

## Solucao Implementada

### 1. Skills com context: fork

```yaml
---
name: pje-download
description: Baixa processos do PJE via API REST
context: fork           # NOVO
agent: general-purpose  # NOVO
allowed-tools: Bash Read Write
---
```

### 2. SKILL.md enxuto

**Antes:** 318 linhas com documentacao rica
**Depois:** 71 linhas com comandos literais

### 3. Regra explicita

```markdown
REGRA ABSOLUTA: Execute os scripts existentes. NAO crie codigo novo.
```

### 4. Documentacao movida para references/

```
skill/
├── SKILL.md                          # ENXUTO
└── references/
    └── documentacao-completa.md      # DETALHES
```

### 5. Commands imperativos

```markdown
Executar EXATAMENTE:
```bash
python .claude/skills/pje-download/scripts/listar_processos.py --cookies pje_session.json
```
```

---

## Arquivos Modificados

### Skills

| Arquivo | Acao | Antes | Depois |
|---------|------|-------|--------|
| `pje-download/SKILL.md` | Reescrito | 318 linhas | 71 linhas |
| `pje-download/references/documentacao-completa.md` | Criado | - | 250 linhas |
| `converter-pdf/SKILL.md` | Reescrito | 225 linhas | 70 linhas |
| `converter-pdf/references/documentacao-completa.md` | Criado | - | 180 linhas |

### Commands

| Arquivo | Acao | Mudanca |
|---------|------|---------|
| `baixar-pje.md` | Atualizado | Instrucoes imperativas com bash literal |
| `baixar-converter.md` | Atualizado | Instrucoes imperativas com bash literal |
| `baixar-inteligente.md` | Atualizado | Instrucoes imperativas com bash literal |

### Spec

| Arquivo | Acao | Mudanca |
|---------|------|---------|
| `spec/README.md` | Atualizado | Nova secao "Skills com context: fork" |
| `spec/templates/skill.md` | Atualizado | Campos context e agent |
| `spec/referencias/refatoracao-skills-fork.md` | Criado | Este arquivo |

---

## Estrutura Final

### pje-download

```
.claude/skills/pje-download/
├── SKILL.md                          # 71 linhas, context: fork
├── bookmarklet.js
├── scripts/
│   ├── listar_processos.py
│   ├── baixar_pdfs.py
│   ├── baixar_por_tipo.py
│   ├── baixar_por_id.py
│   ├── listar_documentos.py
│   ├── extrair_indice_completo.py
│   └── buscar_processo_por_numero.py
└── references/
    ├── api-pje.md
    ├── playbook_baixar_processos.md
    └── documentacao-completa.md      # NOVO
```

### converter-pdf

```
.claude/skills/converter-pdf/
├── SKILL.md                          # 70 linhas, context: fork
├── scripts/
│   └── pdf_para_txt.py
└── references/
    └── documentacao-completa.md      # NOVO
```

---

## Padrao de SKILL.md Enxuto

```yaml
---
name: nome-skill
description: Descricao curta
context: fork
agent: general-purpose
allowed-tools: Bash Read Write
---

# Nome da Skill

REGRA ABSOLUTA: Execute os scripts existentes. NAO crie codigo novo.

## Scripts Disponiveis

| Script | Comando |
|--------|---------|
| Nome | `python .claude/skills/.../scripts/nome.py` |

## Comandos Prontos

### Tarefa 1
```bash
python .claude/skills/.../scripts/script.py --arg valor
```

## Retorno Esperado

Retorne APENAS:
- Status (sucesso/erro)
- Caminhos gerados
- Estatisticas

NAO inclua:
- Output completo
- Logs detalhados

## Documentacao

Para detalhes: references/documentacao-completa.md
```

---

## Padrao de Command Imperativo

```markdown
---
description: Descricao do command
argument-hint: [args]
allowed-tools: Bash Read Write
---

# /nome-command

## Argumentos

$1 = primeiro arg
$2 = segundo arg

---

## EXECUCAO OBRIGATORIA

### Etapa 1: Nome

Executar EXATAMENTE:
```bash
python .claude/skills/.../scripts/script.py --arg $1
```

**Checkpoint:** Arquivo existe?

---

### Etapa 2: Nome

Executar EXATAMENTE:
```bash
python .claude/skills/.../scripts/outro.py --arg $2
```

---

### Etapa 3: Relatorio

Informar:
- O que foi feito
- Caminhos gerados
- Proximos passos
```

---

## Beneficios Esperados

1. **Isolamento de contexto**: Output dos scripts fica no sub-agente
2. **Modelo segue instrucoes**: Comandos literais, sem interpretacao
3. **Economia de tokens**: SKILL.md enxuto, documentacao sob demanda
4. **Consistencia**: Mesmo comportamento a cada execucao
5. **Velocidade**: Menos processamento, execucao direta

---

## Validacao

Para verificar se a refatoracao funcionou:

1. Invocar `/baixar-pje 1 sentenca`
2. Observar se:
   - Modelo executa scripts existentes (nao cria novos)
   - Output fica isolado (nao polui conversa)
   - Execucao e mais rapida
   - Comportamento e consistente

---

## Rollback

Se necessario reverter, os arquivos originais estao preservados em:
- Conteudo rico movido para `references/documentacao-completa.md`
- Basta mover de volta para SKILL.md e remover campos context/agent

---

## Referencias

- [Documentacao oficial: Skills](https://docs.anthropic.com/en/docs/claude-code/slash-commands)
- [Documentacao oficial: Sub-agents](https://code.claude.com/docs/en/sub-agents)
- [Framework Super Jurista: README](../README.md)
