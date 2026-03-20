# Playbook: Agent Teams no SuperJurista

> **Versão:** 1.0
> **Data:** 2026-02-07
> **Público:** Usuários do SuperJurista que querem usar ou criar Agent Teams

---

## O Que São Agent Teams?

Agent Teams são grupos de agents que trabalham **em paralelo**, cada um com sua especialidade, comunicando-se via **arquivos de domínio**. Diferente de pipelines sequenciais, teammates executam simultaneamente.

### Analogia

Pense em um escritório de advocacia:
- **Pipeline Sequencial:** Um advogado faz tudo (pesquisa, análise, redação)
- **Agent Team:** Três estagiários pesquisam fontes diferentes ao mesmo tempo, depois um advogado consolida

---

## Teams Disponíveis

### TEAM Pesquisa

**Objetivo:** Pesquisar precedentes em 3 fontes simultaneamente.

| Teammate | Especialidade | Output |
|----------|---------------|--------|
| pesquisador-bnp | STF/STJ (Repercussão Geral, Repetitivos) | inputs/pesquisa-bnp.md |
| pesquisador-cjf | TRFs (todos os regionais) | inputs/pesquisa-cjf.md |
| pesquisador-julia | TRF5 (jurisprudência local) | inputs/pesquisa-julia.md |

**Quando usar:** Antes da análise, para enriquecer com precedentes vinculantes.

**Benefício:** ~3x mais rápido que pesquisar sequencialmente.

---

### TEAM Verificação

**Objetivo:** Verificar conformidade jurídica em 3 aspectos simultaneamente.

| Teammate | Especialidade | Output |
|----------|---------------|--------|
| verificador-honorarios | CPC, leis especiais, temas repetitivos | inputs/verificacao-honorarios.md |
| verificador-calculos | Correção monetária, juros, marcos temporais | inputs/verificacao-calculos.md |
| verificador-remessa | Cabimento/dispensa de remessa necessária | inputs/verificacao-remessa.md |

**Quando usar:** Antes da fundamentação, para evitar erros técnicos.

**Benefício:** Identifica problemas antes da redação final.

---

## Como Usar

### 1. Pipeline Completo com Teams

Use `/pipeline-sentenca-team` para o pipeline completo:

```
/pipeline-sentenca-team data/sentenca/0814624-28.2019.4.05.8100
```

**O que acontece:**
1. Linha do tempo extraída
2. Relatório gerado
3. **TEAM Pesquisa** executa (3 pesquisadores em paralelo)
4. Análise gerada (com precedentes, se disponíveis)
5. **TEAM Verificação** executa (3 verificadores em paralelo)
6. Fundamentação gerada (com correções, se necessárias)
7. Sentença final montada

---

### 2. Criar Novo Team

Use `/criar-team` para criar um team personalizado:

```
/criar-team analise-dual
```

O meta-criador vai perguntar:
1. Qual o objetivo do team?
2. Quantos teammates?
3. Reutilizar agents existentes?
4. Qual agent vai consumir os outputs?
5. Em qual orquestrador integrar?

---

### 3. Executar Team Isoladamente

Os pesquisadores podem ser usados via `/pipeline-pesquisa`:

```
/pipeline-pesquisa "pensão por morte união homoafetiva"
```

---

## Estrutura de Arquivos

Após executar o pipeline com teams:

```
data/sentenca/0814624-28.2019.4.05.8100/
│
├── processo.txt                    # Entrada
├── _team_manifest.md               # Registro de execução dos teams
│
├── 0814624-linha-tempo.md          # Etapa 1
├── 0814624-relatorio.md            # Etapa 2
│
├── inputs/                         # Outputs dos teams
│   ├── pesquisa-bnp.md            # TEAM Pesquisa
│   ├── pesquisa-cjf.md
│   ├── pesquisa-julia.md
│   ├── verificacao-honorarios.md   # TEAM Verificação
│   ├── verificacao-calculos.md
│   └── verificacao-remessa.md
│
├── 0814624-analise.md              # Etapa 3 (usa pesquisas)
├── 0814624-fundamentacao.md        # Etapa 4 (usa verificações)
└── 0814624-sentenca.md             # Etapa 5 (merge final)
```

---

## Lendo o Team Manifest

O arquivo `_team_manifest.md` registra o que aconteceu:

