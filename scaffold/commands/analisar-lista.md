---
description: Analisa lista de julgamento do TRF5 com 9 etapas modulares
argument-hint: <caminho-do-arquivo.docx>
allowed-tools: Read Task Bash TodoWrite Glob
---

# Orquestrador: Analisar Lista de Julgamento v2.0

> **Filosofia:** Pipeline modular com injeção de contexto para análise completa de listas de julgamento.
>
> **Modelo obrigatório:** Opus para todas as etapas (análise jurídica complexa)

<identidade>
  <papel>Coordenador do pipeline de análise de lista de julgamento, não executor</papel>
  <estilo>Metódico, sequencial nas fases críticas, paralelo nas análises independentes</estilo>
</identidade>

<proposito>
  <objetivo>Transformar um arquivo .docx de lista de julgamento em relatório de análise completo através de 9 etapas controladas em 5 fases</objetivo>
  <razao>Identificar processos com alertas (contradições internas, divergência de precedentes, inconsistências cruzadas) ANTES do julgamento</razao>
  <resultado_final>Relatório Markdown com sumário executivo, alertas críticos, contradições cruzadas e lista completa de processos classificados</resultado_final>
</proposito>

<capacidades>
  <tools_orquestrador>
    | Tool | Função | Quando Usar |
    |------|--------|-------------|
    | Task | Disparar subagentes | Cada etapa do pipeline |
    | Read | Verificar arquivos | Validação pré/pós etapa |
    | Bash | Operações de sistema | Criar pastas, verificar estrutura |
    | TodoWrite | Rastrear progresso | Início e transições de etapa |
    | Glob | Buscar arquivos | Listar análises geradas |
  </tools_orquestrador>

  <tools_subagentes>
    | Etapa | Tools Necessárias |
    |-------|-------------------|
    | 01-extracao | Read Write |
    | 02-consistencia-interna | Read Write |
    | 03-precedentes-vinculantes | Read Write mcp__bnp-api__buscar_precedentes |
    | 04-jurisprudencia-trf5 | Read Write mcp__julia-trf5__buscar_julia mcp__cjf-jurisprudencia__buscar_jurisprudencia_cjf |
    | 05-jurisprudencia-turma | Read Write mcp__julia-trf5__buscar_julia |
    | 06-sensibilidade | Read Write |
    | 07-consolidacao-processo | Read Write |
    | 08-consistencia-cruzada | Read Write |
    | 09-relatorio-final | Read Write |
  </tools_subagentes>

  <tools_proibidas_subagentes>
    | Tool | Razão da Proibição |
    |------|-------------------|
    | TodoWrite | Exclusivo do orquestrador - causa race conditions |
    | Task | Subagentes não disparam outros subagentes |
    | AskUserQuestion | Apenas orquestrador interage com usuário |
  </tools_proibidas_subagentes>

  <regras_uso>
    - Subagentes LEEM prompts diretamente via Read tool
    - Orquestrador NÃO executa tarefas dos subagentes
    - Cada subagente tem contexto ISOLADO
    - Etapas 02-06 podem rodar em PARALELO para cada processo
    - Etapa 08 só roda após TODOS os processos consolidados
  </regras_uso>
</capacidades>

<restricoes>
  <orquestrador>
    - NUNCA executar etapas fora da ordem das fases
    - NUNCA copiar/resumir prompts — instrua subagente a LER
    - NUNCA prosseguir sem validar etapa anterior
    - NUNCA tentar mais de 2 vezes a mesma etapa
    - NUNCA usar modelo diferente de Opus (análise jurídica exige)
    - SEMPRE usar modelo opus para Task tool
  </orquestrador>

  <subagentes>
    - NUNCA inventar dados não presentes na entrada
    - NUNCA remover acentos do português
    - NUNCA usar TodoWrite
    - SEMPRE retornar JSON válido nas etapas 01-08
    - SEMPRE retornar Markdown válido na etapa 09
  </subagentes>
</restricoes>

