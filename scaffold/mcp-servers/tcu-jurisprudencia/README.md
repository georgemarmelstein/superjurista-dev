# MCP TCU Jurisprudencia

Servidor MCP para acesso a jurisprudencia do Tribunal de Contas da Uniao (TCU).

## Instalacao

```bash
cd .claude/mcp-servers/tcu-jurisprudencia
pip install -r requirements.txt
```

## Registro no .mcp.json (raiz do projeto)

Adicionar ao `.mcp.json` na raiz do projeto, com caminho ABSOLUTO — o `/instalar-superjurista`
faz este registro automaticamente. NAO usar settings.json (padrao antigo, falha
silenciosamente). Servidor novo so carrega em sessao nova.

```json
{
  "mcpServers": {
    "tcu-jurisprudencia": {
      "command": "python",
      "args": ["<RAIZ_DO_PROJETO>/.claude/mcp-servers/tcu-jurisprudencia/server.py"]
    }
  }
}
```

## Tools Disponiveis

### buscar_tcu

Busca jurisprudencia retornando XML estruturado.

**Parametros:**
- `busca`: Query com sintaxe do TCU
- `base`: Base de dados (acordao-completo, jurisprudencia-selecionada, sumula, norma)
- `max_resultados`: Maximo de resultados (1-100)
- `sinonimos`: Expandir busca com sinonimos (true/false)

### gerar_relatorio_tcu

Busca e gera relatorio formatado em Markdown.

**Parametros:**
- `busca`: Query com sintaxe do TCU
- `base`: Base de dados
- `max_resultados`: Maximo de resultados (1-50)

### listar_bases_tcu

Lista bases disponiveis e operadores de busca.

## Sintaxe de Busca

O TCU usa operadores em **minusculo**, diferente de outros tribunais.

### Operadores Booleanos

| Operador | Descricao                  | Exemplo                    |
|----------|----------------------------|----------------------------|
| e        | Ambos termos obrigatorios  | licitacao e fraude         |
| ou       | Qualquer um dos termos     | pregao ou concorrencia     |
| nao      | Exclui o segundo termo     | contrato nao emergencial   |

### Operadores de Proximidade

| Operador | Descricao                     | Exemplo                |
|----------|-------------------------------|------------------------|
| adj      | Adjacentes NA ordem           | tomada adj contas      |
| prox     | Proximos QUALQUER ordem       | dano prox erario       |
| mesmo    | No mesmo PARAGRAFO            | multa mesmo gestor     |

### Wildcards e Frase Exata

| Operador | Descricao               | Exemplo                        |
|----------|-------------------------|--------------------------------|
| $        | Qualquer sufixo         | aposentad$ -> aposentadoria    |
| "..."    | Frase exata             | "tomada de contas especial"    |

## Bases de Dados

| Base                       | Descricao                                           |
|----------------------------|-----------------------------------------------------|
| acordao-completo           | Todos os acordaos com inteiro teor (padrao)         |
| jurisprudencia-selecionada | Ementas e sumulas organizadas por tema              |
| norma                      | Normativos internos (Portarias, Resolucoes)         |

**Nota:** As sumulas do TCU estao incluidas na base `jurisprudencia-selecionada`.

## Exemplos de Queries

```
# Licitacao e fraude em pregao
licitacao e fraude e "pregao eletronico"

# Tomada de contas especial com dano ao erario
"tomada de contas especial" e (dano ou prejuizo) e erario

# Servidor com acumulacao ilicita (exceto cargo)
servidor e acumulacao nao cargo

# Aposentadoria por invalidez (usando wildcard)
aposentad$ prox invalidez

# Contrato administrativo por inexigibilidade
contrato adj administrativo e inexigibilidade
```

## Temas Comuns no TCU

- Licitacoes e contratos administrativos
- Tomada de contas especial
- Responsabilizacao de gestores publicos
- Convenios e transferencias voluntarias
- Pessoal e aposentadoria
- Obras publicas e engenharia
- Controle interno e auditoria

## Fontes

- [Portal TCU - Pesquisa Textual](https://pesquisa.apps.tcu.gov.br/)
- [Guia Rapido de Pesquisa](https://portal.tcu.gov.br/pesquisa-de-jurisprudencia-guia-rapido.htm)
