# Referência: Variantes de Prompt de Subagente

> **O que é:** Catálogo de padrões de `<prompt_subagente>` para diferentes cenários.
>
> **Como usar:** Consulte esta referência ao criar o bloco `<prompt_subagente>` dentro do seu orquestrador.

---

## Estrutura Padrão

Todo prompt de subagente segue esta estrutura base:

```markdown
<prompt_subagente tipo="[FUNÇÃO]">

  <cabecalho>
    ═══════════════════════════════════════════════════════════════════════
    VOCÊ É UM SUBAGENTE DE [FUNÇÃO]. EXECUTE DIRETAMENTE.
    ═══════════════════════════════════════════════════════════════════════
  </cabecalho>

  <identidade>
    <papel>Você é um [papel específico].</papel>
  </identidade>

  <proposito>
    <objetivo>[Objetivo desta etapa em uma frase].</objetivo>
  </proposito>

  <execucao>
    <passo numero="1" nome="Ler instruções">
      Read: .claude/agents/[agent].md
      → Este arquivo é LEI. Siga fielmente.
    </passo>

    <passo numero="2" nome="Ler entrada">
      Read: $WORKSPACE/[arquivo-entrada]
      → Leia a entrada por caminho.
    </passo>

    <passo numero="3" nome="Executar tarefa">
      → [Instruções específicas da tarefa]
      → [Mais instruções se necessário]
      → Use português COM ACENTOS
    </passo>

    <passo numero="4" nome="Gravar o documento">
      Write: $WORKSPACE/[arquivo-saida]
      → GRAVE o documento completo, com os marcadores de início/fim.
    </passo>

    <passo numero="5" nome="Responder status">
      → Responder APENAS: "[slug-etapa] OK | [arquivo-saida]" — NÃO imprimir o documento.
    </passo>
  </execucao>

  <restricoes>
    - DEVE GRAVAR o documento com "[SINALIZADOR_INICIO]" e "[SINALIZADOR_FIM]" (âncoras do gate)
    - Responder APENAS 1 linha de status — NÃO imprimir o documento (L5)
    - SEM asteriscos, SEM hashtags
    - [Outras restrições específicas]
  </restricoes>

  <contingencia>
    [O que fazer se encontrar problemas]
  </contingencia>

</prompt_subagente>
```

---

## Catálogo de Variantes

### Variante A: Subagente Simples (uma entrada)

**Quando usar:** Etapa com uma única entrada e uma única saída.

```markdown
<prompt_subagente tipo="[FUNÇÃO]" variante="simples">

  <cabecalho>
    ═══════════════════════════════════════════════════════════════════════
    VOCÊ É UM SUBAGENTE DE [FUNÇÃO]. EXECUTE DIRETAMENTE.
    ═══════════════════════════════════════════════════════════════════════
  </cabecalho>

  <identidade>
    <papel>Você é um [papel].</papel>
  </identidade>

  <proposito>
    <objetivo>[Objetivo].</objetivo>
  </proposito>

  <execucao>
    <passo numero="1" nome="Ler instruções">
      Read: .claude/agents/[agent].md
      → Este arquivo é LEI. Siga fielmente.
    </passo>

    <passo numero="2" nome="Ler entrada">
      Read: $WORKSPACE/[arquivo]
      → Leia a entrada por caminho.
    </passo>

    <passo numero="3" nome="Executar e gravar">
      → [Instruções]
      Write: $WORKSPACE/[saida]   → GRAVA o documento completo, com marcadores.
    </passo>

    <passo numero="4" nome="Responder status">
      → Responder APENAS: "[slug-etapa] OK | [saida]" — NÃO imprimir o documento.
    </passo>
  </execucao>

  <restricoes>
    - DEVE GRAVAR com "[INICIO]" e "[FIM]" (âncoras do gate)
    - Responder APENAS 1 linha de status — NÃO imprimir o documento (L5)
  </restricoes>

</prompt_subagente>
```

---

### Variante B: Subagente com Múltiplas Entradas

**Quando usar:** Etapa que precisa combinar informações de 2+ arquivos.

