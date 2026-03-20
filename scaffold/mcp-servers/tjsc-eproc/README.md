# MCP Server: TJSC eProc - Jurisprudencia

Servidor MCP para busca de jurisprudencia no **Tribunal de Justica de Santa Catarina (TJSC)** via sistema eProc.

Referencia: Tutorial de Pesquisa da Jurisprudencia TJSC (atualizado 06/10/2025)

## Instalacao

```bash
cd .claude/mcp-servers/tjsc-eproc
pip install -r requirements.txt
```

## Configuracao no settings.json

Adicionar ao arquivo `.claude/settings.json` do projeto ou `~/.claude/settings.json` global:

```json
{
  "mcpServers": {
    "tjsc-eproc": {
      "command": "python",
      "args": [".claude/mcp-servers/tjsc-eproc/server.py"],
      "cwd": "."
    }
  }
}
```

## Tools Disponiveis

| Tool | Descricao | Retorno |
|------|-----------|---------|
| `buscar_tjsc` | Busca jurisprudencia com filtros | XML estruturado |
| `gerar_relatorio_tjsc` | Busca e gera relatorio | Markdown formatado |
| `listar_filtros_tjsc` | Lista filtros e operadores | XML com opcoes |

## Sintaxe de Busca

A busca e **case-insensitive** e **acentos sao ignorados** (buscar "acao" encontra "acao").

| Operador | Sintaxe | Exemplo |
|----------|---------|---------|
| AND | (espaco implicito) | `pensao morte` |
| OR | `ou` | `bpc ou loas` |
| NOT | `nao` ou `não` | `servidor nao militar` |
| Frase exata | `"..."` | `"pensao por morte"` |
| Wildcard sufixo | `*` | `aposentad*` |
| Wildcard prefixo | `*` | `*doenca` |
| Proximidade | `prox` | `contrato prox administrativo` |

### Notas sobre operadores

- AND e implicito: termos separados por espaco sao buscados juntos
- `nao` funciona com ou sem acento (`nao` e `não`)
- `*` funciona tanto como sufixo (`aposentad*`) quanto prefixo (`*doenca`)
- `prox` localiza termos proximos em qualquer ordem

## Filtros Disponiveis

### Grupo Base

#### Origem
| Codigo | Descricao |
|--------|-----------|
| `tjsc` | Tribunal de Justica de SC |
| `turmas_recursais` | Turmas Recursais |
| `turmas_uniformizacao` | Turmas de Uniformizacao |
| `conselho_magistratura` | Conselho da Magistratura |

#### Tipo de Documento
| Codigo | Descricao |
|--------|-----------|
| `acordaos` | Acordaos do TJ |
| `decisoes_monocraticas` | Decisoes Monocraticas do TJ |
| `despachos_vice` | Despachos/Decisoes da Vice-Presidencia |

#### Campo de Busca
| Codigo | Descricao |
|--------|-----------|
| `I` | Inteiro Teor (padrao) |
| `E` | Ementa |
| `CE` | Caput da Ementa |

#### Opcoes Booleanas
| Parametro | Descricao |
|-----------|-----------|
| `jurisprudencia_selecionada` | Apenas precedentes relevantes selecionados pelo TJSC |
| `agrupar_resultados` | Agrupa resultados semelhantes (mesma relatoria/classe/ementa), exibe o mais atual |

#### Ordenacao
| Codigo | Descricao |
|--------|-----------|
| `1` | Mais recentes (padrao) |
| `2` | Mais antigos |

### Campos Especificos (Pesquisa Avancada)

| Parametro | Descricao |
|-----------|-----------|
| `processo` | Numero do processo (formato CNJ ou apenas digitos) |
| `classe_processual` | Classe processual para restringir busca |
| `orgao_julgador` | Orgao julgador (colegiado) |
| `relator` | Nome do Relator/Relatora |
| `data_inicio` / `data_fim` | Data decisao/julgamento (DD/MM/AAAA) |
| `data_publicacao_inicio` / `data_publicacao_fim` | Data disponibilizacao/publicacao (DD/MM/AAAA) |

## Exemplos de Uso

```
# Busca simples
buscar_tjsc(busca="pensao por morte")

# Busca com frase exata e filtro
buscar_tjsc(busca='"dano moral" ou "dano material"', tipo_documento="acordaos")

# Busca com wildcard e data
buscar_tjsc(busca="aposentad* nao reforma*", data_inicio="01/01/2024")

# Apenas precedentes relevantes
buscar_tjsc(busca="responsabilidade civil", jurisprudencia_selecionada=True)

# Agrupar resultados semelhantes
buscar_tjsc(busca="dano moral", agrupar_resultados=True)

# Filtrar por orgao julgador
buscar_tjsc(busca="contrato", orgao_julgador="1a Camara de Direito Civil")

# Relatorio formatado
gerar_relatorio_tjsc(busca='"responsabilidade civil"', max_resultados=10)
```

## Detalhes Tecnicos

- **Endpoint publico**: Nao requer autenticacao
- **Encoding**: ISO-8859-1 (Latin-1)
- **Paginacao**: AJAX com cookies de sessao (gerenciado automaticamente)
- **Limite**: 100 resultados por busca (paginacao automatica)
- **Timeout**: 30 segundos por requisicao
- **Portal web**: https://www.tjsc.jus.br/web/jurisprudencia

## Referencia

Tutorial oficial: `references/tutorial-jurisprudencia-tjsc-2025.pdf`
