# Blueprint Schema — Contrato do motor `/criar-sistema`

> O blueprint é o **contrato determinístico** entre a Fase A (planejamento) e as Fases
> B/C/D (geração, validação, consolidação). Ele é gravado como `blueprint.json` no staging
> e consumido por cada subagente gerador SEM que ninguém precise perguntar nada durante a
> geração. Se um campo necessário falta, o gerador correspondente não é determinístico —
> logo, a Fase A só termina quando o blueprint está completo e sem referência circular.

Por que JSON e não Markdown: o blueprint é lido programaticamente por múltiplos geradores;
JSON é inequívoco de parsear. O relatório legível ao usuário (Fase D) é derivado do JSON,
não o JSON cru.

---

## Schema

```json
{
  "meta": {
    "versao": "1.0",
    "nome_sistema": "kebab-case-unico",
    "descricao": "Uma frase clara do que o sistema faz",
    "modo_convencao": "soberano | superjurista | superlivro | generico",
    "target_dir": "caminho absoluto do projeto-alvo (cwd da invocação)",
    "staging_dir": "caminho absoluto do staging temporário",
    "data_geracao": "YYYY-MM-DD (via Bash date)"
  },

  "entrada": {
    "tipo": "string | path | json",
    "descricao": "O que o usuário passa ao orquestrador gerado",
    "argument_hint": "texto do campo argument-hint"
  },
  "saida": {
    "tipo": "file | directory | stdout",
    "descricao": "O artefato final que o sistema gerado produz",
    "path_padrao": "convenção de nomenclatura da saída"
  },

  "agentes": [
    {
      "slug": "nome-kebab-case-unico",
      "capacidade": "verbo no infinitivo + objeto específico (UM verbo principal)",
      "categoria": "extracao | analise | pesquisa | revisao | redacao",
      "entrada_tipo": "tipo genérico (nunca caminho)",
      "saida_tipo": "tipo genérico",
      "grava_saida": true,
      "sinalizador_inicio": "[INICIO_SLUG]",
      "sinalizador_fim": "[FIM_SLUG]",
      "modelo": "opus | sonnet | haiku",
      "cor": "yellow | green | red | blue",
      "path_destino": ".claude/agents/<categoria>/<slug>.md",
      "status": "criar | reusar | absorver",
      "path_existente": null,
      "emenda_sugerida": null,
      "extensoes_dominio": ["hierarquia_de_autoridade", "ecos"]
    }
  ],

  "skills": [
    {
      "slug": "nome-metodologia-dominio",
      "tipo_skill": "disciplina | tecnica | padrao | referencia",
      "descricao_cso": "Use when…",
      "palavras_chave": ["termo1", "termo2"],
      "executa_scripts": false,
      "cenario_red": "Cenário de pressão p/ o teste RED (só se tipo=disciplina)",
      "path_destino": ".claude/skills/<slug>/",
      "status": "criar | reusar | absorver",
      "path_existente": null,
      "emenda_sugerida": null
    }
  ],

  "orquestrador": {
    "slug": "nome-pipeline-dominio",
    "tipo": "skill | command",
    "path_destino": ".claude/skills/<slug>/SKILL.md | .claude/commands/<slug>.md",
    "descricao_cso": "Use when…",
    "argument_hint": "texto do argumento",
    "allowed_tools": ["Read", "Write", "Task", "Bash", "TodoWrite"],
    "fases": [
      {
        "numero": 0,
        "nome": "Preparação",
        "agente_slug": null,
        "entrada": "$ARGUMENTS",
        "saida": "$WORKSPACE",
        "descricao": "Calcular variáveis e criar workspace",
        "paralelo_com": []
      },
      {
        "numero": 1,
        "nome": "Nome da Fase",
        "agente_slug": "slug-do-agente",
        "entrada": "$WORKSPACE/<entrada>",
        "saida": "$WORKSPACE/<saida>",
        "descricao": "O que transforma",
        "paralelo_com": []
      }
    ]
  },

  "dependencias": {
    "descricao": "DAG: arestas do orquestrador para cada agente/skill que ele usa",
    "orquestrador_depende_de": ["slug-agente-1", "slug-agente-2", "slug-skill-1"]
  },

  "validacao": {
    "_escala": "0-100 (ver validador-de-artefato.md)",
    "score_minimo_agente": 85,
    "score_minimo_skill": 85,
    "score_minimo_orquestrador": 90,
    "max_tentativas_regeracao": 2
  }
}
```

