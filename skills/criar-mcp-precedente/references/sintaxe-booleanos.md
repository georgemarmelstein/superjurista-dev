# Guia de Descoberta de Sintaxe Booleana

Este documento descreve o processo sistemático para descobrir a sintaxe booleana de um tribunal.

## Visão Geral do Processo

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Buscar documentação oficial (WebSearch)                  │
│    → Se encontrar: extrair e validar                        │
│    → Se não: ir para testes empíricos                       │
├─────────────────────────────────────────────────────────────┤
│ 2. Executar testes empíricos sistemáticos                   │
│    → Testar cada categoria de operador                      │
│    → Comparar contagem de resultados                        │
├─────────────────────────────────────────────────────────────┤
│ 3. Analisar resultados e inferir sintaxe                    │
│    → Determinar case sensitivity                            │
│    → Identificar operadores suportados                      │
├─────────────────────────────────────────────────────────────┤
│ 4. Gerar tabela de operadores para docstring                │
└─────────────────────────────────────────────────────────────┘
```

## Fase 1: Buscar Documentação

### Queries de busca

```
site:[tribunal].jus.br operadores busca
site:[tribunal].jus.br manual pesquisa jurisprudência
site:[tribunal].jus.br sintaxe busca avançada
site:[tribunal].jus.br ajuda pesquisa
site:[tribunal].jus.br "como pesquisar"
```

### O que procurar

- Tabelas de operadores
- Exemplos de queries
- Páginas de "Ajuda" ou "Como pesquisar"
- Manuais em PDF

## Fase 2: Testes Empíricos

### Query base

Escolher um termo comum com muitos resultados:
- `aposentadoria` (previdenciário)
- `contrato` (cível)
- `furto` (criminal)
- `servidor` (administrativo)

### Matriz de testes

#### 2.1 Operador AND

| Variação | Query de teste |
|----------|----------------|
| Português MAIÚSCULO | `aposentadoria E invalidez` |
| Português minúsculo | `aposentadoria e invalidez` |
| Inglês MAIÚSCULO | `aposentadoria AND invalidez` |
| Inglês minúsculo | `aposentadoria and invalidez` |
| Símbolo + | `aposentadoria +invalidez` |
| Implícito (espaço) | `aposentadoria invalidez` |

#### 2.2 Operador OR

| Variação | Query de teste |
|----------|----------------|
| Português MAIÚSCULO | `aposentadoria OU pensão` |
| Português minúsculo | `aposentadoria ou pensão` |
| Inglês MAIÚSCULO | `aposentadoria OR pensão` |
| Inglês minúsculo | `aposentadoria or pensão` |
| Símbolo \| | `aposentadoria \| pensão` |
| Símbolo \|\| | `aposentadoria \|\| pensão` |

#### 2.3 Operador NOT

| Variação | Query de teste |
|----------|----------------|
| Português MAIÚSCULO | `servidor NAO militar` |
| Português minúsculo | `servidor nao militar` |
| Inglês MAIÚSCULO | `servidor NOT militar` |
| Inglês minúsculo | `servidor not militar` |
| Símbolo - | `servidor -militar` |
| Símbolo ! | `servidor !militar` |

#### 2.4 Frase Exata

| Variação | Query de teste |
|----------|----------------|
| Aspas duplas | `"pensão por morte"` |
| Aspas simples | `'pensão por morte'` |
| Sem aspas (controle) | `pensão por morte` |

#### 2.5 Hífen / Palavras Compostas

| Variação | Query de teste |
|----------|----------------|
| Com hífen | `auxílio-doença` |
| Com aspas | `"auxílio-doença"` |
| Sem hífen | `auxílio doença` |
| Separado com AND | `auxílio E doença` |

#### 2.6 Wildcard

| Variação | Query de teste |
|----------|----------------|
| $ sufixo | `aposentad$` |
| * sufixo | `aposentad*` |
| $ prefixo | `$doença` |
| * prefixo | `*doença` |
| $ ambos | `$pensão$` |
| ? (um char) | `MA??` |

#### 2.7 Proximidade

| Variação | Query de teste |
|----------|----------------|
| ADJ MAIÚSCULO | `processo ADJ administrativo` |
| adj minúsculo | `processo adj administrativo` |
| PROX MAIÚSCULO | `processo PROX administrativo` |
| prox minúsculo | `processo prox administrativo` |
| NEAR | `processo NEAR administrativo` |
| Com distância | `processo ADJ5 administrativo` |
| Com barra | `processo PROX/3 administrativo` |

## Fase 3: Análise de Resultados

### Lógica de interpretação

```python
def analisar_resultado(query: str, contagem: int, contagem_base: int) -> str:
    """
    Analisa resultado de um teste de operador.

    Args:
        query: Query testada
        contagem: Número de resultados
        contagem_base: Resultados da query base (termo simples)

    Returns:
        Interpretação do resultado
    """
    if contagem == 0:
        return "NAO_FUNCIONA"  # Operador não reconhecido ou erro
    elif contagem == contagem_base:
        return "IGNORADO"  # Operador tratado como texto literal
    elif contagem < contagem_base:
        return "FUNCIONA_RESTRITIVO"  # AND, NOT funcionando
    else:  # contagem > contagem_base
        return "FUNCIONA_EXPANSIVO"  # OR funcionando