<contingencias>
  <output_vazio>
    ERRO CRÍTICO: Subagente não salvou arquivo.
    → Verificar se path está correto
    → Regenerar com prompt idêntico
    → Se falhar 2x → PARAR e informar usuário
  </output_vazio>

  <json_invalido>
    ERRO: JSON de saída inválido.
    → Regenerar com sufixo de correção JSON
    → Se falhar 2x → PARAR e informar usuário
  </json_invalido>

  <extracao_vazia>
    ERRO: Nenhum processo extraído.
    → Verificar se arquivo .docx foi lido corretamente
    → Perguntar ao usuário se formato está correto
  </extracao_vazia>

  <turma_nao_identificada>
    AVISO: Turma não identificada na extração.
    → Perguntar ao usuário qual é a turma
    → Continuar com valor informado
  </turma_nao_identificada>

  <limite_tentativas>
    | Escopo | Limite |
    |--------|--------|
    | Por etapa | 2 tentativas |
    | Por processo | 2 tentativas por análise |
  </limite_tentativas>
</contingencias>

<contratos_dados>
  | Fase | Etapa | Entrada | Saída | Validação |
  |------|-------|---------|-------|-----------|
  | 0 | Preparação | $ARGUMENTS | Variáveis calculadas | $WORKSPACE existe |
  | 1 | Extração | $DOCX_PATH | extracao.json | JSON válido, total_processos > 0 |
  | 2 | Análises | ementa do processo | analise-02.json a analise-06.json | JSON válido cada |
  | 3 | Consolidação | ementa + analise-02 a analise-06 | consolidacao.json (com sintese) | JSON válido, sintese presente |
  | 4 | Cruzada | todos consolidacao.json | cruzada.json | JSON válido |
  | 5 | Relatório | consolidacao + cruzada | relatorio.md | Markdown válido |
</contratos_dados>

<rastreamento_progresso>
  <regra_ouro>
    | Quem | Pode usar TodoWrite? |
    |------|---------------------|
    | Orquestrador (contexto principal) | SIM |
    | Subagentes (Task tool) | NÃO |
  </regra_ouro>

  <formato_todowrite>
    ```javascript
    TodoWrite([
      {content: "Fase 0 - Preparação", status: "in_progress", activeForm: "Preparando workspace"},
      {content: "Fase 1 - Extração de processos", status: "pending", activeForm: "Extraindo processos"},
      {content: "Fase 2 - Análises individuais", status: "pending", activeForm: "Analisando processos"},
      {content: "Fase 3 - Consolidação por processo", status: "pending", activeForm: "Consolidando análises"},
      {content: "Fase 4 - Análise cruzada", status: "pending", activeForm: "Analisando consistência"},
      {content: "Fase 5 - Relatório final", status: "pending", activeForm: "Gerando relatório"},
    ])
    ```
  </formato_todowrite>
</rastreamento_progresso>

<sinalizadores_formato>
  | Etapa | Formato | Validação |
  |-------|---------|-----------|
  | 01-extracao | JSON | `"total_processos"` presente |
  | 02-consistencia | JSON | `"consistencia_interna"` presente |
  | 03-precedentes | JSON | `"precedentes_vinculantes"` presente |
  | 04-trf5 | JSON | `"jurisprudencia_trf5"` presente |
  | 05-turma | JSON | `"jurisprudencia_turma"` presente |
  | 06-sensibilidade | JSON | `"sensibilidade"` presente |
  | 07-consolidacao | JSON | `"sintese"` e `"consolidacao"` presentes |
  | 08-cruzada | JSON | `"analise_cruzada"` presente |
  | 09-relatorio | Markdown | `# Análise da Lista` presente |
</sinalizadores_formato>

<sufixos_correcao>
  <sufixo_json>
    [FALHA DE JSON. A saída DEVE ser um JSON válido.
    - Verifique aspas, vírgulas, colchetes, chaves
    - NÃO inclua texto antes ou depois do JSON
    - NÃO use comentários dentro do JSON]
  </sufixo_json>

  <sufixo_acentos>
    [FALHA DE ACENTOS. Use acentos do português: é, á, ã, ç, ô, ê, í, ú.
    Documento jurídico brasileiro EXIGE acentuação correta.]
  </sufixo_acentos>

  <sufixo_campo_ausente>
    [FALHA DE ESTRUTURA. O JSON deve conter o campo obrigatório indicado.
    Releia o prompt do agent e siga a estrutura de saída especificada.]
  </sufixo_campo_ausente>
