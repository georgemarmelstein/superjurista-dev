---
titulo: Guia de Analise de HAR para PJE
---

# Guia de Analise de HAR para PJE

## O que e um arquivo HAR?

HAR (HTTP Archive) e um formato JSON que registra todas as requisicoes HTTP feitas pelo navegador. Contem:

- URLs requisitadas
- Headers enviados e recebidos
- Cookies
- Corpo das requisicoes e respostas
- Tempos de carregamento

## Estrutura do HAR

```json
{
  "log": {
    "version": "1.2",
    "creator": { "name": "Firefox", "version": "..." },
    "entries": [
      {
        "startedDateTime": "2026-01-29T10:00:00.000Z",
        "request": {
          "method": "GET",
          "url": "https://pje1g.trf5.jus.br/pje/...",
          "headers": [...],
          "cookies": [...]
        },
        "response": {
          "status": 200,
          "headers": [...],
          "content": { "mimeType": "application/json", ... }
        }
      }
    ]
  }
}
```

## Passo a Passo: Extrair Informacoes

### 1. Identificar BASE_URL

Filtrar requisicoes que contem `/pje/`:

```python
import json

with open('pje.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

urls = set()
for entry in har['log']['entries']:
    url = entry['request']['url']
    if '/pje/' in url:
        # Extrair dominio
        from urllib.parse import urlparse
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        urls.add(base)

print("URLs encontradas:")
for url in urls:
    print(f"  - {url}")
```

### 2. Mapear Cookies

Listar todos os cookies unicos:

```python
cookies = {}
for entry in har['log']['entries']:
    for cookie in entry['request'].get('cookies', []):
        name = cookie['name']
        if name not in cookies:
            cookies[name] = {
                'valor_exemplo': cookie['value'][:20] + '...',
                'ocorrencias': 0
            }
        cookies[name]['ocorrencias'] += 1

print("Cookies encontrados:")
for name, info in sorted(cookies.items(), key=lambda x: -x[1]['ocorrencias']):
    print(f"  {name}: {info['ocorrencias']} ocorrencias")
```

**Cookies obrigatorios** sao aqueles que aparecem em TODAS as requisicoes bem-sucedidas.

### 3. Identificar Headers Especificos

Filtrar headers que comecam com `X-`:

```python
headers_custom = {}
for entry in har['log']['entries']:
    for header in entry['request'].get('headers', []):
        name = header['name']
        if name.startswith('X-') or name in ['Authorization', 'Origin', 'Referer']:
            if name not in headers_custom:
                headers_custom[name] = set()
            headers_custom[name].add(header['value'][:50])

print("Headers customizados:")
for name, values in headers_custom.items():
    print(f"  {name}:")
    for v in list(values)[:3]:
        print(f"    - {v}")
```

### 4. Mapear Endpoints

Categorizar URLs por tipo:

```python
endpoints = {
    'rest_api': [],      # /pje/seam/resource/rest/
    'jsf_pages': [],     # .seam
    'downloads': [],     # mimeType == application/pdf
    'outros': []
}

for entry in har['log']['entries']:
    url = entry['request']['url']
    mime = entry['response']['content'].get('mimeType', '')

    if '/seam/resource/rest/' in url:
        endpoints['rest_api'].append(url)
    elif '.seam' in url:
        endpoints['jsf_pages'].append(url)
    elif 'application/pdf' in mime:
        endpoints['downloads'].append(url)
    else:
        endpoints['outros'].append(url)

for categoria, urls in endpoints.items():
    print(f"\n{categoria.upper()}: {len(urls)} requisicoes")
    for url in set(urls)[:5]:
        # Remover query string para ver padrao
        base_url = url.split('?')[0]
        print(f"  - {base_url}")
```

## Sinais de Sessao Expirada

Ao analisar o HAR, identificar requisicoes que falharam:

| Status | Significado | Acao |
|--------|-------------|------|
| 401 | Nao autenticado | Token/cookie invalido |
| 403 | Proibido | Sem permissao para recurso |
| 302 para /login | Redirect | Sessao expirou |
| HTML em vez de JSON | Erro | Sessao JSF expirou |

```python
erros = []
for entry in har['log']['entries']:
    status = entry['response']['status']
    url = entry['request']['url']

    if status in [401, 403] or status >= 500:
        erros.append({
            'url': url,
            'status': status
        })
    elif status == 302:
        location = next(
            (h['value'] for h in entry['response']['headers']
             if h['name'].lower() == 'location'),
            ''
        )
        if 'login' in location.lower():
            erros.append({
                'url': url,
                'status': f'302 -> {location}'
            })

if erros:
    print("ATENCAO: Requisicoes com erro encontradas!")
    for e in erros[:10]:
        print(f"  [{e['status']}] {e['url'][:80]}")
```

## Dicas para Captura de HAR

### Firefox
1. F12 -> Network
2. Marcar "Persist Logs"
3. Navegar no PJE
4. Botao direito -> "Save All As HAR"

### Chrome
1. F12 -> Network
2. Marcar "Preserve log"
3. Navegar no PJE
4. Botao direito -> "Save all as HAR with content"

### Edge
Similar ao Chrome (mesmo engine).

## Validacao do HAR

Antes de usar, validar que o HAR contem dados uteis:

```python
def validar_har(arquivo):
    with open(arquivo, 'r', encoding='utf-8') as f:
        har = json.load(f)

    entries = har['log']['entries']
    print(f"Total de requisicoes: {len(entries)}")

    # Verificar se tem requisicoes do PJE
    pje_requests = [e for e in entries if '/pje/' in e['request']['url']]
    print(f"Requisicoes PJE: {len(pje_requests)}")

    if len(pje_requests) == 0:
        print("ERRO: Nenhuma requisicao do PJE encontrada!")
        return False

    # Verificar se tem cookies
    has_cookies = any(
        len(e['request'].get('cookies', [])) > 0
        for e in pje_requests
    )
    if not has_cookies:
        print("ERRO: Nenhum cookie encontrado!")
        return False

    # Verificar se tem requisicoes bem-sucedidas
    success = [e for e in pje_requests if e['response']['status'] == 200]
    print(f"Requisicoes bem-sucedidas: {len(success)}")

    if len(success) == 0:
        print("ERRO: Nenhuma requisicao bem-sucedida!")
        return False

    print("HAR valido!")
    return True
```