---

## Campos críticos para a geração ser determinística

- **`orquestrador.fases[].agente_slug`** vincula cada fase do pipeline ao agente que a
  executa. É o que permite ao `gerador-de-orquestrador` montar o prompt de despacho exato
  (com o `path_destino` correto do agente) sem adivinhar.
- **`agentes[].sinalizador_inicio` / `sinalizador_fim`** são a base da verificação 2b do
  `validador-de-coerencia`: o `[FIM]` de uma etapa deve casar com o que a etapa seguinte
  espera como entrada. Na v3.0 também viram as âncoras `inicio`/`fim` do `ETAPAS` do gate
  `verificar_<sistema>.py` (o sufixo do arquivo vem de `orquestrador.fases[].saida`; `contem`
  e `minimo` são inferidos pelo `gerador-de-orquestrador`, default `minimo=500`).
- **`agentes[].status`** distingue `criar` (gerar agora), `reusar` (agente já existe em
  `path_existente` — só registrar como dependência, não regerar) e `absorver` (capacidade
  QUASE idêntica já existe em `path_existente`: não gerar peça nova; o pipeline trata como
  `reusar` e a `emenda_sugerida` — uma frase dizendo o que acrescentar ao artefato existente —
  vai ao manifesto para aplicação posterior, fora do commit atômico). Resolve colisão de
  capacidade reaproveitando/emendando em vez de duplicar (regra de nascimento).
- **`dependencias.orquestrador_depende_de`** determina a ordem de geração: a Fase B só gera
  o orquestrador depois que todos os slugs aqui listados existirem (no staging se status:criar,
  no target se status:reusar).
- **`agentes[].grava_saida`**: se `true`, o agente grava o próprio output em arquivo → recebe a
  ferramenta `Write`. Se `false`, só retorna texto (o orquestrador grava) → apenas `Read`. No
  estilo SuperLivro os agentes tipicamente gravam seu artefato (`true`).

---

## Regras de integridade do blueprint (verificadas ao fim da Fase A)

1. Todo `slug` é único dentro do blueprint E não colide com artefato existente no
   `target_dir` (Glob). Em colisão: prefixar com `nome_sistema` ou marcar `status: reusar`
   se a capacidade for idêntica.
1-bis. **Scout de capacidade (regra de nascimento):** antes de marcar qualquer peça como
   `criar`, buscar a capacidade nas descriptions dos artefatos existentes (target, global e
   mapa do ecossistema). Capacidade idêntica → `reusar`; quase idêntica → `absorver` com
   `path_existente` + `emenda_sugerida`. Toda peça `absorver` DEVE ter ambos os campos
   preenchidos (sem eles a coerência não resolve a referência).
2. Toda `capacidade` de agente tem **um** verbo principal (atomicidade — L2). Capacidade
   com verbos conjugados por "e" é sinal de agente não-atômico → subdividir.
3. Todo `agente_slug` referenciado em `orquestrador.fases` existe na lista `agentes`.
4. O grafo `dependencias` é acíclico (agentes e skills são folhas; só o orquestrador
   aponta para eles).
5. `meta.nome_sistema`, `entrada`, `saida` e ao menos 1 agente estão preenchidos. Se a
   intenção não permite preencher isso com segurança, a Fase A emite `[SISTEMA_INSUFICIENTE]`
   e PARA (ver trava de viabilidade no SKILL.md).