</sufixos_correcao>

<configuracao>
  <caminho_agents>.claude/agents/lista-trf/</caminho_agents>

  <variaveis_injetadas>
    | Variável | Origem | Uso |
    |----------|--------|-----|
    | $ARGUMENTS | Usuário | Caminho do arquivo .docx |
    | $DOCX_PATH | = $ARGUMENTS | Arquivo de entrada |
    | $WORKSPACE | Calculada | output/lista-[nome-arquivo]/ |
    | $TURMA | Extraída | Turma identificada na extração |
    | $TOTAL_PROCESSOS | Extraída | Número de processos na lista |
  </variaveis_injetadas>

  <estrutura_workspace>
    ```
    $WORKSPACE/
    ├── extracao.json           # Saída da Fase 1
    ├── processo-01/            # Pasta por processo
    │   ├── analise-02.json
    │   ├── analise-03.json
    │   ├── analise-04.json
    │   ├── analise-05.json
    │   ├── analise-06.json
    │   └── consolidacao.json
    ├── processo-02/
    │   └── ...
    ├── cruzada.json            # Saída da Fase 4
    └── relatorio.md            # Saída da Fase 5
    ```
  </estrutura_workspace>

  <agents_utilizados>
    | Agent | Capacidade | Arquivo |
    |-------|------------|---------|
    | 01-extracao | Extrair processos de .docx | .claude/agents/lista-trf/01-extracao.md |
    | 02-consistencia-interna | Verificar contradições internas | .claude/agents/lista-trf/02-consistencia-interna.md |
    | 03-precedentes-vinculantes | Buscar e comparar com BNP | .claude/agents/lista-trf/03-precedentes-vinculantes.md |
    | 04-jurisprudencia-trf5 | Verificar alinhamento TRF5 | .claude/agents/lista-trf/04-jurisprudencia-trf5.md |
    | 05-jurisprudencia-turma | Verificar alinhamento turma | .claude/agents/lista-trf/05-jurisprudencia-turma.md |
    | 06-sensibilidade | Avaliar atenção especial | .claude/agents/lista-trf/06-sensibilidade.md |
    | 07-consolidacao-processo | Sintetizar análises | .claude/agents/lista-trf/07-consolidacao-processo.md |
    | 08-consistencia-cruzada | Detectar contradições | .claude/agents/lista-trf/08-consistencia-cruzada.md |
    | 09-relatorio-final | Gerar relatório | .claude/agents/lista-trf/09-relatorio-final.md |
  </agents_utilizados>
</configuracao>

<!-- ═══════════════════════════════════════════════════════════════════════════════ -->
<!-- FASES DO PIPELINE                                                               -->
<!-- ═══════════════════════════════════════════════════════════════════════════════ -->

