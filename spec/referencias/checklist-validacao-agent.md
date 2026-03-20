# Checklist de Validação: Agent v2.0

> **Propósito:** Métrica de conformidade para validar se um agent segue o spec v2.0.
>
> **Como usar:** Aplique este checklist a cada agent criado. Score mínimo recomendado: 80%.
>
> **Versão:** 1.1 (calibrado após auditoria de relator-marmelstein)

---

## Pontuação

| Categoria | Peso | Descrição |
|-----------|------|-----------|
| CRÍTICO | 10 pts | Falha impede funcionamento correto |
| ALTO | 5 pts | Falha compromete reutilização/manutenção |
| MÉDIO | 3 pts | Falha afeta qualidade mas não funcionalidade |
| MENOR | 1 pt | Melhoria recomendada |

**Score máximo:** 110 pontos (com seção de Granularidade)
**Score mínimo recomendado:** 88 pontos (80%)

---

## 1. YAML Frontmatter (30 pontos)

### 1.1 Estrutura (CRÍTICO - 10 pts)

```
[ ] Bloco YAML presente no início do arquivo?
    Formato: --- no início e fim do bloco
```

### 1.2 Campo `name` (CRÍTICO - 10 pts)

```
[ ] Campo `name` presente?
[ ] Formato kebab-case? (minúsculas + hífens)
[ ] Sem underscores, espaços ou maiúsculas?
[ ] Nome reflete CAPACIDADE, não pipeline?

Exemplos válidos:
  ✅ extrator-linha-tempo
  ✅ analisador-juridico
  ❌ etapa-01-extracao (referência a etapa)
  ❌ pipeline_sentenca_relator (underscore + pipeline)
```

### 1.3 Campo `description` (ALTO - 5 pts)

```
[ ] Campo `description` presente?
[ ] Descreve a CAPACIDADE do agent?
[ ] Não menciona pipeline ou etapa específica?
[ ] Conciso (1-2 linhas)?

Exemplos válidos:
  ✅ "Extrai cronologia completa de atos processuais"
  ❌ "Etapa 1 do pipeline de sentença" (menciona pipeline)
```

### 1.4 Campo `tools` (ALTO - 5 pts)

```
[ ] Campo `tools` presente?
[ ] Ferramentas separadas por ESPAÇO (não vírgula)?
[ ] Apenas tools necessárias listadas?

Exemplos válidos:
  ✅ tools: Read Write
  ✅ tools: Read Write Glob
  ❌ tools: Read, Write (vírgula)
  ❌ tools: [Read, Write] (colchetes)
```

### 1.5 Campo `model` (CRÍTICO - 5 pts) [NOVO v1.2]

```
[ ] Campo `model` presente?
[ ] Modelo correto para o tipo de tarefa?

REGRA DE SELEÇÃO:
  | Tipo de Tarefa | Modelo |
  |----------------|--------|
  | Jurídica (extração, análise, relatório) | opus |
  | Pesquisa (busca precedentes) | sonnet |
  | Operacional (formatação, merge) | haiku |

Exemplos:
  ✅ model: opus (para relator, analisador, fundamentador)
  ✅ model: sonnet (para pesquisador-julia, pesquisador-cjf)
  ❌ model: sonnet (para analisador-marmelstein - deveria ser opus)
```

### 1.6 Campo `color` (MÉDIO - 3 pts) [NOVO v1.2]

```
[ ] Campo `color` presente?
[ ] Cor corresponde à categoria do agent?

CORES SEMÂNTICAS (Convenção Anthropic):
  | Cor | Semântica | Categorias |
  |-----|-----------|------------|
  | yellow | Exploração, investigação | extracao, analise, pesquisa |
  | green | Construção, design | redacao |
  | red | Revisão crítica, validação | revisao |
  | blue | Propósito geral | (neutro) |
  | purple | Documentação | (informativo) |
  | orange | Refatoração | (transformação) |

Exemplos:
  ✅ color: yellow (para linha-tempo, analisador, pesquisador)
  ✅ color: green (para redator, fundamentador)
  ✅ color: red (para revisor, advogado-diabo)
  ❌ color: blue (para analisador - deveria ser yellow)
```

---

## 2. Localização do Arquivo (10 pontos)

### 2.1 Caminho (CRÍTICO - 10 pts)

