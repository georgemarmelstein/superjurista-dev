# Estrutura de Tarefas e Filas do PJE TRF5

Este documento mapeia as tarefas disponíveis no PJE TRF5 e seus identificadores para uso via API.

## Tarefas por Categoria

### Elaboracao de Minutas (Magistrado/Assessor)

| Nome da Tarefa | Modo | Identificador API |
|----------------|------|-------------------|
| Elaboracao de sentenca - Minutar | sentenca | Elabora%C3%A7%C3%A3o%20de%20senten%C3%A7a%20-%20Minutar |
| Elaboracao de decisao - Minutar | decisao | Elabora%C3%A7%C3%A3o%20de%20decis%C3%A3o%20-%20Minutar |
| Minutar Despacho | despacho | Minutar%20Despacho |
| Assinar Acordao | acordao | Assinar%20Ac%C3%B3rd%C3%A3o |

### Conferencia e Assinatura

| Nome da Tarefa | Descrição |
|----------------|-----------|
| Conferir Minuta | Magistrado confere minuta elaborada |
| Assinar Documento | Assinatura digital do magistrado |
| Liberar Documento | Liberacao para publicacao |

### Gestao de Audiencias

| Nome da Tarefa | Descrição |
|----------------|-----------|
| Designar ou administrar audiencia | Agendamento e gestao de audiencias |
| Preparar ata de audiencia | Elaboracao de ata pos-audiencia |

### Comunicacoes Processuais

| Nome da Tarefa | Descrição |
|----------------|-----------|
| Preparar comunicacao | Intimacoes, citacoes, notificacoes |
| Expedir comunicacao | Envio via correio ou eletronico |

### Analise Processual

| Nome da Tarefa | Descrição |
|----------------|-----------|
| Analisar processo | Triagem e classificacao |
| Verificar pendencias | Checagem de requisitos |
| Arquivar processo | Encerramento |

## Mapeamento para listar_processos.py

O script `listar_processos.py` suporta dois modos principais:

```python
TAREFAS = {
    'sentenca': "Elaboracao de sentenca - Minutar",
    'decisao': "Elaboracao de decisao - Minutar"
}
```

Para adicionar novos modos, editar o dicionario TAREFAS no script.

## Estrutura de Resposta da API

A API retorna processos com os seguintes campos relevantes:

```json
{
  "idProcesso": 12345678,
  "numeroProcesso": "0814624-28.2019.4.05.8100",
  "classeJudicial": "Acao Ordinaria",
  "assunto": "Aposentadoria por Idade",
  "poloAtivo": "JOAO DA SILVA",
  "poloPassivo": "INSS",
  "dataChegada": 1704067200000,
  "prioridade": true,
  "sigiloso": false,
  "etiquetas": ["URGENTE", "LIMINAR"],
  "nomeTarefa": "Elaboracao de sentenca - Minutar"
}
```

## Fluxo Tipico de Tarefas

```
1. Processo chega na fila
   |
   v
2. Triagem (Analisar processo)
   |
   v
3. Conclusao para minutar
   |
   v
4. Elaboracao da minuta (sentenca/decisao/despacho)
   |
   v
5. Conferencia pelo magistrado
   |
   v
6. Assinatura digital
   |
   v
7. Publicacao/Comunicacao
```

## Referencia Rapida

### Baixar processos para sentenca

```bash
python listar_processos.py --cookies pje_session.json --modo sentenca --limite 10
```

### Baixar processos para decisao

```bash
python listar_processos.py --cookies pje_session.json --modo decisao --limite 10
```

### Filtrar por prioridade

```bash
python listar_processos.py --cookies pje_session.json --modo sentenca --prioridade
```