```

### Exemplo de análise

```
Query base: "aposentadoria" → 5000 resultados

Teste AND:
- "aposentadoria E invalidez"   → 150 resultados  ✓ FUNCIONA (restritivo)
- "aposentadoria e invalidez"   → 0 resultados    ✗ NAO_FUNCIONA
- "aposentadoria AND invalidez" → 5000 resultados ✗ IGNORADO (AND virou texto)

Conclusão: AND = "E" MAIÚSCULO
```

### Determinar case sensitivity

```
Se "E" funciona e "e" não funciona:
    → Case SENSITIVE, usar MAIÚSCULO

Se "E" e "e" funcionam igual:
    → Case INSENSITIVE, documentar ambos

Se "e" funciona e "E" não funciona:
    → Case SENSITIVE, usar minúsculo (raro, mas JULIA usa)
```

## Fase 4: Gerar Documentação

### Template de tabela

```markdown
## Sintaxe de Busca - [TRIBUNAL]

| Operador    | Sintaxe   | Case       | Exemplo                              |
|-------------|-----------|------------|--------------------------------------|
| AND         | [valor]   | [case]     | [exemplo]                            |
| OR          | [valor]   | [case]     | [exemplo]                            |
| NOT         | [valor]   | [case]     | [exemplo]                            |
| Frase exata | [valor]   | -          | [exemplo]                            |
| Hífen       | [comportamento] | -     | [exemplo]                            |
| Wildcard    | [valor]   | [posição]  | [exemplo] → [expansão]               |
| Proximidade | [valor]   | [case]     | [exemplo]                            |
```

### Exemplo preenchido (CJF)

```markdown
## Sintaxe de Busca - CJF

| Operador    | Sintaxe   | Case       | Exemplo                              |
|-------------|-----------|------------|--------------------------------------|
| AND         | E         | MAIÚSCULO  | pensão E morte                       |
| OR          | OU        | MAIÚSCULO  | bpc OU loas                          |
| NOT         | NAO       | MAIÚSCULO  | servidor NAO militar                 |
| XOR         | XOU       | MAIÚSCULO  | pensão XOU aposentadoria             |
| Frase exata | "..."     | -          | "pensão por morte"                   |
| Hífen       | preservar | -          | auxílio-doença                       |
| Wildcard    | $         | sufixo     | aposentad$ → aposentadoria, aposentado|
| Wildcard    | $         | prefixo    | $doença → auxílio-doença             |
| Adjacente   | ADJ[n]    | MAIÚSCULO  | Repartição ADJ Pública               |
| Próximo     | PROX[n]   | MAIÚSCULO  | aposentadoria PROX3 invalidez        |
```

### Exemplo preenchido (JULIA - minúsculo)

```markdown
## Sintaxe de Busca - JULIA/TRF5

| Operador    | Sintaxe   | Case       | Exemplo                              |
|-------------|-----------|------------|--------------------------------------|
| AND         | e         | minúsculo  | pensão e morte                       |
| OR          | ou        | minúsculo  | bpc ou loas                          |
| NOT         | nao       | minúsculo  | servidor nao militar                 |
| Frase exata | "..."     | -          | "pensão por morte"                   |
| Hífen       | preservar | -          | auxílio-doença                       |
| Wildcard    | $         | sufixo     | aposentad$ → aposentadoria, aposentado|
| Adjacente   | adj       | minúsculo  | processo adj físico                  |
| Próximo     | prox      | minúsculo  | auxílio prox doença                  |
```

## Operadores Especiais por Tribunal

### Campos específicos (CJF)

Alguns tribunais permitem busca em campos específicos:

```
termo[CAMPO]

Campos comuns:
- [EMEN] - Ementa
- [DECI] - Decisão
- [REL]  - Relator
- [TRIB] - Tribunal
```

Testar: `aposentadoria[EMEN]` vs `aposentadoria`

### Operadores de proximidade

Variações encontradas:

| Tribunal | Adjacente | Próximo | Com distância |
|----------|-----------|---------|---------------|
| CJF | ADJ | PROX | ADJ5, PROX3 |
| JULIA | adj | prox | Distância fixa (5) |
| Alguns TJs | NEAR | - | NEAR/5 |

### Operadores de escopo

Alguns tribunais têm operadores de escopo:

| Operador | Significado | Exemplo |
|----------|-------------|---------|
| COM | Mesma sentença | pensão COM dependente |
| MESMO | Mesmo parágrafo | benefício MESMO previdenciário |
| PAR | Mesmo parágrafo | termo1 PAR termo2 |

## Checklist Final

Antes de finalizar a documentação, verificar:

- [ ] AND testado (MAIÚSCULO e minúsculo)
- [ ] OR testado (MAIÚSCULO e minúsculo)
- [ ] NOT testado (MAIÚSCULO e minúsculo)
- [ ] Frase exata testada (aspas duplas e simples)
- [ ] Hífen testado (com e sem aspas)
- [ ] Wildcard sufixo testado ($ e *)
- [ ] Wildcard prefixo testado ($ e *)
- [ ] Proximidade testada (ADJ, PROX, variações)
- [ ] Case sensitivity determinada para cada operador
- [ ] Tabela gerada com exemplos reais
- [ ] Exemplos de queries complexas documentados