```
[ ] Arquivo em `.claude/agents/` ou subpasta por categoria?

Caminhos válidos:
  ✅ .claude/agents/extrator-linha-tempo.md
  ✅ .claude/agents/extracao/linha-tempo.md (categoria)
  ✅ .claude/agents/revisao/advogado-diabo.md (categoria)

Caminhos inválidos:
  ❌ .claude/agents/pipeline-sentenca/relator.md (pipeline no nome)
  ❌ .claude/agents/etapa-01/extrator.md (etapa no nome)

Regra: Subpasta deve indicar TIPO DE TAREFA, não pipeline.
```

---

## 3. Tags XML Obrigatórias (40 pontos)

### 3.1 Tag `<identidade>` (ALTO - 5 pts)

```
[ ] Tag <identidade> presente?
[ ] Subtag <papel> presente e preenchida?
[ ] Subtag <estilo> presente e preenchida?
[ ] Sem texto solto fora das subtags?

Formato correto:
  <identidade>
    <papel>Descrição do papel</papel>
    <estilo>Estilo de execução</estilo>
  </identidade>

Formato incorreto:
  <identidade>
  Você é um extrator...  ← texto solto
  <papel>...</papel>
  </identidade>
```

### 3.2 Tag `<capacidade>` (CRÍTICO - 10 pts)

```
[ ] Tag <capacidade> presente?
[ ] Subtag <habilidade> descreve O QUE sabe fazer?
[ ] Subtag <especializacao> define área de expertise?
[ ] Não menciona caminhos ou pipelines?

Formato:
  <capacidade>
    <habilidade>Verbo no infinitivo + o que faz</habilidade>
    <especializacao>Área de conhecimento</especializacao>
  </capacidade>
```

### 3.3 Tag `<contrato>` (CRÍTICO - 10 pts)

```
[ ] Tag <contrato> presente?
[ ] Subtag <entrada> com <tipo>, <formato>, <requisitos>?
[ ] Subtag <saida> com <tipo>, <formato>?
[ ] Tipos são GENÉRICOS (não caminhos específicos)?

Formato:
  <contrato>
    <entrada>
      <tipo>Tipo de dado (texto, relatório, lista)</tipo>
      <formato>TXT, MD, JSON</formato>
      <requisitos>O que a entrada DEVE conter</requisitos>
    </entrada>
    <saida>
      <tipo>Tipo de dado produzido</tipo>
      <formato>MD, TXT</formato>
    </saida>
  </contrato>

Erros comuns:
  ❌ <tipo>Arquivo relatorio.md</tipo> (caminho específico)
  ❌ <formato>workspace/processo/saida.md</formato> (caminho)
```

### 3.4 Tag `<restricoes>` (ALTO - 5 pts)

```
[ ] Tag <restricoes> presente?
[ ] Usa prefixos NUNCA/NÃO/SEMPRE?
[ ] Inclui "NÃO assumir caminhos de arquivo"?
[ ] Inclui "SEMPRE usar português com acentos"?

Restrições obrigatórias para v2.0:
  - NÃO assumir caminhos de arquivo - recebe via contexto
  - NUNCA inventar informações não presentes na entrada
  - SEMPRE usar português com acentos corretos
```

### 3.5 Tag `<contingencias>` (ALTO - 5 pts)

```
[ ] Tag <contingencias> presente?
[ ] Subtag <se_entrada_insuficiente> presente?
[ ] Subtag <se_ambiguo> presente?
[ ] Ações são claras e executáveis?

Formato:
  <contingencias>
    <se_entrada_insuficiente>Ação específica</se_entrada_insuficiente>
    <se_ambiguo>Ação específica</se_ambiguo>
  </contingencias>
```

### 3.6 Tag `<instrucoes>` (ALTO - 5 pts)

```
[ ] Tag <instrucoes> presente?
[ ] Usa subtags <passo numero="N" nome="...">?
[ ] Passos em ordem lógica?
[ ] Passo 1 menciona "receber entrada" (não caminho específico)?

Formato:
  <instrucoes>
    <passo numero="1" nome="Receber entrada">
      Ler o conteúdo fornecido pelo orquestrador.
    </passo>
    <passo numero="2" nome="Processar">
      Descrição do processamento.
    </passo>
    <passo numero="3" nome="Produzir saída">
      Gerar saída no formato especificado.
    </passo>
  </instrucoes>
```

---

## 4. Tags XML Recomendadas (10 pontos)

### 4.1 Tag `<formato_saida>` (MÉDIO - 3 pts)