```markdown
### TEAM Pesquisa (Etapa 2.5)
| # | Teammate | Status | Output |
|---|----------|--------|--------|
| 1 | pesquisador-bnp | concluído | inputs/pesquisa-bnp.md |
| 2 | pesquisador-cjf | concluído | inputs/pesquisa-cjf.md |
| 3 | pesquisador-julia | erro | - |

**Resultado:** 2/3 concluídos
```

**Status possíveis:**
- `concluído` - Teammate retornou output válido
- `erro` - Teammate falhou (MCP não respondeu, timeout, etc.)
- `pendente` - Ainda não executou

---

## Comportamento de Falha

### Se um teammate falhar:

O pipeline **continua** com os que funcionaram.

Exemplo: Se `pesquisador-julia` falhar:
- Análise é gerada com precedentes de BNP e CJF
- Manifest registra o erro
- Usuário pode ver que JULIA não foi pesquisado

### Se TODOS teammates falharem:

O pipeline **continua** sem enriquecimento.

Exemplo: Se nenhuma pesquisa funcionar:
- Análise é gerada sem precedentes
- Output menciona: "Análise sem precedentes pesquisados"
- Usuário pode pesquisar manualmente depois

**Filosofia:** Graceful degradation - pipeline nunca trava por falha de team.

---

## Perguntas Frequentes

### Por que usar teams em vez de um agent que faz tudo?

1. **Velocidade:** 3 pesquisas em paralelo = ~3x mais rápido
2. **Especialização:** Cada teammate conhece sua fonte profundamente
3. **Resiliência:** Se um falhar, os outros ainda funcionam
4. **Debugging:** Fácil saber qual fonte não retornou resultado

### Quando NÃO usar teams?

- Se a tarefa é sequencial por natureza (cada etapa depende da anterior)
- Se só precisa de 1 agent (overhead desnecessário)
- Se quer economizar tokens (cada teammate é uma Task separada)

### Como os agents downstream sabem quais inputs existem?

Eles verificam se os arquivos existem antes de ler:

```
SE existir inputs/pesquisa-bnp.md:
    Ler e incorporar
SENÃO:
    Prosseguir sem BNP
```

Os inputs são sempre **opcionais** - o agent funciona com ou sem eles.

### Posso adicionar mais teammates a um team existente?

Sim! Use `/criar-team` e especifique que quer modificar team existente.

Ou edite manualmente:
1. Crie o novo agent em `.claude/agents/<categoria>/`
2. Adicione-o à lista de teammates no orquestrador
3. Atualize o manifest para incluir o novo output

---

## Criando Seu Próprio Team

### Checklist

1. **Defina o objetivo:** O que o team vai fazer?
2. **Identifique teammates:** 2-4 agents especializados
3. **Garanta não-sobreposição:** Cada um faz algo diferente
4. **Defina outputs:** Cada um escreve em arquivo único
5. **Configure downstream:** Agent que vai consumir os outputs
6. **Teste:** Execute e verifique o manifest

### Exemplo: TEAM Análise Dual

**Objetivo:** Analisar caso de duas perspectivas (autor vs réu).

**Teammates:**
- `analisador-autor` → inputs/analise-autor.md
- `analisador-reu` → inputs/analise-reu.md

**Downstream:** Novo agent `consolidador-analise` (a criar) lê ambas e produz síntese imparcial.

---

## Referências

- SPEC v2.8: `.claude/spec/referencias/team-pattern.md`
- Template Manifest: `.claude/spec/templates/team-manifest.md`
- Meta-criador: `.claude/commands/criar-team.md`
- Pipeline com Teams: `.claude/commands/pipeline-sentenca-team.md`

---

## Troubleshooting

### "Nenhuma pesquisa foi encontrada"

Verifique:
1. Os MCPs estão rodando? (`/mcp`)
2. O relatório tem termos pesquisáveis?
3. A sintaxe de busca está correta? (BNP vs CJF vs JULIA)

### "Manifest não foi criado"

A Etapa 0 deve criar o manifest. Verifique:
1. O caminho do workspace está correto?
2. Há permissão para criar arquivos?

### "Fundamentação não usou as verificações"

O fundamentador deve ler `inputs/verificacao-*.md`. Verifique:
1. Os arquivos existem na pasta inputs?
2. O prompt do fundamentador menciona os inputs opcionais?

---

**Playbook:** Agent Teams
**Framework:** Super Jurista v2.8