```markdown
<prompt_subagente tipo="[FUNÇÃO]" variante="multiplas-entradas">

  <cabecalho>
    ═══════════════════════════════════════════════════════════════════════
    VOCÊ É UM SUBAGENTE DE [FUNÇÃO]. EXECUTE DIRETAMENTE.
    ═══════════════════════════════════════════════════════════════════════
  </cabecalho>

  <identidade>
    <papel>Você é um [papel].</papel>
  </identidade>

  <proposito>
    <objetivo>[Objetivo].</objetivo>
  </proposito>

  <execucao>
    <passo numero="1" nome="Ler instruções">
      Read: .claude/agents/[agent].md
      → Este arquivo é LEI. Siga fielmente.
    </passo>

    <passo numero="2" nome="Ler entrada principal">
      Read: $WORKSPACE/[arquivo-principal]
      → Este é o documento BASE.
    </passo>

    <passo numero="3" nome="Ler contexto adicional">
      Read: $WORKSPACE/[arquivo-contexto]
      → Use como REFERÊNCIA, não copie.
    </passo>

    <passo numero="4" nome="Executar e gravar">
      → [Instruções]
      Write: $WORKSPACE/[saida]   → GRAVA o documento completo, com marcadores.
    </passo>

    <passo numero="5" nome="Responder status">
      → Responder APENAS: "[slug-etapa] OK | [saida]" — NÃO imprimir o documento.
    </passo>
  </execucao>

  <restricoes>
    - DEVE GRAVAR com "[INICIO]" e "[FIM]" (âncoras do gate)
    - Responder APENAS 1 linha de status — NÃO imprimir o documento (L5)
  </restricoes>

</prompt_subagente>
```

---

### Variante C: Subagente com Chunking (arquivos grandes)

> **LEGADO — era-200k.** O chunking defensivo era necessário na janela de 200k; hoje leia
> a entrada direto por caminho. Use esta variante SÓ para arquivos genuinamente gigantes
> que estouram a janela atual — não como padrão.

**Quando usar:** Arquivo de entrada muito grande para processar de uma vez.

```markdown
<prompt_subagente tipo="[FUNÇÃO]" variante="chunking" chunk="[N]" total="[TOTAL]">

  <cabecalho>
    ═══════════════════════════════════════════════════════════════════════
    VOCÊ É UM SUBAGENTE DE [FUNÇÃO] - CHUNK [N] de [TOTAL]. EXECUTE DIRETAMENTE.
    ═══════════════════════════════════════════════════════════════════════
  </cabecalho>

  <identidade>
    <papel>Você é um [papel] processando parte de um documento maior.</papel>
  </identidade>

  <proposito>
    <objetivo>[Objetivo para este chunk].</objetivo>
  </proposito>

  <execucao>
    <passo numero="1" nome="Ler instruções">
      Read: .claude/agents/[agent].md
      → Este arquivo é LEI. Siga fielmente.
    </passo>

    <passo numero="2" nome="Ler chunk">
      Read: $WORKSPACE/chunks/chunk_[N].txt
      → Este é o CHUNK [N] de [TOTAL].
      → Processe apenas este trecho.
    </passo>

    <passo numero="3" nome="Executar e salvar">
      → [Instruções específicas para chunk]
      Write: $WORKSPACE/chunks/resultado_[N].md
    </passo>
  </execucao>

  <restricoes>
    - Este é chunk [N] de [TOTAL]
    - NÃO tente acessar outros chunks
    - Mantenha contexto local apenas
  </restricoes>

</prompt_subagente>
```

---

### Variante D: Subagente Consolidador (pós-chunking)

> **LEGADO — era-200k.** Só faz sentido como par da Variante C (chunking defensivo). Hoje,
> se a leitura direta cabe, não há chunks a consolidar. Use apenas quando C for genuinamente
> necessária (arquivo gigante).

**Quando usar:** Após processar chunks, para unificar os resultados parciais.

```markdown
<prompt_subagente tipo="CONSOLIDADOR" variante="pos-chunking">

  <cabecalho>
    ═══════════════════════════════════════════════════════════════════════
    VOCÊ É UM CONSOLIDADOR. EXECUTE DIRETAMENTE.
    ═══════════════════════════════════════════════════════════════════════
  </cabecalho>

  <identidade>
    <papel>Você consolida resultados de múltiplos chunks em documento único.</papel>
  </identidade>

  <proposito>
    <objetivo>Unificar [N] resultados parciais em [saída final].</objetivo>
  </proposito>

  <execucao>
    <passo numero="1" nome="Ler instruções">
      Read: .claude/agents/[agent].md
    </passo>

    <passo numero="2" nome="Ler todos os resultados">
      Read: $WORKSPACE/chunks/resultado_aa.md
      Read: $WORKSPACE/chunks/resultado_ab.md
      Read: $WORKSPACE/chunks/resultado_ac.md
      ... (todos os chunks)
    </passo>

    <passo numero="3" nome="Consolidar">
      → Unificar em ordem cronológica
      → Remover duplicatas
      → Manter consistência
    </passo>

    <passo numero="4" nome="Salvar">
      Write: $WORKSPACE/[arquivo-consolidado]
    </passo>
  </execucao>

  <restricoes>
    - DEVE seguir formato do agent
    - NÃO duplicar conteúdo
    - MANTER ordem original
  </restricoes>

</prompt_subagente>
```

---

### Variante E: Subagente de Merge (apenas unificar)

> **v3.0 — prefira um SCRIPT para merge PURO.** Se o merge é concatenação sem juízo (juntar
> dois arquivos sem modificar), use um `merge_<sistema>.py` (zero LLM, zero contexto): o
> conteúdo não transita pelo contexto do orquestrador. Este subagente de merge só é necessário
> quando há JUÍZO EDITORIAL (reconciliar, deduplicar com critério, reescrever transições).

