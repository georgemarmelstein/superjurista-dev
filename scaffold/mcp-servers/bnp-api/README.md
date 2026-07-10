# MCP Server: BNP/CNJ - Banco Nacional de Precedentes

Servidor MCP standalone para busca de precedentes qualificados no Banco Nacional de Precedentes (BNP) do CNJ.

## Fonte de Dados

- **Portal**: https://bnp.pdpj.jus.br
- **API**: https://pangeabnp.pdpj.jus.br/api/v1
- **Backend**: Flask + OpenSearch (gunicorn)
- **Sem autenticacao**: A API publica nao exige login

## Instalacao

```bash
cd .claude/mcp-servers/bnp-api
pip install -r requirements.txt
```

## Registro (.mcp.json do projeto, com caminho absoluto)

Adicione ao `.mcp.json` na raiz do projeto (o `/instalar-superjurista` faz isso
automaticamente; servidor novo so carrega em sessao nova):

```json
{
  "mcpServers": {
    "bnp-api": {
      "command": "python",
      "args": ["<RAIZ_DO_PROJETO>/.claude/mcp-servers/bnp-api/server.py"]
    }
  }
}
```

## Tools Disponiveis

### 1. `buscar_precedentes`

Busca precedentes qualificados. Retorna XML estruturado.

**Parametros:**
| Parametro | Tipo | Default | Descricao |
|-----------|------|---------|-----------|
| busca | str | (obrigatorio) | Query com sintaxe OpenSearch |
| max_resultados | int | 10 | Resultados por pagina (1-50) |
| orgaos | list[str] | todos | Filtro por tribunais |
| tipos | list[str] | todos | Filtro por especie |
| pagina | int | 1 | Pagina (1-based) |

### 2. `gerar_relatorio_precedentes`

Busca e gera relatorio Markdown formatado.

**Parametros:** Mesmos de `buscar_precedentes` (sem pagina).

### 3. `listar_filtros_bnp`

Lista tribunais, especies e operadores disponiveis (consulta API /parametros).

## Sintaxe de Busca

O BNP usa OpenSearch (derivado do ElasticSearch). Operadores:

| Operador | Sintaxe | Exemplo |
|----------|---------|---------|
| Obrigatorio | +termo | +aposentadoria +especial |
| Exclusao | -termo | previdenciario -militar |
| Frase exata | "frase" | "pensao por morte" |
| OR implicito | termo1 termo2 | bpc loas |

## Filtros por Tribunal

**Superiores:** STF, STJ, TST, STM, TNU
**TRFs:** TRF01 a TRF06
**TJs:** TJAC a TJTO (27 tribunais)
**TRTs:** TRT01 a TRT24
**TJMs:** TJMMG, TJMRS, TJMSP

**Grupos (atalho):** "superiores", "trfs", "tjs", "trts"

## Filtros por Especie

| Sigla | Descricao |
|-------|-----------|
| SUM | Sumula |
| SV | Sumula Vinculante |
| RG | Tema de Repercussao Geral |
| RR | Recurso Especial Repetitivo |
| IAC | Incidente de Assuncao de Competencia |
| IRDR | Incidente de Resolucao de Demandas Repetitivas |
| IRR | Incidente de Recurso Repetitivo |
| SIRDR | Suspensao Nacional em IRDR |
| CT | Controversia |
| PUIL | Pedido de Uniformizacao de Lei |
| OJ | Orientacao Jurisprudencial |

## Exemplos de Uso

```
buscar_precedentes(busca='"pensao por morte"', orgaos=["STJ"], tipos=["RR","SUM"])
buscar_precedentes(busca="+aposentadoria +especial", orgaos=["superiores"])
gerar_relatorio_precedentes(busca="dano moral consumidor", tipos=["SUM","SV"])
listar_filtros_bnp()
```

## Estrutura da Resposta (XML)

```xml
<precedentes_bnp total="275">
  <precedente indice="1">
    <id>stf-rg-503</id>
    <tipo>RG</tipo>
    <numero>503</numero>
    <orgao>STF</orgao>
    <situacao>Ha repercussao geral</situacao>
    <ultima_atualizacao>07/11/2025</ultima_atualizacao>
    <questao>Definir se...</questao>
    <tese>No ambito do RGPS...</tese>
    <processos_paradigma>
      <processo numero="0001234..." link="https://..." />
    </processos_paradigma>
    <suspensao ativa="true" data="23/09/2024">Processos em segunda instancia</suspensao>
  </precedente>
</precedentes_bnp>
```

## Descoberta da API

API descoberta via engenharia reversa do frontend Angular 16:
1. `env.js` → URLs de configuracao
2. Chunk 27 (lazy-loaded PesquisaModule) → contrato da API
3. HAR capture → body exato e headers CORS obrigatorios
4. `GET /api/v1/parametros` → filtros disponiveis

