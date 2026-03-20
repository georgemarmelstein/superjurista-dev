# Template: Team Manifest v1.0

> **Propósito:** Registro compartilhado de execução de Agent Team
> **Criado por:** Orquestrador na Etapa 0
> **Atualizado por:** Orquestrador após cada etapa paralela
> **Lido por:** Agents downstream para descobrir inputs disponíveis

---

## Uso

### Criação (Etapa 0 do Orquestrador)

```bash
# Criar pasta inputs e manifest
mkdir -p $WORKSPACE/inputs

# Criar manifest inicial
cat > $WORKSPACE/_team_manifest.md << 'EOF'
[conteúdo do template abaixo]
EOF
```

### Atualização (Após cada Team)

O orquestrador atualiza a tabela de teammates e a lista de artefatos após cada execução paralela.

### Leitura (Agent Downstream)

```python
# Pseudocódigo
manifest = Read("$WORKSPACE/_team_manifest.md")
inputs_disponiveis = [linha for linha in manifest if linha.startswith("- [x]")]
```

---

## Template

```markdown
# Team Manifest: Processo $NUMERO

## Metadata

| Campo | Valor |
|-------|-------|
| **Processo** | $NUMERO |
| **Pipeline** | $PIPELINE_NAME |
| **Workspace** | $WORKSPACE |
| **Iniciado** | $TIMESTAMP |
| **Status** | em_andamento / concluído / erro |

---

## Teams Executados

### TEAM Pesquisa (Etapa 2.5)

| # | Teammate | Status | Output | Timestamp |
|---|----------|--------|--------|-----------|
| 1 | pesquisador-bnp | pendente / em_progresso / concluído / erro | - | - |
| 2 | pesquisador-cjf | pendente | - | - |
| 3 | pesquisador-julia | pendente | - | - |

**Resultado:** 0/3 concluídos

### TEAM Verificação (Etapa 3.5)

| # | Teammate | Status | Output | Timestamp |
|---|----------|--------|--------|-----------|
| 1 | verificador-honorarios | pendente | - | - |
| 2 | verificador-calculos | pendente | - | - |
| 3 | verificador-remessa | pendente | - | - |

**Resultado:** 0/3 concluídos

---

## Artefatos Disponíveis

> Checklist de arquivos gerados. Agents downstream usam esta lista
> para descobrir quais inputs opcionais estão disponíveis.

### Etapas Sequenciais
- [ ] processo.txt
- [ ] $NUMERO-linha-tempo.md
- [ ] $NUMERO-relatorio.md
- [ ] $NUMERO-analise.md
- [ ] $NUMERO-fundamentacao.md
- [ ] $NUMERO-sentenca.md

### TEAM Pesquisa (inputs/pesquisa-*.md)
- [ ] inputs/pesquisa-bnp.md
- [ ] inputs/pesquisa-cjf.md
- [ ] inputs/pesquisa-julia.md

### TEAM Verificação (inputs/verificacao-*.md)
- [ ] inputs/verificacao-honorarios.md
- [ ] inputs/verificacao-calculos.md
- [ ] inputs/verificacao-remessa.md

---

## Alertas e Warnings

> Mensagens importantes dos teammates para revisão humana
> ou para agents downstream considerarem.

| Timestamp | Teammate | Tipo | Mensagem |
|-----------|----------|------|----------|
| - | - | - | Nenhum alerta registrado |

---

## Histórico de Execução

| Timestamp | Etapa | Ação | Resultado |
|-----------|-------|------|-----------|
| $TIMESTAMP | 0 | Preparação | Manifest criado |

---

Manifest atualizado: $TIMESTAMP
```

---

## Campos Explicados

### Metadata

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| Processo | Número do processo judicial | 0814624-28.2019.4.05.8100 |
| Pipeline | Nome do orquestrador | pipeline-sentenca-team |
| Workspace | Caminho absoluto do diretório | data/sentenca/0814624-28.2019.4.05.8100 |
| Iniciado | Timestamp de início | 2026-02-07T10:30:00 |
| Status | Estado global do pipeline | em_andamento |

### Status de Teammate

| Status | Significado |
|--------|-------------|
| `pendente` | Ainda não executado |
| `em_progresso` | Task disparado, aguardando |
| `concluído` | Output gerado com sucesso |
| `erro` | Falhou após tentativas |
| `pulado` | Intencionalmente não executado |

### Artefatos