```
[ ] Tag <formato_saida> presente?
[ ] Template literal do output esperado?
[ ] Inclui sinalizadores de início e fim?
```

### 4.2 Tag `<sinalizadores>` (MÉDIO - 3 pts)

```
[ ] Tag <sinalizadores> presente?
[ ] Define pelo menos Início e Fim?
[ ] Formato de tabela correto?

Formato:
  <sinalizadores>
    | Posição | Texto Obrigatório |
    |---------|-------------------|
    | Início  | "TEXTO_INICIO"    |
    | Fim     | "TEXTO_FIM"       |
  </sinalizadores>
```

### 4.3 Tag `<exemplos>` (MÉDIO - 3 pts)

```
[ ] Tag <exemplos> presente?
[ ] Exemplo de entrada típica?
[ ] Exemplo de saída esperada?
```

### 4.4 Extensões de Domínio (MENOR - 1 pt)

```
[ ] Se há conhecimento de domínio extenso, está em tags separadas?
[ ] Considerar mover para references/ se > 50 linhas?

Tags de extensão aceitáveis:
  <principios>
  <regras_especificas>
  <glossario>
  <templates_dominio>
```

---

## 5. Ausência de Anti-Patterns (10 pontos)

### 5.1 Sem Caminhos Hardcoded (CRÍTICO - 10 pts)

```
[ ] NENHUM caminho específico em todo o arquivo?

Buscar por padrões proibidos:
  ❌ workspace/
  ❌ processo-
  ❌ .claude/agents/
  ❌ [NUMERO]-arquivo.md
  ❌ etapa-01
  ❌ Read: caminho/específico
  ❌ Write: caminho/específico

O agent NÃO deve saber:
  - Onde está o arquivo de entrada
  - Onde salvar a saída
  - Qual o número do processo
  - Em qual etapa do pipeline está
```

### 5.2 Sem Pseudo-Contratos em Comentários (ALTO - 5 pts) [NOVO v1.1]

```
[ ] NENHUM comentário HTML/XML define entrada/saída?

Buscar por padrões proibidos:
  ❌ <!-- ENTRADA: arquivo.txt -->
  ❌ <!-- SAÍDA: resultado.md -->
  ❌ // Input: data.json
  ❌ # ENTRADA: ... / SAÍDA: ...

Contratos devem estar em tag <contrato>, não em comentários.
```

### 5.3 Sem Tags v1 Obsoletas (ALTO - 5 pts) [NOVO v1.1]

```
[ ] NENHUMA tag v1 presente no arquivo?

Mapeamento v1 → v2 (tags obsoletas):
  ❌ <persona> → use <identidade>
  ❌ <objetivo> → use <capacidade> + <contrato>
  ❌ <regras> → use <restricoes>
  ❌ <instrucao> (singular) → use <instrucoes> com <passo>
  ❌ # ETAPA XX → remover (agent não sabe sua etapa)
```

---

## 6. Modularidade e Granularidade (10 pontos) [NOVO v1.1]

> **Rationale:** Agent deve ser reutilizável em múltiplos pipelines, recebendo
> entradas variáveis (só processo, processo + linha-tempo, múltiplos documentos).

### 6.1 Entrada Flexível (CRÍTICO - 5 pts)

```
[ ] Entrada definida por TIPO genérico, não nome de arquivo?
    ✅ Correto: <tipo>Documentos processuais em texto</tipo>
    ❌ Errado: ENTRADA: processo.txt

[ ] Agent funciona com entrada mínima?
    ✅ "Ao menos um documento processual"
    ❌ "Deve haver processo.txt e contestacao.txt"

[ ] Agent aproveita entradas opcionais se disponíveis?
    ✅ "Se houver linha-tempo, usar para ordenação"
    ❌ Ignora completamente outros arquivos
```

### 6.2 Saída Genérica (ALTO - 5 pts)

```
[ ] Saída definida por TIPO, não caminho?
    ✅ Correto: <tipo>Relatório estruturado</tipo>
    ❌ Errado: SAÍDA: relatorio-marmelstein.md

[ ] Nome do arquivo de saída NÃO hardcoded?
    ✅ Orquestrador define o destino
    ❌ Agent assume nome específico

[ ] Formato independente do pipeline?
    ✅ Funciona para pipeline-sentenca, pipeline-pesquisa, etc.
    ❌ Assume contexto específico de um pipeline
```

---

## 7. Prevenção de Anti-Padrões Multi-Agentes (14 pontos) [NOVO v1.3]