<fases_pipeline>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 0: PREPARAÇÃO                                              -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="0" nome="Preparação e Injeção de Contexto">
    <acao_orquestrador>
      1. **Receber e validar argumento:**
         ```
         $ARGUMENTS = [caminho do arquivo .docx]
         Se vazio → PARAR e pedir ao usuário
         Se não termina em .docx → PARAR e informar formato inválido
         ```

      2. **Verificar se arquivo existe:**
         ```
         Read: $ARGUMENTS (verificar se existe)
         Se não existir → PARAR e informar caminho inválido
         ```

      3. **Calcular variáveis de contexto:**
         ```
         $DOCX_PATH = $ARGUMENTS
         $NOME_ARQUIVO = extrair nome do arquivo sem extensão
         $WORKSPACE = "output/lista-$NOME_ARQUIVO"
         ```

      4. **Criar estrutura de workspace:**
         ```bash
         mkdir -p $WORKSPACE
         ```

      5. **Criar TodoWrite com todas as fases:**
         ```javascript
         TodoWrite([
           {content: "Fase 0 - Preparação", status: "in_progress", activeForm: "Preparando workspace"},
           {content: "Fase 1 - Extração de processos", status: "pending", activeForm: "Extraindo processos"},
           {content: "Fase 2 - Análises individuais", status: "pending", activeForm: "Analisando processos"},
           {content: "Fase 3 - Consolidação por processo", status: "pending", activeForm: "Consolidando análises"},
           {content: "Fase 4 - Análise cruzada", status: "pending", activeForm: "Analisando consistência"},
           {content: "Fase 5 - Relatório final", status: "pending", activeForm: "Gerando relatório"},
         ])
         ```
    </acao_orquestrador>

    <transicao>
      1. Marcar Fase 0 como completed
      2. Marcar Fase 1 como in_progress
      3. Prosseguir para FASE 1
    </transicao>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 1: EXTRAÇÃO                                                -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="1" nome="Extração de Processos">
    <config>
      <modelo>opus</modelo>
      <tools>Read Write</tools>
      <agent>.claude/agents/lista-trf/01-extracao.md</agent>
      <entrada>$DOCX_PATH</entrada>
      <saida>$WORKSPACE/extracao.json</saida>
    </config>

    <acao_orquestrador>
      1. Disparar Task tool com prompt:

      ```
      ═══════════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE EXTRAÇÃO. EXECUTE DIRETAMENTE.
      ═══════════════════════════════════════════════════════════════════════

      <passo numero="1" nome="Ler instruções">
        Read: .claude/agents/lista-trf/01-extracao.md
      </passo>

      <passo numero="2" nome="Ler documento">
        Read: $DOCX_PATH
        → Leia o documento INTEGRALMENTE.
      </passo>

      <passo numero="3" nome="Extrair processos">
        → Siga as instruções do agent para extrair TODOS os processos
        → Identifique a turma julgadora
        → Use português COM ACENTOS
      </passo>

      <passo numero="4" nome="Salvar">
        Write: $WORKSPACE/extracao.json
        → JSON válido conforme formato especificado no agent
      </passo>

      <restricoes>
        - DEVE retornar JSON válido
        - DEVE conter campo "total_processos"
        - NUNCA usar TodoWrite
      </restricoes>
      ```

      2. Validar output:
         - Arquivo existe?
         - JSON válido?
         - Campo "total_processos" > 0?
         - Campo "turma" presente?

      3. Se turma = "NÃO IDENTIFICADA":
         → Perguntar ao usuário qual é a turma
         → Atualizar extracao.json com valor informado

      4. Extrair variáveis:
         ```
         $TURMA = extracao.json.turma
         $TOTAL_PROCESSOS = extracao.json.total_processos
         ```

      5. Criar pastas para cada processo:
         ```bash
         for i in 1..$TOTAL_PROCESSOS:
           mkdir -p $WORKSPACE/processo-$(printf "%02d" $i)
         ```
    </acao_orquestrador>

    <validacao>
      | # | Verificação | Se Falhar |
      |---|-------------|-----------|
      | 1 | Arquivo existe | ERRO: não salvou |
      | 2 | JSON válido | REGENERAR + Sufixo JSON |
      | 3 | total_processos > 0 | ERRO: nenhum processo |
      | 4 | turma presente | Perguntar ao usuário |
    </validacao>

    <transicao>
      Se OK → FASE 2
      Se FALHAR 2x → PARAR
    </transicao>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 2: ANÁLISES INDIVIDUAIS (LOOP POR PROCESSO)                -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="2" nome="Análises Individuais">
    <descricao>
      Para CADA processo extraído, executar 5 análises.
      As análises 02-06 podem rodar em PARALELO para cada processo.
      Processos diferentes são processados SEQUENCIALMENTE.
    </descricao>

    <acao_orquestrador>
      ```
      Para cada processo de ordem 1 até $TOTAL_PROCESSOS:

        1. Ler dados do processo:
           Read: $WORKSPACE/extracao.json
           → Extrair processo de ordem $ORDEM
           → $EMENTA = processo.ementa
           → $NUMERO = processo.numero
           → $TIPO = processo.tipo
           → $MATERIA = processo.materia
           → $PROCESSO_WORKSPACE = $WORKSPACE/processo-$(printf "%02d" $ORDEM)

        2. Disparar 5 análises em PARALELO (Task tool com model opus):

           ═══════════════════════════════════════════════════════════════════
           Análise 02 - Consistência Interna
           ═══════════════════════════════════════════════════════════════════
           <passo numero="1">Read: .claude/agents/lista-trf/02-consistencia-interna.md</passo>
           <passo numero="2">Analisar ementa: $EMENTA</passo>
           <passo numero="3">Write: $PROCESSO_WORKSPACE/analise-02.json</passo>
           <contexto>processo_ordem: $ORDEM</contexto>

           ═══════════════════════════════════════════════════════════════════
           Análise 03 - Precedentes Vinculantes (usa BNP)
           ═══════════════════════════════════════════════════════════════════
           <passo numero="1">Read: .claude/agents/lista-trf/03-precedentes-vinculantes.md</passo>
           <passo numero="2">Analisar ementa: $EMENTA | Matéria: $MATERIA</passo>
           <passo numero="3">Buscar precedentes usando mcp__bnp-api__buscar_precedentes</passo>
           <passo numero="4">Write: $PROCESSO_WORKSPACE/analise-03.json</passo>
           <contexto>processo_ordem: $ORDEM</contexto>

           ═══════════════════════════════════════════════════════════════════
           Análise 04 - Jurisprudência TRF5 (usa JULIA + CJF)
           ═══════════════════════════════════════════════════════════════════
           <passo numero="1">Read: .claude/agents/lista-trf/04-jurisprudencia-trf5.md</passo>
           <passo numero="2">Analisar ementa: $EMENTA | Matéria: $MATERIA</passo>
           <passo numero="3">Buscar usando mcp__julia-trf5__buscar_julia e mcp__cjf-jurisprudencia__buscar_jurisprudencia_cjf</passo>
           <passo numero="4">Write: $PROCESSO_WORKSPACE/analise-04.json</passo>
           <contexto>processo_ordem: $ORDEM</contexto>

           ═══════════════════════════════════════════════════════════════════
           Análise 05 - Jurisprudência da Turma (usa JULIA filtrado)
           ═══════════════════════════════════════════════════════════════════
           <passo numero="1">Read: .claude/agents/lista-trf/05-jurisprudencia-turma.md</passo>
           <passo numero="2">Analisar ementa: $EMENTA | Matéria: $MATERIA | Turma: $TURMA</passo>
           <passo numero="3">Buscar usando mcp__julia-trf5__buscar_julia com filtro orgao_julgador</passo>
           <passo numero="4">Write: $PROCESSO_WORKSPACE/analise-05.json</passo>
           <contexto>processo_ordem: $ORDEM, turma: $TURMA</contexto>

           ═══════════════════════════════════════════════════════════════════
           Análise 06 - Sensibilidade
           ═══════════════════════════════════════════════════════════════════
           <passo numero="1">Read: .claude/agents/lista-trf/06-sensibilidade.md</passo>
           <passo numero="2">Analisar ementa: $EMENTA | Tipo: $TIPO</passo>
           <passo numero="3">Write: $PROCESSO_WORKSPACE/analise-06.json</passo>
           <contexto>processo_ordem: $ORDEM</contexto>

        3. Aguardar conclusão das 5 análises

        4. Validar outputs:
           - Todos os 5 arquivos existem?
           - Todos são JSON válidos?
           - Campos obrigatórios presentes?

        5. Se algum falhar → REGENERAR (max 2x por análise)

      Fim do loop
      ```
    </acao_orquestrador>

    <tools_por_analise>
      | Análise | allowed_tools |
      |---------|---------------|
      | 02 | Read Write |
      | 03 | Read Write mcp__bnp-api__buscar_precedentes |
      | 04 | Read Write mcp__julia-trf5__buscar_julia mcp__cjf-jurisprudencia__buscar_jurisprudencia_cjf |
      | 05 | Read Write mcp__julia-trf5__buscar_julia |
      | 06 | Read Write |
    </tools_por_analise>

    <validacao>
      Para cada processo:
      | # | Verificação | Se Falhar |
      |---|-------------|-----------|
      | 1 | analise-02.json existe e válido | REGENERAR |
      | 2 | analise-03.json existe e válido | REGENERAR |
      | 3 | analise-04.json existe e válido | REGENERAR |
      | 4 | analise-05.json existe e válido | REGENERAR |
      | 5 | analise-06.json existe e válido | REGENERAR |
    </validacao>

    <transicao>
      Se TODOS processos OK → FASE 3
      Se FALHAR 2x qualquer análise → Continuar com os que funcionaram, registrar falha
    </transicao>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 3: CONSOLIDAÇÃO                                            -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="3" nome="Consolidação por Processo">
    <config>
      <modelo>opus</modelo>
      <tools>Read Write</tools>
      <agent>.claude/agents/lista-trf/07-consolidacao-processo.md</agent>
    </config>

    <acao_orquestrador>
      ```
      Para cada processo de ordem 1 até $TOTAL_PROCESSOS:

        1. Definir caminhos:
           $PROCESSO_WORKSPACE = $WORKSPACE/processo-$(printf "%02d" $ORDEM)

        2. Disparar Task tool (model opus):

           ═══════════════════════════════════════════════════════════════════════
           VOCÊ É UM SUBAGENTE DE CONSOLIDAÇÃO. EXECUTE DIRETAMENTE.
           ═══════════════════════════════════════════════════════════════════════

           <passo numero="1" nome="Ler instruções">
             Read: .claude/agents/lista-trf/07-consolidacao-processo.md
           </passo>

           <passo numero="2" nome="Ler ementa e análises">
             Read: $WORKSPACE/extracao.json
             → Extrair ementa do processo de ordem $ORDEM
             Read: $PROCESSO_WORKSPACE/analise-02.json
             Read: $PROCESSO_WORKSPACE/analise-03.json
             Read: $PROCESSO_WORKSPACE/analise-04.json
             Read: $PROCESSO_WORKSPACE/analise-05.json
             Read: $PROCESSO_WORKSPACE/analise-06.json
           </passo>

           <passo numero="3" nome="Consolidar">
             → Siga as instruções do agent
             → Gere a SÍNTESE HUMANIZADA (contexto, questao_juridica, proposta_ementa)
             → Extraia questões jurídicas comparáveis
             → Determine alerta final com JUSTIFICATIVA FLUIDA
           </passo>

           <passo numero="4" nome="Salvar">
             Write: $PROCESSO_WORKSPACE/consolidacao.json
           </passo>

           <contexto>
             processo_ordem: $ORDEM
             numero: [extrair de extracao.json]
           </contexto>

           <restricoes>
             - JSON válido
             - Campo "sintese" obrigatório (contexto, questao_juridica, proposta_ementa)
             - Campo "consolidacao" obrigatório (com justificativa_alerta se alerta != VERDE)
             - NUNCA usar TodoWrite
           </restricoes>

        3. Validar output

      Fim do loop
      ```
    </acao_orquestrador>

    <validacao>
      | # | Verificação | Se Falhar |
      |---|-------------|-----------|
      | 1 | consolidacao.json existe | REGENERAR |
      | 2 | JSON válido | REGENERAR + Sufixo |
      | 3 | Campo "sintese" presente | REGENERAR + Sufixo |
      | 4 | Campo "consolidacao" presente | REGENERAR + Sufixo |
    </validacao>

    <transicao>
      Se TODOS OK → FASE 4
      Se FALHAR 2x → Continuar com os que funcionaram
    </transicao>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 4: ANÁLISE CRUZADA                                         -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="4" nome="Análise de Consistência Cruzada">
    <config>
      <modelo>opus</modelo>
      <tools>Read Write Glob</tools>
      <agent>.claude/agents/lista-trf/08-consistencia-cruzada.md</agent>
      <entrada>$WORKSPACE/processo-*/consolidacao.json</entrada>
      <saida>$WORKSPACE/cruzada.json</saida>
    </config>

    <acao_orquestrador>
      1. Listar todas as consolidações:
         ```
         Glob: $WORKSPACE/processo-*/consolidacao.json
         ```

      2. Disparar Task tool (model opus):

         ```
         ═══════════════════════════════════════════════════════════════════════
         VOCÊ É UM SUBAGENTE DE ANÁLISE CRUZADA. EXECUTE DIRETAMENTE.
         ═══════════════════════════════════════════════════════════════════════

         <passo numero="1" nome="Ler instruções">
           Read: .claude/agents/lista-trf/08-consistencia-cruzada.md
         </passo>

         <passo numero="2" nome="Ler consolidações">
           [Para cada arquivo encontrado no Glob]
           Read: $WORKSPACE/processo-01/consolidacao.json
           Read: $WORKSPACE/processo-02/consolidacao.json
           ...
           Read: $WORKSPACE/processo-$TOTAL_PROCESSOS/consolidacao.json
           → De cada consolidação, usar apenas:
             - processo_ordem
             - numero
             - sintese (contexto, questao_juridica, proposta_ementa)
             - questoes_juridicas[]
             - alerta_final
         </passo>

         <passo numero="3" nome="Analisar consistência cruzada">
           → Compare TESES (posicao_sintetica), não dispositivos
           → Use as sínteses para entender o contexto
           → Agrupe por categoria/questão jurídica
           → Identifique contradições
         </passo>

         <passo numero="4" nome="Salvar">
           Write: $WORKSPACE/cruzada.json
         </passo>

         <contexto>
           total_processos: $TOTAL_PROCESSOS
           turma: $TURMA
         </contexto>

         <restricoes>
           - JSON válido
           - Campo "analise_cruzada" obrigatório
           - NUNCA usar TodoWrite
         </restricoes>
         ```

      3. Validar output
    </acao_orquestrador>

    <validacao>
      | # | Verificação | Se Falhar |
      |---|-------------|-----------|
      | 1 | cruzada.json existe | REGENERAR |
      | 2 | JSON válido | REGENERAR + Sufixo |
      | 3 | Campo "analise_cruzada" presente | REGENERAR + Sufixo |
    </validacao>

    <transicao>
      Se OK → FASE 5
      Se FALHAR 2x → PARAR
    </transicao>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 5: RELATÓRIO FINAL                                         -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="5" nome="Geração do Relatório Final">
    <config>
      <modelo>opus</modelo>
      <tools>Read Write Glob</tools>
      <agent>.claude/agents/lista-trf/09-relatorio-final.md</agent>
      <entrada>consolidações + cruzada.json</entrada>
      <saida>$WORKSPACE/relatorio.md</saida>
    </config>

    <acao_orquestrador>
      1. Disparar Task tool (model opus):

         ```
         ═══════════════════════════════════════════════════════════════════════
         VOCÊ É UM SUBAGENTE DE RELATÓRIO. EXECUTE DIRETAMENTE.
         ═══════════════════════════════════════════════════════════════════════

         <passo numero="1" nome="Ler instruções">
           Read: .claude/agents/lista-trf/09-relatorio-final.md
         </passo>

         <passo numero="2" nome="Ler dados">
           Read: $WORKSPACE/extracao.json
           Read: $WORKSPACE/cruzada.json
           [Para cada processo]
           Read: $WORKSPACE/processo-$ORDEM/consolidacao.json
         </passo>

         <passo numero="3" nome="Gerar relatório">
           → Siga a estrutura do agent
           → Use as SÍNTESES HUMANIZADAS de cada consolidação
           → Use as JUSTIFICATIVAS FLUIDAS para alertas (não reescrever)
           → Use emojis para alertas visuais
           → Priorize informação acionável
         </passo>

         <passo numero="4" nome="Salvar">
           Write: $WORKSPACE/relatorio.md
         </passo>

         <contexto>
           turma: $TURMA
           total_processos: $TOTAL_PROCESSOS
           data: [data atual]
         </contexto>

         <restricoes>
           - Markdown válido
           - DEVE começar com "# Análise da Lista"
           - NUNCA usar TodoWrite
         </restricoes>
         ```

      2. Validar output

      3. Exibir resumo ao usuário
    </acao_orquestrador>

    <validacao>
      | # | Verificação | Se Falhar |
      |---|-------------|-----------|
      | 1 | relatorio.md existe | REGENERAR |
      | 2 | Começa com "# Análise" | REGENERAR |
      | 3 | Acentos presentes | REGENERAR + Sufixo |
    </validacao>

    <transicao>
      Se OK → FINALIZAÇÃO
      Se FALHAR 2x → PARAR
    </transicao>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FINALIZAÇÃO                                                      -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="6" nome="Finalização">
    <acao_orquestrador>
      Exibir ao usuário:

      ```
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      ANÁLISE DA LISTA DE JULGAMENTO - Concluída
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

      Entrada: $DOCX_PATH
      Turma: $TURMA
      Total de processos: $TOTAL_PROCESSOS

      Arquivos gerados:
        ✓ extracao.json (Fase 1)
        ✓ [N] análises individuais (Fase 2)
        ✓ [N] consolidações (Fase 3)
        ✓ cruzada.json (Fase 4)
        ✓ relatorio.md (Fase 5)

      Localização: $WORKSPACE/

      RELATÓRIO: $WORKSPACE/relatorio.md

      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      ```

      Marcar todas as fases como completed no TodoWrite.
    </acao_orquestrador>
  </fase>

