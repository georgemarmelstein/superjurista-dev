# Navegacao Avancada no PJE

Este documento contem receitas praticas para casos de uso comuns na navegacao do PJE.

## Casos de Uso

### 1. Priorizar processos de idosos/doentes graves

Processos com prioridade legal (idosos 60+, doentes graves, etc).

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo sentenca \
  --prioridade \
  --ordem crescente \
  --limite 10 \
  --output prioritários.json
```

**Logica:** Processos mais antigos primeiro (ordem crescente), com prioridade.

---

### 2. Tutelas de urgencia (liminares)

Processos com pedido de tutela provisoria.

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo decisao \
  --tags LIMINAR \
  --limite 5 \
  --output liminares.json
```

**Nota:** A etiqueta LIMINAR deve existir no sistema. Verificar nome exato.

---

### 3. Processos novos (não conferidos)

Processos que acabaram de chegar na fila.

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo sentenca \
  --nao-conferidos \
  --limite 20 \
  --output novos.json
```

**Logica:** `conferidos: false` filtra processos ainda não visualizados.

---

### 4. Materia previdenciaria

Processos de uma classe ou assunto específico.

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo sentenca \
  --assunto "aposentadoria" \
  --limite 15 \
  --output previdenciarios.json
```

**Variantes:**
- `--assunto "auxilio-doenca"` - Beneficios por incapacidade
- `--assunto "pensao"` - Pensao por morte
- `--assunto "BPC"` - Beneficio de Prestacao Continuada

---

### 5. Processos contra INSS

Filtrar por polo passivo.

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo sentenca \
  --polo-passivo "INSS" \
  --limite 20 \
  --output inss.json
```

---

### 6. Processos sem etiqueta (não triados)

Processos que ainda não foram classificados.

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo sentenca \
  --sem-etiqueta \
  --limite 30 \
  --output nao_triados.json
```

**Uso:** Identificar processos que precisam de triagem inicial.

---

### 7. Processos sigilosos

Processos com restricao de acesso.

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo sentenca \
  --sigiloso \
  --output sigilosos.json
```

**Cuidado:** Tratamento especial para sigilo.

---

### 8. Combinacao: Urgentes + Prioritarios + Novos

Triagem inteligente para despacho imediato.

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo decisao \
  --tags URGENTE \
  --prioridade \
  --nao-lidos \
  --limite 5 \
  --output despacho_imediato.json
```

**Logica:** Urgente E Prioritario E Nao lido = Atencao maxima.

---

### 9. Processos de autor específico

Buscar todos os processos de uma parte.

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo sentenca \
  --polo-ativo "MARIA DA SILVA" \
  --output processos_maria.json
```

**Nota:** Nome deve ser exato (case-insensitive).

---

### 10. Processos para pauta de julgamento

Processos marcados para sessao.

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo sentenca \
  --tags PAUTA \
  --output pauta.json
```

---

## Combinacoes Uteis

| Cenario | Filtros |
|---------|---------|
| Triagem matinal | `--nao-lidos --limite 20` |
| Despachos urgentes | `--prioridade --tags URGENTE` |
| Mutirao de sentencas | `--sem-etiqueta --limite 50` |
| Revisao de conferidos | `--conferidos --limite 10` |
| Processos volumosos | Usar `baixar_por_tipo.py --relevantes` |

---

## Fluxo de Trabalho Sugerido

### 1. Inicio do dia

```bash
# Ver novos processos
python listar_processos.py --cookies pje_session.json --modo decisao --nao-lidos --limite 10

# Ver urgentes
python listar_processos.py --cookies pje_session.json --modo decisao --tags URGENTE --limite 5
```

### 2. Producao de sentencas

```bash
# Listar por ordem de antiguidade
python listar_processos.py --cookies pje_session.json --modo sentenca --ordem crescente --limite 10

# Baixar PDFs
python baixar_pdfs.py --cookies pje_session.json --processos processos_sentenca.json --output data/sentenca
```

### 3. Fim do dia

```bash
# Ver o que ficou pendente
python listar_processos.py --cookies pje_session.json --modo sentenca --nao-conferidos
```

---

## Troubleshooting

### Etiqueta não encontrada

```
[OK] 0 processos salvos
```

**Causa:** Etiqueta não existe ou nome diferente.
**Solucao:** Verificar nome exato no PJE (case-sensitive).

### Muitos processos

```
[OK] 300 processos salvos (limite da API)
```

**Causa:** Mais de 300 processos na fila.
**Solucao:** Adicionar filtros ou usar `--limite`.

### Sessao expirada

```
[ERRO] Nenhum processo encontrado
```

**Causa:** Cookie JSESSIONID expirou (~30 min).
**Solucao:** Executar `/baixar-pje` novamente para renovar sessao.

---

## Referencias

- `pje-estrutura-tarefas.md` - Tarefas disponíveis
- `pje-etiquetas-filtros.md` - Lista completa de filtros
- `documentacao-completa.md` - Fluxos detalhados