- `[ ]` = Pendente ou não existe
- `[x]` = Disponível para leitura

### Alertas

| Tipo | Significado |
|------|-------------|
| `INFO` | Informação útil |
| `AVISO` | Pode impactar resultado |
| `ERRO` | Problema que precisa atenção |
| `CRÍTICO` | Impede continuação normal |

---

## Exemplo Preenchido

```markdown
# Team Manifest: Processo 0814624-28.2019.4.05.8100

## Metadata

| Campo | Valor |
|-------|-------|
| **Processo** | 0814624-28.2019.4.05.8100 |
| **Pipeline** | pipeline-sentenca-team |
| **Workspace** | data/sentenca/0814624-28.2019.4.05.8100 |
| **Iniciado** | 2026-02-07T10:30:00 |
| **Status** | em_andamento |

---

## Teams Executados

### TEAM Pesquisa (Etapa 2.5)

| # | Teammate | Status | Output | Timestamp |
|---|----------|--------|--------|-----------|
| 1 | pesquisador-bnp | concluído | inputs/pesquisa-bnp.md | 10:31:22 |
| 2 | pesquisador-cjf | concluído | inputs/pesquisa-cjf.md | 10:31:45 |
| 3 | pesquisador-julia | erro | - | 10:32:10 |

**Resultado:** 2/3 concluídos

### TEAM Verificação (Etapa 3.5)

| # | Teammate | Status | Output | Timestamp |
|---|----------|--------|--------|-----------|
| 1 | verificador-honorarios | concluído | inputs/verificacao-honorarios.md | 10:45:12 |
| 2 | verificador-calculos | concluído | inputs/verificacao-calculos.md | 10:45:30 |
| 3 | verificador-remessa | concluído | inputs/verificacao-remessa.md | 10:45:08 |

**Resultado:** 3/3 concluídos

---

## Artefatos Disponíveis

### Etapas Sequenciais
- [x] processo.txt
- [x] 0814624-linha-tempo.md
- [x] 0814624-relatorio.md
- [x] 0814624-analise.md
- [ ] 0814624-fundamentacao.md
- [ ] 0814624-sentenca.md

### TEAM Pesquisa (inputs/pesquisa-*.md)
- [x] inputs/pesquisa-bnp.md
- [x] inputs/pesquisa-cjf.md
- [ ] inputs/pesquisa-julia.md

### TEAM Verificação (inputs/verificacao-*.md)
- [x] inputs/verificacao-honorarios.md
- [x] inputs/verificacao-calculos.md
- [x] inputs/verificacao-remessa.md

---

## Alertas e Warnings

| Timestamp | Teammate | Tipo | Mensagem |
|-----------|----------|------|----------|
| 10:32:10 | pesquisador-julia | ERRO | MCP julia-trf5 não respondeu após 2 tentativas |
| 10:45:12 | verificador-honorarios | AVISO | Percentual de honorários acima do usual (18%) |
| 10:45:08 | verificador-remessa | INFO | Remessa necessária dispensada (valor inferior a 1000 SM) |

---

## Histórico de Execução

| Timestamp | Etapa | Ação | Resultado |
|-----------|-------|------|-----------|
| 10:30:00 | 0 | Preparação | Manifest criado |
| 10:30:15 | 1 | Linha do Tempo | Concluído |
| 10:30:45 | 2 | Relatório | Concluído |
| 10:31:00 | 2.5 | TEAM Pesquisa | 2/3 concluídos |
| 10:35:00 | 3 | Análise | Concluído (com inputs de 2 pesquisas) |
| 10:45:00 | 3.5 | TEAM Verificação | 3/3 concluídos |
| 10:50:00 | 4 | Fundamentação | Em progresso |

---

Manifest atualizado: 2026-02-07T10:50:00
```

---

## Validação do Manifest

### Checklist de Conformidade

| # | Item | Obrigatório |
|---|------|-------------|
| 1 | Seção Metadata com todos os campos | SIM |
| 2 | Pelo menos 1 Team listado | SIM |
| 3 | Tabela de teammates com colunas corretas | SIM |
| 4 | Lista de artefatos com checklist | SIM |
| 5 | Timestamp de última atualização | SIM |
| 6 | Seção de alertas (mesmo que vazia) | NÃO |
| 7 | Histórico de execução | NÃO |

---

**Template:** Team Manifest
**Versão:** 1.0
**Framework:** Super Jurista v2.8