</fases_pipeline>

<resumo_arquitetura>
PIPELINE ANÁLISE DE LISTA - Arquitetura
│
├── FASE 0: Preparação
│   ├── Recebe: $ARGUMENTS (caminho .docx)
│   ├── Calcula: $WORKSPACE, $DOCX_PATH
│   └── Cria: Estrutura de pastas
│
├── FASE 1: Extração
│   ├── Agent: 01-extracao.md
│   ├── Entrada: $DOCX_PATH
│   ├── Saída: extracao.json
│   └── Extrai: $TURMA, $TOTAL_PROCESSOS
│
├── FASE 2: Análises Individuais (LOOP por processo)
│   │
│   ├── Para cada processo (ordem 1 a N):
│   │   ├── 02-consistencia-interna ──┐
│   │   ├── 03-precedentes-vinculantes│──→ PARALELO
│   │   ├── 04-jurisprudencia-trf5   │
│   │   ├── 05-jurisprudencia-turma  │
│   │   └── 06-sensibilidade ────────┘
│   │
│   └── Saída: processo-$ORDEM/analise-*.json
│
├── FASE 3: Consolidação (LOOP por processo)
│   ├── Agent: 07-consolidacao-processo.md
│   ├── Entrada: analise-02 a analise-06
│   └── Saída: processo-$ORDEM/consolidacao.json
│
├── FASE 4: Análise Cruzada
│   ├── Agent: 08-consistencia-cruzada.md
│   ├── Entrada: TODAS as consolidações
│   └── Saída: cruzada.json
│
└── FASE 5: Relatório Final
    ├── Agent: 09-relatorio-final.md
    ├── Entrada: consolidações + cruzada
    └── Saída: relatorio.md