**Quando usar:** Juntar dois ou mais arquivos com juízo editorial (não mera concatenação).

```markdown
<prompt_subagente tipo="MERGE" variante="unificacao">

  <cabecalho>
    ═══════════════════════════════════════════════════════════════════════
    VOCÊ É UM SUBAGENTE DE MERGE. EXECUTE DIRETAMENTE.
    ═══════════════════════════════════════════════════════════════════════
  </cabecalho>

  <identidade>
    <papel>Você é um assistente de formatação. Apenas unifica, não modifica.</papel>
  </identidade>

  <proposito>
    <objetivo>Unificar [arquivo-1] e [arquivo-2] em documento único.</objetivo>
  </proposito>

  <execucao>
    <passo numero="1" nome="Ler instruções">
      Read: .claude/agents/merge.md
    </passo>

    <passo numero="2" nome="Ler primeiro documento">
      Read: $WORKSPACE/[arquivo-1]
    </passo>

    <passo numero="3" nome="Ler segundo documento">
      Read: $WORKSPACE/[arquivo-2]
    </passo>

    <passo numero="4" nome="Unificar e salvar">
      → APENAS UNIFIQUE — NÃO modifique conteúdo
      → PRESERVE TODOS OS ACENTOS
      → NÃO duplique títulos
      Write: $WORKSPACE/[arquivo-final]
    </passo>
  </execucao>

  <restricoes>
    - APENAS unificar, NUNCA modificar
    - PRESERVAR acentos EXATAMENTE como estão
    - DEVE começar com "[INICIO]"
    - DEVE terminar com "[FIM]"
  </restricoes>

</prompt_subagente>
```

---

## Guia Rápido de Seleção

| Cenário | Variante |
|---------|----------|
| Uma entrada, uma saída | A - Simples |
| Duas+ entradas para combinar | B - Múltiplas Entradas |
| Arquivo genuinamente gigante (estoura a janela) | C - Chunking (LEGADO era-200k) |
| Após chunking, unificar | D - Consolidador (LEGADO era-200k) |
| Concatenação PURA (sem juízo) | SCRIPT `merge_<sistema>.py` (não subagente) |
| Merge com JUÍZO EDITORIAL | E - Merge |

---

## Tags XML

| Tag | Obrigatória | Descrição |
|-----|-------------|-----------|
| `<prompt_subagente>` | Sim | Raiz com atributos `tipo` e `variante` |
| `<cabecalho>` | Sim | Delimitador visual com mensagem de execução |
| `<identidade>` | Sim | Quem é o subagente |
| `<proposito>` | Sim | O que deve fazer |
| `<execucao>` | Sim | Passos numerados com Read/Write |
| `<restricoes>` | Sim | Sinalizadores e regras |
| `<contingencia>` | Opcional | O que fazer se falhar |

## Atributos do `<prompt_subagente>`

| Atributo | Obrigatório | Descrição |
|----------|-------------|-----------|
| `tipo` | Sim | Função do subagente (ex: RELATOR, FUNDAMENTADOR) |
| `variante` | Opcional | Tipo de variante (simples, multiplas-entradas, chunking, etc.) |
| `chunk` | Condicional | Número do chunk (se variante=chunking) |
| `total` | Condicional | Total de chunks (se variante=chunking) |

## Regras de Ouro

1. **Sempre instrua LER o agent** - Nunca copie o prompt completo
2. **Passos explícitos** - Read → Process → **Write (grava)** → **Responder 1 linha de status**
3. **Grava + responde 1 linha (L5)** - o documento vai no ARQUIVO; a resposta é só "<slug> OK | <arquivo>", nunca o documento inline
4. **Sinalizadores obrigatórios** - âncoras do gate, gravadas NO ARQUIVO (conferidas por verificar_<sistema>.py, não por leitura)
5. **Variáveis com $** - $WORKSPACE, $NUMERO, etc. (orquestrador substitui antes de enviar)
6. **Seta para instruções** - Use → para clareza

## Checklist de Validação

```
[ ] <prompt_subagente> tem atributo tipo?
[ ] <cabecalho> com delimitador ═══?
[ ] <identidade> define o papel?
[ ] <proposito> tem objetivo claro?
[ ] <execucao> tem passos numerados?
[ ] Primeiro passo é SEMPRE Read do agent?
[ ] Passo de saída GRAVA (Write) o documento com marcadores?
[ ] Último passo responde 1 linha de status ("<slug> OK | <arquivo>") — NÃO ecoa o documento (L5)?
[ ] <restricoes> tem sinalizadores início/fim (âncoras do gate) e "NÃO imprimir inline"?
[ ] Validação da etapa é por gate por script (verificar --etapa), não por leitura?
[ ] Variáveis usam $VARIAVEL (ex: $WORKSPACE)?
```
