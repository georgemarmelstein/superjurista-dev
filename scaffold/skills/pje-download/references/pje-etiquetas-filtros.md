# Sistema de Etiquetas e Filtros do PJE

Este documento descreve o sistema de etiquetas e todos os filtros disponíveis na API do PJE.

## Etiquetas (Tags)

### O que sao

Etiquetas sao marcadores personalizados que serventuários e magistrados criam para organizar processos. Sao compartilhadas dentro do orgao julgador.

### Etiquetas Comuns

| Etiqueta | Uso Tipico |
|----------|------------|
| URGENTE | Processos que precisam de atencao imediata |
| LIMINAR | Pedidos de tutela provisoria |
| PRIORIDADE | Idosos, doentes graves, etc |
| PERICIA | Aguardando ou com laudo pericial |
| PAUTA | Incluido em pauta de julgamento |
| REVISAR | Precisa de revisao |
| COMPLEXO | Materia ou volume complexo |
| PRECEDENTE | Tema com precedente vinculante |

### Como usar etiquetas na API

```python
# Processos COM etiquetas especificas
payload = {
    "tags": ["URGENTE", "LIMINAR"],  # Lista de etiquetas
    ...
}

# Processos SEM nenhuma etiqueta
payload = {
    "semEtiqueta": True,
    ...
}
```

## Filtros Disponiveis na API

A API do PJE aceita diversos filtros no payload da requisicao.

### Filtros de Identificacao

| Filtro | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| númeroProcesso | string | Numero CNJ completo | "0814624-28.2019.4.05.8100" |
| classe | int | ID da classe judicial | 1238 |
| assunto | string | Texto no assunto | "aposentadoria" |
| competencia | string | Codigo da competencia | "1" |

### Filtros de Partes

| Filtro | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| poloAtivo | string | Nome do autor | "JOAO SILVA" |
| poloPassivo | string | Nome do reu | "INSS" |
| nomeParte | string | Qualquer polo | "MARIA" |
| cpfCnpj | string | CPF/CNPJ da parte | "12345678900" |

### Filtros de Etiquetas

| Filtro | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| tags | array | Etiquetas a incluir | ["URGENTE"] |
| tagsString | string | Etiquetas separadas por virgula | "URGENTE,LIMINAR" |
| semEtiqueta | bool | Sem nenhuma etiqueta | true |
| somenteFavoritas | bool | Etiquetas favoritadas | true |
| somenteComTodasTags | bool | Todas as tags devem estar presentes | true |

### Filtros de Status

| Filtro | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| prioridadeProcesso | bool | Processos prioritários | true |
| sigiloso | bool | Processos sigilosos | true |
| conferidos | bool | Ja conferidos | true/false |
| naoLidos | bool | Nao lidos pelo usuario | true |

### Filtros Especiais

| Filtro | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| somenteLiminar | bool | Com liminar | true |
| somenteLembrete | bool | Com lembrete | true |
| eleicao | bool | Materia eleitoral | true |

### Filtros de Organizacao

| Filtro | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| orgao | int | ID do orgao | 123 |
| orgaoJulgador | int | ID do orgao julgador | 456 |
| orgaoJulgadorColegiado | int | ID do colegiado | 789 |
| relator | int | ID do relator | 100 |

### Filtros de Paginacao

| Filtro | Tipo | Descrição | Exemplo |
|--------|------|-----------|---------|
| page | int | Numero da pagina (0-based) | 0 |
| maxResults | int | Quantidade maxima | 300 |
| ordem | string | Campo de ordenacao | "dataChegada" |

## Uso no Script listar_processos.py

### Argumentos CLI disponíveis

```bash
python listar_processos.py --help

Opcoes:
  --cookies, -c    Arquivo de cookies (obrigatorio)
  --modo, -m       sentenca ou decisao (padrao: sentenca)
  --limite, -l     Quantidade maxima (padrao: todos)
  --ordem          crescente ou decrescente (padrao: crescente)
  --output, -o     Arquivo de saida
  --verbose, -v    Output detalhado

Filtros (a implementar):
  --tags           Filtrar por etiquetas
  --sem-etiqueta   Apenas sem etiqueta
  --prioridade     Apenas prioritários
  --sigiloso       Apenas sigilosos
  --nao-conferidos Apenas não conferidos
  --nao-lidos      Apenas não lidos
  --polo-ativo     Filtrar por autor
  --polo-passivo   Filtrar por reu
  --classe         Filtrar por ID da classe
  --assunto        Filtrar por texto no assunto
```

### Exemplos de Uso

#### Processos prioritários de idosos

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo sentenca \
  --prioridade \
  --limite 10
```

#### Processos com etiqueta LIMINAR

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo decisao \
  --tags LIMINAR \
  --limite 5
```

#### Processos não conferidos (novos)

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo sentenca \
  --nao-conferidos
```

#### Processos de autor específico

```bash
python listar_processos.py \
  --cookies pje_session.json \
  --modo sentenca \
  --polo-ativo "MARIA SILVA"
```

## Payload Completo da API

```json
{
  "numeroProcesso": "",
  "classe": null,
  "tags": [],
  "tagsString": null,
  "poloAtivo": null,
  "poloPassivo": null,
  "orgao": null,
  "ordem": null,
  "page": 0,
  "maxResults": 300,
  "idTaskInstance": null,
  "apelidoSessao": null,
  "idTipoSessao": null,
  "dataSessao": null,
  "somenteFavoritas": null,
  "objeto": null,
  "semEtiqueta": null,
  "assunto": null,
  "dataAutuacao": null,
  "nomeParte": null,
  "nomeFiltro": null,
  "numeroDocumento": null,
  "competencia": "",
  "relator": null,
  "orgaoJulgador": null,
  "somenteLembrete": null,
  "somenteSigiloso": null,
  "somenteLiminar": null,
  "eleicao": null,
  "estado": null,
  "municipio": null,
  "prioridadeProcesso": null,
  "cpfCnpj": null,
  "porEtiqueta": null,
  "conferidos": null,
  "orgaoJulgadorColegiado": null,
  "naoLidos": null,
  "tipoProcessoDocumento": null,
  "somenteComTodasTags": null
}
```

## Notas Importantes

1. **Etiquetas sao case-sensitive**: "URGENTE" != "urgente"
2. **Filtros null sao ignorados**: Nao precisa enviar todos
3. **maxResults maximo**: 300 por requisicao
4. **Tags vazias**: `tags: []` não filtra por etiquetas
5. **Combinacao de filtros**: Todos os filtros sao AND (conjuncao)
