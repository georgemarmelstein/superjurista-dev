# Exemplo: CJF - Scraping JSF/AJAX

Este documento descreve o padrão de implementação usado no MCP do CJF (Conselho da Justiça Federal), que usa tecnologia JSF (JavaServer Faces) com requisições AJAX.

## Características do Sistema

| Aspecto | Valor |
|---------|-------|
| URL | https://jurisprudencia.cjf.jus.br/unificada/index.xhtml |
| Tecnologia | JSF 2.x com PrimeFaces |
| Autenticação | Pública (sem login) |
| Formato Request | `application/x-www-form-urlencoded` |
| Formato Response | XML parcial (AJAX) |

## Detecção de JSF

Sinais de que um tribunal usa JSF:

```html
<!-- Hidden field obrigatório -->
<input type="hidden" name="javax.faces.ViewState" value="..." />

<!-- IDs com padrão JSF -->
<input id="formulario:textoLivre" name="formulario:textoLivre" />

<!-- Scripts PrimeFaces -->
<script src="/javax.faces.resource/primefaces.js" />
```

## Fluxo de Requisição

### 1. Obter ViewState (GET inicial)

```python
def obter_viewstate(self) -> str:
    """Obtém ViewState da página inicial."""
    resp = self.session.get(CJF_URL, timeout=30)
    resp.raise_for_status()

    # Padrão 1: atributo value
    match = re.search(r'name="javax\.faces\.ViewState"[^>]*value="([^"]+)"', resp.text)
    if match:
        return match.group(1)

    # Padrão 2: no JavaScript
    match = re.search(r'ViewState:([^"]+)"', resp.text)
    if match:
        return match.group(1)

    raise ValueError("ViewState não encontrado")
```

### 2. Fazer Busca (POST AJAX)

```python
HEADERS = {
    "User-Agent": "Mozilla/5.0 ...",
    "Accept": "application/xml, text/xml, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Faces-Request": "partial/ajax",  # CRÍTICO para JSF
    "X-Requested-With": "XMLHttpRequest"
}

def buscar(self, termo: str, tribunais: List[str]) -> str:
    """Faz busca AJAX no CJF."""
    form_data = []

    # Headers AJAX obrigatórios
    form_data.append(("javax.faces.partial.ajax", "true"))
    form_data.append(("javax.faces.source", "formulario:actPesquisar"))
    form_data.append(("javax.faces.partial.execute", "@all"))
    form_data.append(("javax.faces.partial.render", "formulario:resultado"))

    # Identificador do botão
    form_data.append(("formulario:actPesquisar", "formulario:actPesquisar"))

    # Formulário e termo
    form_data.append(("formulario", "formulario"))
    form_data.append(("formulario:textoLivre", termo))

    # Checkboxes (tribunais selecionados)
    for trib in tribunais:
        form_data.append(("formulario:j_idt51", trib))

    # ViewState (obrigatório)
    form_data.append(("javax.faces.ViewState", self.viewstate))

    resp = self.session.post(CJF_URL, data=form_data, headers=HEADERS, timeout=60)
    return resp.text
```

### 3. Extrair Resultados do XML

A resposta AJAX do JSF vem em formato XML com CDATA:

```xml
<?xml version='1.0' encoding='UTF-8'?>
<partial-response>
  <changes>
    <update id="formulario:resultado">
      <![CDATA[
        <table id="tabelaDocumentos">
          <tr>
            <td>STJ</td>
            <td>REsp 1234567/SP</td>
            ...
          </tr>
        </table>
      ]]>
    </update>
  </changes>
</partial-response>
```

Extração:

```python
def extrair_documentos(html_content: str) -> List[Dict]:
    """Extrai documentos do HTML dentro do CDATA."""
    content = html.unescape(html_content)

    # Extrair conteúdo do CDATA
    cdata_matches = re.findall(r'<!\[CDATA\[(.*?)\]\]>', content, re.DOTALL)
    if cdata_matches:
        content = ''.join(cdata_matches)

    # Encontrar índices de documentos
    doc_indices = set(re.findall(r'tabelaDocumentos:(\d+):', content))

    documentos = []
    for idx in sorted(doc_indices, key=int):
        doc = {"indice": int(idx)}

        # Extrair campos por padrão
        pattern = rf'tabelaDocumentos:{idx}:.*?label[^>]*>Número</span>.*?<td[^>]*>([^<]+)</td>'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            doc["numero"] = match.group(1).strip()

        # ... mais campos
        documentos.append(doc)

    return documentos
```

## Sintaxe Booleana do CJF

| Operador | Sintaxe | Case | Exemplo |
|----------|---------|------|---------|
| AND | E | MAIÚSCULO | pensão E morte |
| OR | OU | MAIÚSCULO | bpc OU loas |
| NOT | NAO | MAIÚSCULO | servidor NAO militar |
| XOR | XOU | MAIÚSCULO | pensão XOU aposentadoria |
| Adjacente | ADJ[n] | MAIÚSCULO | Repartição ADJ Pública |
| Próximo | PROX[n] | MAIÚSCULO | aposentadoria PROX3 invalidez |
| Mesma sentença | COM | MAIÚSCULO | pensão COM dependente |
| Mesmo parágrafo | MESMO | MAIÚSCULO | benefício MESMO previdenciário |
| Campo específico | [CAMPO] | - | aposentadoria[EMEN] |
| Wildcard sufixo | $ | - | aposentad$ |
| Wildcard prefixo | $ | - | $doença |
| Wildcard n chars | $[n] | - | A$3Z |
| Um caractere | ? | - | MA?? |

### Campos específicos do CJF

| Campo | Descrição |
|-------|-----------|
| EMEN | Ementa |
| DECI | Decisão |
| REL | Relator |
| TRIB | Tribunal |
| ORGA | Órgão julgador |
| REFL | Legislação citada |
| INDE | Indexação |
| ITEO | Inteiro teor |
| DTDP | Data da decisão |
| DTPP | Data da publicação |

## Lições Aprendidas

1. **ViewState é obrigatório** - Sem ele, a requisição falha silenciosamente
2. **Header Faces-Request** - Identifica requisição AJAX para o servidor JSF
3. **IDs são dinâmicos** - O padrão `formulario:j_idt51` pode mudar entre versões
4. **CDATA wrapping** - O HTML vem dentro de CDATA no XML de resposta
5. **Session cookies** - O JSF mantém estado na sessão, use `requests.Session()`
6. **Retry é importante** - O portal CJF ocasionalmente retorna erros 500
