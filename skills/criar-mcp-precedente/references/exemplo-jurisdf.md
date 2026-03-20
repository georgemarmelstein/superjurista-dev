# Exemplo: JurisDF/TJDFT - API REST

Este documento descreve o padrão de implementação usado no MCP do JurisDF (TJDFT), que usa uma API REST pública com JSON.

## Características do Sistema

| Aspecto | Valor |
|---------|-------|
| URL | https://jurisdf.tjdft.jus.br/api/v1/pesquisa |
| Tecnologia | API REST |
| Autenticação | Pública (sem login) |
| Formato Request | `application/json` |
| Formato Response | JSON |

## Detecção de API REST

Sinais de que um tribunal tem API REST:

```javascript
// No código fonte ou Network tab:
fetch('/api/v1/pesquisa', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: '...' })
})

// Resposta JSON pura:
{
    "registros": [...],
    "hits": { "value": 1234 },
    "agregacoes": {...}
}
```

## Fluxo de Requisição

### 1. Fazer Busca (POST JSON)

```python
JURISDF_API_URL = "https://jurisdf.tjdft.jus.br/api/v1/pesquisa"

HEADERS = {
    "User-Agent": "Mozilla/5.0 ...",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}

async def buscar(query: str, pagina: int = 0, tamanho: int = 20) -> dict:
    """Faz busca na API REST."""
    payload = {
        "query": query,
        "termosAcessorios": [],
        "pagina": pagina,
        "tamanho": tamanho,
        "sinonimos": True,
        "espelho": True,
        "inteiroTeor": False,
        "retornaInteiroTeor": False,
        "retornaTotalizacao": True,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            JURISDF_API_URL,
            json=payload,
            headers=HEADERS,
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()
```

### 2. Estrutura da Resposta

```json
{
    "registros": [
        {
            "uuid": "abc-123-def",
            "processo": "0001234-56.2024.8.07.0000",
            "base": "acordaos",
            "nomeRelator": "Des. Nome Sobrenome",
            "descricaoOrgaoJulgador": "1ª Turma Cível",
            "dataJulgamento": "2024-01-15T00:00:00Z",
            "dataPublicacao": "2024-01-20T00:00:00Z",
            "decisao": "Provido",
            "ementa": "CIVIL. CONSUMIDOR. DANO MORAL..."
        }
    ],
    "hits": {
        "value": 1234
    },
    "agregacoes": {
        "base": [
            { "nome": "acordaos", "total": 800 },
            { "nome": "decisoes-monocraticas", "total": 400 }
        ]
    }
}
```

### 3. Extrair Resultados

```python
def extrair_resultados(data: dict) -> List[Dict]:
    """Extrai resultados do JSON."""
    resultados = []

    for reg in data.get("registros", []):
        resultados.append({
            "numero": reg.get("processo", ""),
            "tipo": reg.get("base", ""),
            "orgao": reg.get("descricaoOrgaoJulgador", ""),
            "relator": reg.get("nomeRelator", ""),
            "data": reg.get("dataJulgamento", ""),
            "ementa": reg.get("ementa", ""),
            "url": f"https://jurisdf.tjdft.jus.br/acordaos/{reg.get('uuid', '')}",
        })

    return resultados
```

## Sintaxe Booleana do JurisDF

| Operador | Sintaxe | Case | Exemplo |
|----------|---------|------|---------|
| AND | E | MAIÚSCULO | furto E estacionamento |
| OR | OU | MAIÚSCULO | supermercado OU hipermercado |
| NOT | NAO | MAIÚSCULO | furto NAO militar |
| Frase exata | "..." | - | "dano moral" |
| Wildcard sufixo | $ | - | bio$ |
| Wildcard prefixo | $ | - | $logia |

### Bases disponíveis

| Código | Nome |
|--------|------|
| acordaos | Acórdãos |
| acordaos-tr | Acórdãos - Turmas Recursais |
| decisoes-monocraticas | Decisões Monocráticas |
| decisoes-presidencia | Decisões da Presidência |
| jurisprudencia-foco | Jurisprudência em Foco |

## Comparação: API REST vs JSF/Scraping

| Aspecto | API REST (JurisDF) | JSF/Scraping (CJF) |
|---------|--------------------|--------------------|
| Complexidade | Baixa | Alta |
| Estabilidade | Alta | Média (IDs mudam) |
| Manutenção | Fácil | Difícil |
| Velocidade | Rápida | Média |
| Sessão | Não necessária | Obrigatória |
| Parsing | JSON direto | Regex em HTML |

## Lições Aprendidas

1. **JSON é direto** - Não precisa de parsing complexo
2. **Sem sessão** - Cada requisição é independente
3. **Paginação simples** - Parâmetros `pagina` e `tamanho`
4. **Agregações úteis** - A API retorna totais por categoria
5. **UUIDs para links** - Usar UUID para construir URL do documento
6. **Usar httpx** - Suporte nativo a async para melhor performance

## Quando Recomendar mcp-builder

Se durante a análise você encontrar uma API REST bem documentada como esta, considere recomendar a skill `mcp-builder` da Anthropic, que é otimizada para APIs REST.

Critérios para recomendar mcp-builder:
- Endpoint retorna JSON puro
- Não precisa de sessão/cookies
- Não tem ViewState ou tokens CSRF
- Documentação Swagger/OpenAPI disponível