> **Referência:** `.claude/specs/referencias/anti-padroes-multi-agentes.md`
>
> Baseado em pesquisa que mostra 60-80% de falha em sistemas multi-agentes.

### 7.1 Clareza de Papel (CRÍTICO - 5 pts)

```
[ ] Agent tem papel ÚNICO e ESPECÍFICO?
    ✅ "Analisa consistência interna de fundamentações"
    ❌ "Ajuda com análise jurídica" (muito genérico)

[ ] Papel é DISTINTO de outros agents?
    ✅ analisador-interno ≠ analisador-externo
    ❌ agent1 e agent2 fazem a mesma coisa

[ ] Ferramentas são ESCOPADAS ao papel?
    ✅ Revisor só precisa de Read
    ❌ Todo agent tem Write Edit Bash Task
```

### 7.2 Prompt Não-Emaranhado (ALTO - 3 pts)

```
[ ] Prompt principal < 300 linhas?
[ ] Conhecimento extenso em references/?
[ ] Instruções separadas em passos claros?

Buscar por sinais de emaranhamento:
  ❌ Arquivo > 500 linhas
  ❌ Múltiplos domínios em um só prompt
  ❌ Instruções conflitantes
```

### 7.3 Comunicação Estruturada (ALTO - 3 pts)

```
[ ] Saída tem formato estruturado (schema)?
    ✅ JSON, XML, ou Markdown com headers definidos
    ❌ Texto livre sem estrutura

[ ] <contrato> define formato esperado?
[ ] <formato_saida> é preciso e parseável?
```

### 7.4 Diversidade de Perspectiva (MÉDIO - 3 pts)

```
[ ] Se agent é revisor, ele QUESTIONA (não apenas confirma)?
    ✅ "Buscar falhas, inconsistências, vulnerabilidades"
    ❌ "Validar que está tudo certo"

[ ] Instruções evitam viés de confirmação?
    ✅ "Liste problemas ANTES de listar pontos positivos"
    ❌ "Verifique se está bom"
```

---

## Cálculo do Score

```
YAML Frontmatter:                    ___ / 38
Localização:                         ___ / 10
Tags Obrigatórias:                   ___ / 40
Tags Recomendadas:                   ___ / 10
Ausência Anti-Patterns (código):     ___ / 20
Granularidade:                       ___ / 10
Anti-Padrões Multi-Agentes:          ___ / 14  [NOVO v1.3]
─────────────────────────────────────────────
TOTAL:                               ___ / 142
```

### Detalhamento Seção 5 (Anti-Patterns)

```
5.1 Sem caminhos hardcoded:     ___ / 10
5.2 Sem pseudo-contratos:       ___ / 5
5.3 Sem tags v1 obsoletas:      ___ / 5
                                ─────────
Subtotal:                       ___ / 20
```

### Detalhamento Seção 7 (Anti-Padrões Multi-Agentes)

```
7.1 Clareza de papel:               ___ / 5
7.2 Prompt não-emaranhado:          ___ / 3
7.3 Comunicação estruturada:        ___ / 3
7.4 Diversidade de perspectiva:     ___ / 3
                                    ─────────
Subtotal:                           ___ / 14
```

### Interpretação

| Score | % | Classificação | Ação |
|-------|---|---------------|------|
| 128-142 | 90%+ | Excelente | Aprovado |
| 114-127 | 80-89% | Bom | Aprovado com observações |
| 99-113 | 70-79% | Regular | Correções recomendadas |
| 85-98 | 60-69% | Insuficiente | Correções necessárias |
| < 85 | < 60% | Reprovado | Refazer seguindo spec |

---

## Exemplo de Aplicação

### Agent: `linha-tempo.md` (antes da correção)

```
YAML Frontmatter:
  [❌] Bloco YAML presente? (0/10)
  [❌] Campo name? (0/10)
  [❌] Campo description? (0/5)
  [❌] Campo tools? (0/5)
  Subtotal: 0/30

Localização:
  [⚠️] Subpasta por categoria? (5/10 - categoria ok, mas pipeline no path)
  Subtotal: 5/10

Tags Obrigatórias:
  [⚠️] <identidade>? (3/5 - presente mas mal formatada)
  [❌] <capacidade>? (0/10)
  [❌] <contrato>? (0/10)
  [⚠️] <restricoes>? (3/5 - presente mas falta restrição de caminhos)
  [❌] <contingencias>? (0/5)
  [❌] <instrucoes>? (0/5)
  Subtotal: 6/40

Tags Recomendadas:
  [✅] <formato_saida>? (3/3)
  [✅] <sinalizadores>? (3/3)
  [❌] <exemplos>? (0/3)
  [✅] Extensões de domínio organizadas? (1/1)
  Subtotal: 7/10

Ausência Anti-Patterns:
  [❌] Sem caminhos hardcoded? (0/10 - tem [NUMERO]-linha-tempo.md)
  Subtotal: 0/10

─────────────────────────────
TOTAL: 18/100 (REPROVADO)
─────────────────────────────
```

