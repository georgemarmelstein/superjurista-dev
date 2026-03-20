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
      → Leia INTEGRALMENTE. Se grande, leia em blocos.
    </passo>

    <passo numero="3" nome="Executar tarefa">
      → [Instruções específicas da tarefa]
      → [Mais instruções se necessário]
      → Use português COM ACENTOS
    </passo>

    <passo numero="4" nome="Salvar">
      Write: $WORKSPACE/[arquivo-saida]
    </passo>
  </execucao>

  <restricoes>
    - DEVE começar com "[SINALIZADOR_INICIO]"
    - DEVE terminar com "[SINALIZADOR_FIM]"
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
    </passo>

    <passo numero="3" nome="Executar e salvar">
      → [Instruções]
      Write: $WORKSPACE/[saida]
    </passo>
  </execucao>

  <restricoes>
    - DEVE começar com "[INICIO]"
    - DEVE terminar com "[FIM]"
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

    <passo numero="4" nome="Executar e salvar">
      → [Instruções]
      Write: $WORKSPACE/[saida]
    </passo>
  </execucao>

  <restricoes>
    - DEVE começar com "[INICIO]"
    - DEVE terminar com "[FIM]"
  </restricoes>

</prompt_subagente>
```

---

### Variante C: Subagente com Chunking (arquivos grandes)

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

**Quando usar:** Juntar dois ou mais arquivos sem modificar o conteúdo.

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
| Arquivo muito grande | C - Chunking |
| Após chunking, unificar | D - Consolidador |
| Juntar arquivos sem modificar | E - Merge |

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
2. **Passos explícitos** - Read → Process → Write
3. **Sinalizadores obrigatórios** - Sempre nas restrições
4. **Variáveis com $** - $WORKSPACE, $NUMERO, etc. (orquestrador substitui antes de enviar)
5. **Seta para instruções** - Use → para clareza

## Checklist de Validação

```
[ ] <prompt_subagente> tem atributo tipo?
[ ] <cabecalho> com delimitador ═══?
[ ] <identidade> define o papel?
[ ] <proposito> tem objetivo claro?
[ ] <execucao> tem passos numerados?
[ ] Primeiro passo é SEMPRE Read do agent?
[ ] <restricoes> tem sinalizadores início/fim?
[ ] Variáveis usam $VARIAVEL (ex: $WORKSPACE)?
```