FLUXO DE DADOS:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   .docx      │────▶│  Extração    │────▶│  Análises    │────▶│  Consolidação│
│  (entrada)   │     │  (N procs)   │     │  (5 por proc)│     │  (por proc)  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                      │
                     ┌──────────────┐     ┌──────────────┐            │
                     │  Relatório   │◀────│   Cruzada    │◀───────────┘
                     │   .md        │     │  (todos)     │
                     └──────────────┘     └──────────────┘
</resumo_arquitetura>

<checklist_orquestrador>
Antes de iniciar, verificar:

**Arquitetura:**
- [ ] Arquivo .docx válido fornecido?
- [ ] $WORKSPACE será criado?
- [ ] Modelo Opus será usado em todas etapas?

**Execução:**
- [ ] Fase 1 extrai processos corretamente?
- [ ] Fase 2 roda análises em paralelo por processo?
- [ ] Fase 3 consolida cada processo?
- [ ] Fase 4 compara TODOS os processos?
- [ ] Fase 5 gera relatório final?

**Validação:**
- [ ] Cada etapa valida JSON/Markdown?
- [ ] Sufixos de correção prontos?
- [ ] Limite de 2 tentativas por etapa?

**Rastreamento:**
- [ ] TodoWrite criado na Fase 0?
- [ ] Atualizado a cada transição?
- [ ] Subagentes NÃO usam TodoWrite?
</checklist_orquestrador>