---

## Checklist Rápido (Versão Resumida)

Para uso diário, versão simplificada:

```
CRÍTICO (deve ter todos):
[ ] YAML frontmatter com name, description, tools, model
[ ] Localização correta (.claude/agents/ ou subpasta por categoria)
[ ] Tag <capacidade> com <habilidade> e <especializacao>
[ ] Tag <contrato> com <entrada> e <saida>
[ ] ZERO caminhos hardcoded no arquivo
[ ] ZERO tags v1 (<persona>, <objetivo>) - usar tags v2        [NOVO v1.1]
[ ] Entrada definida por TIPO, não por nome de arquivo          [NOVO v1.1]

ALTO (deve ter maioria):
[ ] Tag <identidade> com <papel> e <estilo>
[ ] Tag <restricoes> com "NÃO assumir caminhos"
[ ] Tag <contingencias> com ações para falhas
[ ] Tag <instrucoes> com passos numerados
[ ] Sem pseudo-contratos em comentários HTML                    [NOVO v1.1]
[ ] Saída definida por TIPO, não por nome de arquivo            [NOVO v1.1]

RECOMENDADO (nice to have):
[ ] Tag <formato_saida> com template
[ ] Tag <sinalizadores> com início/fim
[ ] Tag <exemplos> com entrada/saída
[ ] Agent aproveita entradas opcionais se disponíveis           [NOVO v1.1]

ANTI-PADRÕES MULTI-AGENTES (verificar):                         [NOVO v1.3]
[ ] Papel é ÚNICO e ESPECÍFICO (não genérico)?
[ ] Papel é DISTINTO de outros agents?
[ ] Ferramentas são ESCOPADAS ao papel (mínimo necessário)?
[ ] Prompt < 300 linhas (conhecimento em references/)?
[ ] Saída tem formato ESTRUTURADO (parseável)?
[ ] Se revisor: questiona ao invés de confirmar?
```

---

## Changelog

### v1.3 (2026-01-19)
- ADICIONADO: Seção 7 - Prevenção de Anti-Padrões Multi-Agentes (14 pts)
  - 7.1 Clareza de papel (5 pts)
  - 7.2 Prompt não-emaranhado (3 pts)
  - 7.3 Comunicação estruturada (3 pts)
  - 7.4 Diversidade de perspectiva (3 pts)
- ATUALIZADO: Score máximo de 128 para 142 pontos
- ATUALIZADO: Tabela de interpretação com novos ranges
- ADICIONADO: Referência a `.claude/specs/referencias/anti-padroes-multi-agentes.md`
- FONTE: Pesquisa de Arquiteturas Multi-Agentes Hierárquicas (60-80% falha)

### v1.2 (2026-01-18)
- ADICIONADO: Seção 1.5 - Campo `model` com regra de seleção (opus/sonnet/haiku)
- ADICIONADO: Seção 1.6 - Campo `color` com cores semânticas por categoria
- ATUALIZADO: Score máximo de 120 para 128 pontos
- ATUALIZADO: YAML Frontmatter de 30 para 38 pontos

### v1.1 (2026-01-18)
- Calibrado após auditoria de `relator-marmelstein.md`
- ADICIONADO: Seção 5.2 - Sem pseudo-contratos em comentários
- ADICIONADO: Seção 5.3 - Sem tags v1 obsoletas (mapeamento v1→v2)
- ADICIONADO: Seção 6 - Modularidade e Granularidade (10 pts)
- ATUALIZADO: Score máximo de 100 para 120 pontos
- ATUALIZADO: Tabela de interpretação com porcentagens

### v1.0 (2026-01-18)
- Versão inicial baseada em Spec Agent v2.0

---

**Versão:** 1.3
**Data:** 2026-01-19
**Baseado em:** Spec Agent v2.0 + Regras de modelo/cor + Anti-Padrões Multi-Agentes
