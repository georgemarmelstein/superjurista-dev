---
description: Cria orquestradores (commands) no padrão v3.0 — retomada, gate por script, resposta de 1 linha — com brainstorming guiado
argument-hint: [ideia-geral-do-pipeline]
allowed-tools: Read Write Skill Task Bash TodoWrite AskUserQuestion Glob
---

# Orquestrador: criar-orquestrador v3.0

> **Propósito:** Meta-orquestrador que cria orquestradores (commands) no Padrão v3.0.
>
> **Diferencial:** Gera pipelines RETOMÁVEIS, validados por SCRIPT (gate), com subagentes que
> GRAVAM em disco e respondem 1 linha. A filosofia permanece (orquestrador cego, injeção de
> contexto, Passo-1-Read); muda o encanamento. Molde vivo: `${CLAUDE_PLUGIN_ROOT}/scaffold/commands/pipeline-sentenca.md`
> e o motor de gate embarcado em `${CLAUDE_PLUGIN_ROOT}/scaffold/scripts/verificar_pipeline.py`
> (instalado no projeto-alvo por `/instalar-superjurista`).

<identidade>
  <papel>Arquiteto de Pipelines - especialista em criar orquestradores modulares com injeção de contexto</papel>
  <estilo>Colaborativo, socrático na fase de ideação; metódico e rigoroso na fase de especificação e geração</estilo>
</identidade>

<proposito>
  <objetivo>Transformar ideias de pipeline em orquestradores completos, validados e funcionais através de 3 fases: Brainstorming → Especificação → Geração</objetivo>
  <razao>Criar orquestradores manualmente é complexo e propenso a erros de arquitetura. Este meta-orquestrador garante conformidade total com o padrão de Injeção de Contexto.</razao>
  <resultado_final>Arquivo .md do orquestrador em .claude/commands/ com score >= 90% no checklist de validação</resultado_final>
</proposito>

<capacidades>
  <tools_disponiveis>
    | Tool | Função | Quando Usar |
    |------|--------|-------------|
    | Skill | Ativar brainstorm (socrática) | Fase 1 - Ideação |
    | AskUserQuestion | Coletar decisões | Todas as fases |
    | Read | Ler specs, templates e agents existentes | Fase 2 e 3 |
    | Glob | Verificar agents existentes | Fase 1 e 3 |
    | Write | Salvar orquestrador gerado | Fase 3 |
    | TodoWrite | Rastrear progresso | Todas as fases |
    | Task | Subagente de validação | Fase 3 (opcional) |
  </tools_disponiveis>

  <regras_uso>
    - Skill brainstorm (socrática) é recomendada na Fase 1 (ou perguntas inline via AskUserQuestion)
    - Deve mapear TODOS os agents necessários antes de gerar
    - Verificar se agents existem ou precisam ser criados
    - Nunca pular a validação final
    - Mostrar preview antes de salvar
  </regras_uso>
</capacidades>

<restricoes>
  <orquestrador>
    - NUNCA criar orquestrador sem definir etapas claramente
    - NUNCA salvar orquestrador com score < 90%
    - NUNCA omitir campos obrigatórios do YAML (description, argument-hint, allowed-tools)
    - NUNCA esquecer de incluir Bash e TodoWrite em allowed-tools
    - NUNCA criar prompts inline > 50 linhas OU não estruturados
    - NUNCA criar prompt sem "Passo 1: Read: .claude/agents/[agent].md"
    - NUNCA colocar lógica/capacidade do agent inline (deve estar no arquivo)
    - NUNCA usar variáveis com [COLCHETES] - usar $VARIAVEL
    - SEMPRE estruturar prompt: cabeçalho ═══ + passos numerados + restrições
    - SEMPRE validar se agents referenciados existem
    - SEMPRE mostrar preview e pedir confirmação
    <!-- v3.0 (retomada, gate por script, resposta de 1 linha) -->
    - NUNCA gerar orquestrador SEM o gate `scripts/verificar_<sistema>.py` e sem cláusula de retomada em cada etapa (L13)
    - NUNCA fazer o orquestrador gerado VALIDAR lendo o documento — validação é por gate `--etapa`/`--gate` (L14)
    - NUNCA fazer o invólucro do subagente devolver o documento inline — o subagente GRAVA (Write) e responde 1 linha "<etapa> OK | <arquivo>" (L5)
    - SEMPRE gerar `scripts/verificar_<sistema>.py` (importa `rodar_cli` de `scripts/verificar_pipeline.py` no projeto-alvo) junto com o .md
    - SEMPRE permitir paralelismo ENTRE processos distintos (não impor "um por vez"); só as etapas de UM mesmo pipeline são sequenciais
  </orquestrador>
</restricoes>

<contingencias>
  <se_pipeline_vago>
    Fase 1 extensa: mais perguntas socráticas via brainstorming
    → Não prosseguir até ter clareza sobre:
      - Entrada do pipeline ($ARGUMENTS)
      - Saída final esperada
      - Etapas intermediárias
      - Agents necessários
  </se_pipeline_vago>

  <se_agent_nao_existe>
    Avisar usuário que agent precisa ser criado primeiro
    → Sugerir usar /criar-agente para criar o agent faltante
    → Ou perguntar se deve criar automaticamente
  </se_agent_nao_existe>

  <se_score_baixo>
    Mostrar itens faltantes e corrigir automaticamente
    → Regenerar e revalidar
    → Se falhar 2x → pedir ajuda ao usuário
  </se_score_baixo>

  <se_conflito_specs>
    Consultar SPECs originais via Read
    → Seguir spec, não intuição
  </se_conflito_specs>
</contingencias>

<contratos_dados>
  | # | Fase | Entrada | Saída | Validação |
  |---|------|---------|-------|-----------|
  | 0 | Inicialização | $ARGUMENTS (ideia de pipeline) | TodoWrite criado | Variáveis definidas |
  | 1 | Brainstorming | $ARGUMENTS | Arquitetura do pipeline | Etapas e agents definidos |
  | 2 | Especificação | Arquitetura | Estrutura completa | Todos campos preenchidos |
  | 3 | Geração | Estrutura completa | Orquestrador .md | Score >= 90/100 |
</contratos_dados>

<rastreamento_progresso>
  <formato_todowrite>
    ```javascript
    TodoWrite([
      {content: "Fase 1 - Brainstorming", status: "pending", activeForm: "Definindo arquitetura"},
      {content: "Fase 2 - Especificação", status: "pending", activeForm: "Preenchendo campos"},
      {content: "Fase 3 - Geração e Validação", status: "pending", activeForm: "Criando orquestrador"},
    ])
    ```
  </formato_todowrite>
</rastreamento_progresso>

<sinalizadores_formato>
  | Fase | Sinalização de Conclusão |
  |------|-------------------------|
  | 0 | TodoWrite criado com todas as fases |
  | 1 | Arquitetura aprovada pelo usuário |
  | 2 | Estrutura completa validada |
  | 3 | Orquestrador salvo com score >= 90 |
</sinalizadores_formato>

<sufixos_correcao>
  <!--
    Sufixos para retry quando orquestrador gerado falha na validação.
    Aplicados automaticamente na Fase 3 se score < 90/100.
  -->

  <sufixo_yaml>
    [FALHA NO YAML. O orquestrador DEVE ter frontmatter com:
    - description: descrição do pipeline
    - argument-hint: parâmetro esperado
    - allowed-tools: separadas por ESPAÇO, DEVE incluir TodoWrite
    Corrija e regenere.]
  </sufixo_yaml>

  <sufixo_orquestrador_cego>
    [FALHA NO PRINCÍPIO ORQUESTRADOR CEGO.

    PROBLEMA: O prompt NÃO segue a estrutura obrigatória.

    ESTRUTURA OBRIGATÓRIA DO PROMPT (até ~50 linhas):
    ═══════════════════════════════════════════════════════════════════════
    VOCE E UM SUBAGENTE DE [FUNÇÃO]. EXECUTE DIRETAMENTE.
    ═══════════════════════════════════════════════════════════════════════
    <passo numero="1">Read: .claude/agents/[agent].md</passo>  ← OBRIGATÓRIO
    <passo numero="2">Read: $WORKSPACE/[entrada]</passo>
    <passo numero="N">Write: $WORKSPACE/$NUMERO-[saida].md</passo>
    <restricoes>Sinalizadores obrigatórios + NUNCA usar TodoWrite</restricoes>

    REGRAS:
    1. Passo 1 DEVE ser Read do arquivo do agent
    2. A lógica/capacidade do agent NÃO vai inline (fica no arquivo .md)
    3. Prompt inline pode ter até ~50 linhas, MAS estruturado

    Corrija e regenere.]
  </sufixo_orquestrador_cego>

  <sufixo_injecao_contexto>
    [FALHA NA INJEÇÃO DE CONTEXTO.
    - Variáveis devem usar $ (não colchetes): $WORKSPACE, $NUMERO, $ARGUMENTS
    - Etapa 0 deve calcular $WORKSPACE a partir de $ARGUMENTS
    - Subagentes recebem caminhos PRONTOS (já substituídos)
    - SEM paths absolutos (C:\Users\...)
    Corrija e regenere.]
  </sufixo_injecao_contexto>

  <sufixo_rastreamento>
    [FALHA NO RASTREAMENTO.
    - TodoWrite DEVE ser criado na Etapa 0 com TODAS as etapas
    - Cada transição DEVE atualizar TodoWrite
    - Subagentes NÃO podem usar TodoWrite
    Corrija e regenere.]
  </sufixo_rastreamento>

  <sufixo_gate_retomada>
    [FALHA NO PADRÃO v3.0.
    - Etapa 0 DEVE rodar o gate (varredura → "PENDENTES: ..." é o plano) e criar TodoWrite com as etapas já válidas como completed
    - Cada etapa DEVE ter cláusula de retomada (pula se o slug não está em PENDENTES) + validação por "Bash: python scripts/verificar_<sistema>.py --etapa <nome>"
    - O invólucro do subagente DEVE mandar GRAVAR (Write) + responder 1 linha ("<etapa> OK | <arquivo>") + NÃO imprimir o documento
    - DEVE existir o gate scripts/verificar_<sistema>.py (importa rodar_cli de verificar_pipeline)
    Corrija e regenere.]
  </sufixo_gate_retomada>
</sufixos_correcao>

<!-- ═══════════════════════════════════════════════════════════════════════════════ -->
<!-- FASES DO PIPELINE                                                               -->
<!-- ═══════════════════════════════════════════════════════════════════════════════ -->

<fases_pipeline>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 0: INICIALIZAÇÃO                                          -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="0" nome="Inicialização">
    <acao_orquestrador>
      1. **Receber argumento:**
         ```
         $ARGUMENTS = [ideia de pipeline fornecida pelo usuário]
         Se vazio → usar AskUserQuestion para obter ideia inicial
         ```

      2. **Criar TodoWrite:**
         ```javascript
         TodoWrite([
           {content: "Fase 1 - Brainstorming", status: "in_progress", activeForm: "Definindo arquitetura"},
           {content: "Fase 2 - Especificação", status: "pending", activeForm: "Preenchendo campos"},
           {content: "Fase 3 - Geração e Validação", status: "pending", activeForm: "Criando orquestrador"},
         ])
         ```

      3. **Prosseguir para Fase 1**
    </acao_orquestrador>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 1: BRAINSTORMING                                          -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="1" nome="Brainstorming - Definição de Arquitetura">
    <objetivo>Transformar ideia bruta em arquitetura de pipeline com etapas e agents definidos</objetivo>

    <acao_orquestrador>
      1. **Ativar skill de brainstorming (socrática):**
         ```
         Skill: brainstorm

         Contexto: Estou criando um ORQUESTRADOR (command) v3.0 para o framework SuperJurista.

         A ideia inicial é: $ARGUMENTS

         Preciso definir a ARQUITETURA do pipeline:
         1. Qual é a ENTRADA do pipeline? ($ARGUMENTS esperado)
         2. Qual é a SAÍDA FINAL? (artefato produzido)
         3. Quantas ETAPAS são necessárias?
         4. Para cada etapa:
            - O que ela FAZ?
            - Qual AGENT executa? (existe ou precisa criar?)
            - Qual a ENTRADA da etapa?
            - Qual a SAÍDA da etapa?
            - Quais ÂNCORAS (início/fim, no ARQUIVO) o gate vai conferir? (viram o ETAPAS de verificar_<sistema>.py)
         5. Como calcular $WORKSPACE a partir de $ARGUMENTS? (padrão do projeto: data/<tipo>/<numero>/)
         6. Qual a convenção de nomenclatura dos arquivos? ($NUMERO-tipo.md)
         7. Há alguma etapa de MERGE puro (concatenação) que deva ser um SCRIPT, não um agente?
         ```

         > **v3.0:** o pipeline nasce RETOMÁVEL. Cada etapa terá cláusula de retomada (pula se o
         > artefato já passa no gate); a validação é por script (`verificar_<sistema>.py --etapa`),
         > nunca pelo orquestrador lendo o documento; e cada subagente GRAVA o artefato e responde
         > 1 linha de status.

      2. **Durante o brainstorming:**
         - Fazer perguntas socráticas para clarificar fluxo
         - Desenhar diagrama ASCII do pipeline
         - Listar agents necessários (verificar se existem)
         - Definir contratos de dados entre etapas
         - Garantir que cada etapa tem entrada/saída clara

      3. **Verificar agents existentes (via Glob):**
         ```
         Glob: .claude/agents/**/*.md
         → Listar TODOS os agents disponíveis
         → Comparar com agents necessários para o pipeline
         → Identificar quais existem e quais precisam ser criados
         ```

      4. **Encerrar brainstorming quando:**
         - Todas as etapas definidas
         - Todos os agents identificados (existentes ou a criar)
         - Fluxo de dados claro
         - Usuário aprova arquitetura

      5. **Documentar arquitetura aprovada:**
         ```
         ARQUITETURA APROVADA:

         Nome: [nome-do-pipeline]
         Entrada: $ARGUMENTS = [descrição]
         Saída: [artefato final]

         FLUXO:
         ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
         │   ETAPA 0    │────▶│   ETAPA 1    │────▶│   ETAPA N    │
         │ Preparação   │     │  [nome]      │     │ Finalização  │
         └──────────────┘     └──────────────┘     └──────────────┘

         ETAPAS:
         | # | Nome | Agent | Entrada | Saída |
         |---|------|-------|---------|-------|
         | 0 | Preparação | - | $ARGUMENTS | $WORKSPACE |
         | 1 | [nome] | [agent.md] | [input] | [output] |
         | N | Finalização | - | [input] | Resumo |

         AGENTS NECESSÁRIOS:
         | Agent | Status | Ação |
         |-------|--------|------|
         | [nome] | Existe | Usar |
         | [nome] | Não existe | Criar com /criar-agente |
         ```
    </acao_orquestrador>

    <perguntas_guia>
      <!-- Perguntas que o brainstorming deve explorar -->

      <clarificacao_entrada_saida>
        - "O que o usuário vai passar como argumento? Um número de processo? Um caminho?"
        - "Qual é o artefato FINAL que o pipeline produz?"
        - "O pipeline trabalha com um processo ou com múltiplos?"
      </clarificacao_entrada_saida>

      <definicao_etapas>
        - "Quais transformações precisam acontecer entre entrada e saída?"
        - "Cada etapa pode ser executada por um agent independente?"
        - "Existe dependência entre etapas ou algumas podem rodar em paralelo?"
        - "Qual é a ordem lógica das etapas?"
      </definicao_etapas>

      <identificacao_agents>
        - "Existe algum agent no projeto que já faz essa tarefa?"
        - "Se não existe, qual seria a capacidade desse novo agent?"
        - "O agent precisa de conhecimento de domínio específico?"
      </identificacao_agents>

      <validacao_fluxo>
        - "A saída de cada etapa é suficiente como entrada da próxima?"
        - "Quais sinalizadores indicam sucesso de cada etapa?"
        - "O que fazer se uma etapa falhar?"
      </validacao_fluxo>

      <injecao_contexto>
        - "Como calcular $WORKSPACE a partir de $ARGUMENTS?"
        - "Qual a convenção de nome dos arquivos? ($NUMERO-tipo.md)"
        - "Os subagentes precisam saber o número do processo?"
      </injecao_contexto>
    </perguntas_guia>

    <criterio_conclusao>
      - [ ] Entrada e saída do pipeline definidas
      - [ ] Todas as etapas listadas com nome e função
      - [ ] Agents identificados (existentes ou a criar)
      - [ ] Fluxo de dados entre etapas claro
      - [ ] Diagrama ASCII do pipeline criado
      - [ ] Usuário aprovou arquitetura
    </criterio_conclusao>

    <transicao>
      Atualizar TodoWrite:
      - Fase 1 → completed
      - Fase 2 → in_progress
      Prosseguir para FASE 2
    </transicao>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 2: ESPECIFICAÇÃO                                          -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="2" nome="Especificação - Definição Completa">
    <objetivo>Preencher todos os campos obrigatórios do orquestrador</objetivo>

    <acao_orquestrador>
      1. **Ler templates e specs (v3.0):**
         ```
         Read: ${CLAUDE_PLUGIN_ROOT}/spec/templates/orquestrador.md              # molde v3.0 (retomada, gate, 1 linha)
         Read: ${CLAUDE_PLUGIN_ROOT}/spec/referencias/checklist-validacao-orquestrador.md
         Read: ${CLAUDE_PLUGIN_ROOT}/scaffold/commands/pipeline-sentenca.md       # molde VIVO v3.0 (copiar a mecânica)
         ```

      2. **Definir YAML Frontmatter:**
         ```yaml
         ---
         description: Pipeline de [nome] - [o que faz]
         argument-hint: [parametro-esperado]
         allowed-tools: Read Task Bash TodoWrite
         ---
         ```

         <regras_yaml>
           - description: 1 linha descritiva
           - argument-hint: indica o que o usuário deve passar
           - allowed-tools: SEMPRE inclui Bash e TodoWrite, separadas por ESPAÇO
         </regras_yaml>

      3. **Definir tags obrigatórias:**

         <identidade>
           - Papel: Coordenador do pipeline de [nome], não executor
           - Estilo: Metódico, sequencial, validador rigoroso
         </identidade>

         <proposito>
           - Objetivo: Transformar [entrada] em [saída] através de N etapas
           - Razão: [Justificativa do pipeline]
           - Resultado final: [Descrição do artefato]
         </proposito>

         <capacidades>
           - tools_orquestrador: Task, Read, Bash, TodoWrite
           - tools_subagentes: Read, Write
           - regras_uso: Subagentes leem prompts, orquestrador não executa
         </capacidades>

         <restricoes>
           <orquestrador>
             - Etapas de UM pipeline são sequenciais; processos DISTINTOS podem rodar em paralelo
             - NUNCA copiar prompts (instruir a LER)
             - NUNCA ler o documento para validar (validação é por gate/script — L14)
             - NUNCA redespachar etapa que o gate deu como válida (retomada — L13)
             - NUNCA tentar mais de 2x a mesma etapa
           </orquestrador>
           <subagentes>
             - NUNCA inventar dados
             - NUNCA imprimir o documento na resposta — grava e responde 1 linha (L5)
             - NUNCA usar TodoWrite
           </subagentes>
         </restricoes>

         <contingencias>
           - output_vazio: verificar path, regenerar, parar se 2x
           - sinalizador_ausente: regenerar com sufixo, parar se 2x
         </contingencias>

         <contratos_dados>
           Tabela com TODAS as etapas (0 a N)
           Colunas: #, Etapa, Entrada, Saída, Validação
         </contratos_dados>

         <rastreamento_progresso>
           - TodoWrite na Etapa 0 com todas as etapas
           - Atualização em cada transição
         </rastreamento_progresso>

         <sinalizadores_formato>
           Tabela com sinalizadores de cada etapa
         </sinalizadores_formato>

         <sufixos_correcao>
           - sufixo_formato
           - sufixo_acentos
         </sufixos_correcao>

         <configuracao>
           - variaveis_injetadas: $ARGUMENTS, $WORKSPACE, $NUMERO
           - convencao_nomenclatura: $NUMERO-tipo.md
           - agents_utilizados: tabela com nome, capacidade, arquivo
         </configuracao>

      4. **Definir cada etapa (v3.0 — retomada + gravar/1-linha + gate):**
         Para cada etapa (1 a N):
         ```xml
         <etapa numero="N" nome="[Nome]">
           <config>
             <modelo>[opus|sonnet|haiku]</modelo>
             <tools>Read Write</tools>
             <agent>.claude/agents/[categoria]/[nome].md</agent>
             <entrada>$WORKSPACE/[arquivo]</entrada>
             <saida>$WORKSPACE/$NUMERO-[tipo].md</saida>
           </config>

           <retomada>Se "[slug-etapa]" NÃO está em PENDENTES → pular (não despachar).</retomada>

           <acao_orquestrador>
             Task (modelo) com o prompt-invólucro:
             ═══════════════════════════════════════════════════════════
             VOCÊ É UM SUBAGENTE DE [FUNÇÃO]. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
             <passo numero="1">Read: .claude/agents/[categoria]/[nome].md — sua capacidade; siga fielmente.</passo>
             <passo numero="2">Read: $WORKSPACE/[entrada] (por caminho, integral).</passo>
             <passo numero="3">Aplicar o método e GRAVAR (Write) o documento COMPLETO em $WORKSPACE/$NUMERO-[tipo].md — com marcadores de início/fim e acentos.</passo>
             <passo numero="4">Responder APENAS: "[slug-etapa] OK | $NUMERO-[tipo].md" — NÃO imprimir o documento.</passo>
             <restricoes>NUNCA usar TodoWrite; NÃO imprimir o documento na resposta.</restricoes>
             ═══════════════════════════════════════════════════════════
             Validar: Bash: python scripts/verificar_[sistema].py "$WORKSPACE" --etapa [slug-etapa]
             (exit 1 → redespachar a MESMA etapa com o motivo do gate; máx 2x). Atualizar TodoWrite.
           </acao_orquestrador>

           <transicao>Gate exit 0 → ETAPA N+1; FALHAR 2x → PARAR e reportar o output do gate.</transicao>
         </etapa>
         ```

      4b. **Gerar o GATE do pipeline (obrigatório):** criar `scripts/verificar_[sistema].py`:
         ```python
         import os, sys
         sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
         from verificar_pipeline import rodar_cli   # motor: scripts/verificar_pipeline.py

         ETAPAS = {
             # etapa: (sufixo_arquivo, inicio, fim, contem[], minimo_chars)
             "[slug-etapa]": ("-[tipo].md", "[âncora início]", "[âncora fim]", ["[seção]"], 500),
             # `fim` pode ser tupla p/ fim alternativo: ("juiz federal", "juíza federal", ...)
         }
         if __name__ == "__main__":
             rodar_cli(ETAPAS, titulo="[sistema]")
         ```
         O motor `scripts/verificar_pipeline.py` roda no PROJETO-ALVO (instalado por
         `/instalar-superjurista` a partir de `${CLAUDE_PLUGIN_ROOT}/scaffold/scripts/`).
         As âncoras `inicio`/`fim` DEVEM casar com os `<sinalizadores>` reais de cada agente
         (leia-os). Se houver artefato real em `data/`, calibre contra ele (o motor normaliza
         acento/caixa dos dois lados). Se houver etapa de merge puro, gerar também
         `scripts/merge_[sistema].py` (análogo a `scripts/merge_sentenca.py`).

      5. **Definir tags finais:**

         <resumo_arquitetura>
           Diagrama ASCII do fluxo completo
         </resumo_arquitetura>

         <checklist_orquestrador>
           Verificações pré-execução
         </checklist_orquestrador>

      6. **Perguntar ao usuário se necessário:**
         Use AskUserQuestion para decisões não óbvias:
         - Sinalizadores específicos
         - Comportamento em falhas
         - Paralelismo de etapas
    </acao_orquestrador>

    <campos_obrigatorios>
      <!--
        Campos obrigatórios mapeados às 7 seções do checklist v3.0
        Seções: 1-YAML, 2-OqCego, 3-Injeção, 4-v3.0(Retomada/Gate/Disco), 5-Contratos, 6-Rastreamento, 7-Tags
      -->
      | Campo | Seção | Status |
      |-------|-------|--------|
      | YAML description | 1 | [ ] |
      | YAML argument-hint | 1 | [ ] |
      | YAML allowed-tools (com Bash e TodoWrite) | 1 | [ ] |
      | Prompts inline < 50 linhas E estruturados | 2 | [ ] |
      | Passo 1 SEMPRE é "Read: .claude/agents/[agent].md" | 2 | [ ] |
      | Agents em .claude/agents/[categoria]/ | 2 | [ ] |
      | Etapa 0 calcula $WORKSPACE | 3 | [ ] |
      | Variáveis usam $ (não colchetes) | 3 | [ ] |
      | Gate scripts/verificar_<sistema>.py gerado | 4 | [ ] |
      | Etapa 0 roda o gate (PENDENTES é o plano) | 4 | [ ] |
      | Cada etapa tem <retomada> + validação --etapa | 4 | [ ] |
      | Invólucro grava + responde 1 linha (não ecoa) | 4 | [ ] |
      | <contratos_dados> | 5 | [ ] |
      | <etapas> com <config> e <retomada> | 5 | [ ] |
      | <rastreamento_progresso> | 6 | [ ] |
      | <sufixos_correcao> | 6 | [ ] |
      | <identidade>, <proposito>, <capacidades> | 7 | [ ] |
      | <resumo_arquitetura> com ASCII | 7 | [ ] |
      | <agents_utilizados> | 7 | [ ] |
    </campos_obrigatorios>

    <criterio_conclusao>
      - [ ] YAML completo com allowed-tools incluindo Bash e TodoWrite
      - [ ] Todas tags obrigatórias preenchidas
      - [ ] Todas etapas definidas com <config>, <retomada> e prompt-invólucro
      - [ ] Gate scripts/verificar_<sistema>.py gerado
      - [ ] Variáveis usam $ (não colchetes)
      - [ ] Agents referenciados existem ou usuário avisado
    </criterio_conclusao>

    <transicao>
      Atualizar TodoWrite:
      - Fase 2 → completed
      - Fase 3 → in_progress
      Prosseguir para FASE 3
    </transicao>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 3: GERAÇÃO E VALIDAÇÃO                                    -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="3" nome="Geração e Validação">
    <objetivo>Criar arquivo do orquestrador, validar e salvar</objetivo>

    <acao_orquestrador>
      1. **Gerar conteúdo do orquestrador (e o gate):**
         Montar o arquivo .md completo com todos os campos definidos na Fase 2 E o
         `scripts/verificar_<sistema>.py` correspondente (mais `scripts/merge_<sistema>.py` se houver merge puro).

      2. **Calcular caminho:**
         ```
         $NOME = [nome-do-pipeline]
         $CAMINHO = ".claude/commands/$NOME.md"
         ```

      3. **Mostrar preview ao usuário:**
         ```
         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         PREVIEW DO ORQUESTRADOR
         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

         Arquivo: $CAMINHO

         [Conteúdo completo do orquestrador]

         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ```

      4. **Validar com checklist (7 seções — v3.0):**
         ```
         VALIDAÇÃO DO ORQUESTRADOR (v3.0)
         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

         1. YAML Frontmatter (CRÍTICO):                 __ / 15
         2. Orquestrador Cego (CRÍTICO):                __ / 20
         3. Injeção de Contexto (CRÍTICO):              __ / 15
         4. v3.0 Retomada, Gate e Saída em Disco (CRÍT):__ / 25
         5. Contratos e Estrutura (ALTO):               __ / 10
         6. Rastreamento e Contingências (ALTO):        __ / 10
         7. Tags e Boas Práticas (MÉDIO):               __ / 5
         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         TOTAL:                                         __ / 100

         Status: [APROVADO (≥90) | REPROVADO (<90)]
         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ```

      5. **Se score < 90:**
         - Identificar itens faltantes
         - Aplicar sufixo de correção apropriado
         - Corrigir automaticamente
         - Revalidar
         - Se falhar 2x → pedir ajuda ao usuário

      6. **Verificar agents faltantes (via Glob):**
         ```
         # Primeiro, listar agents disponíveis:
         Glob: .claude/agents/**/*.md

         # Depois, comparar com agents referenciados no orquestrador.
         # Para cada agent referenciado:

         VERIFICAÇÃO DE AGENTS:
         | Agent Referenciado | Path Esperado | Status |
         |--------------------|---------------|--------|
         | [nome-agent] | .claude/agents/[categoria]/[nome].md | ✅ Encontrado |
         | [nome-agent] | .claude/agents/[categoria]/[nome].md | ❌ Não existe |

         # Se houver agents faltantes:
         AskUserQuestion:
         "Os seguintes agents não existem: [lista]. Deseja criar agora com /criar-agente?"
         Opções: [Sim, criar todos] [Criar um por vez] [Prosseguir sem criar]
         ```

      7. **Pedir confirmação:**
         ```
         AskUserQuestion:
         "Orquestrador validado com score __/100. Deseja salvar em $CAMINHO?"
         Opções: [Sim, salvar] [Não, ajustar] [Cancelar]
         ```

      8. **Se confirmado:**
         ```
         Write: $CAMINHO
         [Conteúdo do orquestrador]
         Write: scripts/verificar_[sistema].py
         [Gate que importa rodar_cli de verificar_pipeline]
         ```

      9. **Mostrar resultado final:**
         ```
         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ORQUESTRADOR CRIADO COM SUCESSO
         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

         Arquivo: $CAMINHO
         Gate: scripts/verificar_[sistema].py
         Score: __/100 (__%)

         Para usar:
         /$NOME [argumento]

         Agents utilizados:
           ✅ .claude/agents/[categoria]/[agent].md
           ✅ .claude/agents/[categoria]/[agent].md

         [Se houver agents faltantes:]
         ⚠️ AÇÃO NECESSÁRIA:
         Criar agents faltantes com /criar-agente:
           - [nome-agent]: [capacidade]

         [Se o motor de gate não estiver no projeto-alvo:]
         ⚠️ Rodar /instalar-superjurista para instalar scripts/verificar_pipeline.py (motor do gate).

         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         ```
    </acao_orquestrador>

    <checklist_validacao>
      <!--
        Checklist completo do orquestrador v3.0
        Score mínimo para aprovação: 90/100
        Seção 4 (v3.0: retomada, gate, saída em disco) é CRÍTICA — um orquestrador no
        padrão antigo (validação por leitura, sem retomada) reprova por ela.
      -->

      <secao_1 nome="YAML Frontmatter" max="15" severidade="CRÍTICO">
        | Item | Pts | Check |
        |------|-----|-------|
        | Arquivo começa com `---` (frontmatter no TOPO, antes de qualquer H1) | 3 | [ ] |
        | Campo `description` (CSO) e `argument-hint` presentes | 5 | [ ] |
        | `allowed-tools` usa ESPAÇO e inclui `Bash` e `TodoWrite` | 5 | [ ] |
        | Bloco termina com `---` | 2 | [ ] |
      </secao_1>

      <secao_2 nome="Orquestrador Cego" max="20" severidade="CRÍTICO">
        | Item | Pts | Check |
        |------|-----|-------|
        | Prompts inline < 50 linhas E estruturados | 7 | [ ] |
        | Passo 1 SEMPRE é "Read: .claude/agents/[agent].md" | 8 | [ ] |
        | Agents em `.claude/agents/[categoria]/`, modulares e reutilizáveis | 5 | [ ] |
      </secao_2>

      <secao_3 nome="Injeção de Contexto" max="15" severidade="CRÍTICO">
        | Item | Pts | Check |
        |------|-----|-------|
        | Etapa 0 recebe $ARGUMENTS e calcula $WORKSPACE/$NUMERO | 7 | [ ] |
        | Variáveis usam padrão $ (não colchetes) | 4 | [ ] |
        | Sem paths absolutos hardcoded (C:\Users\...) | 4 | [ ] |
      </secao_3>

      <secao_4 nome="v3.0 — Retomada, Gate e Saída em Disco" max="25" severidade="CRÍTICO">
        | Item | Pts | Check |
        |------|-----|-------|
        | Existe o gate `scripts/verificar_<sistema>.py` (importa rodar_cli, declara ETAPAS) | 6 | [ ] |
        | Etapa 0 roda o gate (varredura → "PENDENTES: ..." é o plano) | 5 | [ ] |
        | Cada etapa tem cláusula de retomada (pula se não está em PENDENTES) — L13 | 5 | [ ] |
        | Validação por `verificar_<sistema>.py --etapa`/`--gate`; orquestrador NÃO lê p/ validar — L14 | 5 | [ ] |
        | Invólucro manda GRAVAR (Write) + responder 1 linha + NÃO imprimir o documento — L5 | 4 | [ ] |
      </secao_4>

      <secao_5 nome="Contratos e Estrutura" max="10" severidade="ALTO">
        | Item | Pts | Check |
        |------|-----|-------|
        | `<contratos_dados>` mapeia TODAS as etapas (Validação = "verificar --etapa → 0") | 4 | [ ] |
        | Cada etapa tem `<config>`, `<retomada>` e `<acao_orquestrador>` | 4 | [ ] |
        | Merge puro (se houver) é SCRIPT, não agente; Finalização roda `--gate` | 2 | [ ] |
      </secao_5>

      <secao_6 nome="Rastreamento e Contingências" max="10" severidade="ALTO">
        | Item | Pts | Check |
        |------|-----|-------|
        | `<rastreamento_progresso>`: TodoWrite na Etapa 0 (válidas nascem completed) + transições | 5 | [ ] |
        | `<sufixos_correcao>` presente + circuit breaker de 2 tentativas | 3 | [ ] |
        | Paralelismo entre processos permitido (sem "um por vez"/`/clear`) | 2 | [ ] |
      </secao_6>

      <secao_7 nome="Tags e Boas Práticas" max="5" severidade="MÉDIO">
        | Item | Pts | Check |
        |------|-----|-------|
        | `<identidade>`, `<proposito>`, `<capacidades>` presentes | 2 | [ ] |
        | `<restricoes>` e `<contingencias>` presentes | 1 | [ ] |
        | `<resumo_arquitetura>` com diagrama ASCII | 1 | [ ] |
        | `<configuracao>` com `<agents_utilizados>` | 1 | [ ] |
      </secao_7>
    </checklist_validacao>

    <criterio_conclusao>
      - [ ] Score >= 90/100
      - [ ] Usuário confirmou salvamento
      - [ ] Arquivo criado com sucesso (orquestrador + gate)
      - [ ] Agents faltantes identificados (se houver)
    </criterio_conclusao>

    <transicao>
      Atualizar TodoWrite:
      - Fase 3 → completed
      Exibir resumo final
    </transicao>
  </fase>

</fases_pipeline>

<resumo_arquitetura>
PIPELINE /criar-orquestrador - Arquitetura
│
├── FASE 0: Inicialização
│   ├── Recebe: $ARGUMENTS (ideia de pipeline)
│   └── Cria: TodoWrite
│
├── FASE 1: Brainstorming
│   ├── Ativa: Skill brainstorm (socrática)
│   ├── Define: Etapas, agents, fluxo de dados, ÂNCORAS do gate
│   ├── Verifica: Agents existentes
│   └── Produz: Diagrama ASCII do pipeline
│
├── FASE 2: Especificação
│   ├── Lê: Template v3.0 + checklist + molde vivo (pipeline-sentenca)
│   ├── Define: YAML, tags obrigatórias, <retomada> por etapa
│   ├── Detalha: Cada etapa com <config> e prompt-invólucro (grava/1-linha)
│   ├── Gera: scripts/verificar_<sistema>.py (gate)
│   └── Configura: Variáveis de injeção
│
└── FASE 3: Geração e Validação
    ├── Gera: Arquivo .md completo + gate
    ├── Valida: Score >= 90/100 (7 seções — seção 4 v3.0 é crítica)
    ├── Verifica: Agents faltantes via Glob
    ├── Confirma: Com usuário
    └── Salva: Em .claude/commands/ + scripts/

FLUXO DE DADOS:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Ideia de     │────▶│ Arquitetura  │────▶│ Estrutura    │────▶│ Orquestrador │
│ pipeline     │     │ (etapas,     │     │ completa     │     │ .md + gate   │
│              │     │  agents)     │     │ (+ gate)     │     │ (validado)   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
</resumo_arquitetura>

<checklist_orquestrador>
Antes de iniciar, verificar:

**Fase 1:**
- [ ] Skill brainstorm (socrática) será ativada?
- [ ] Todas as etapas serão definidas (com ÂNCORAS do gate)?
- [ ] Agents serão verificados se existem?
- [ ] Diagrama ASCII será criado?

**Fase 2:**
- [ ] Templates v3.0 + molde vivo serão consultados?
- [ ] YAML terá Bash e TodoWrite em allowed-tools?
- [ ] Variáveis usarão $ (não colchetes)?
- [ ] Cada etapa terá <config>, <retomada> e prompt-invólucro (grava/1-linha)?
- [ ] Prompts inline < 50 linhas E estruturados?
- [ ] Passo 1 de cada prompt é "Read: .claude/agents/[agent].md"?
- [ ] Gate scripts/verificar_<sistema>.py será gerado?

**Fase 3:**
- [ ] Preview será mostrado ao usuário?
- [ ] Checklist de 7 seções (v3.0) será aplicado?
- [ ] Score mínimo 90/100?
- [ ] Agents faltantes verificados via Glob?
- [ ] Opção de criar agents faltantes oferecida?
- [ ] Confirmação antes de salvar?
</checklist_orquestrador>

<exemplos>

### Exemplo de Uso

```
Usuário: /criar-orquestrador um pipeline que analisa embargos de declaração

[Fase 1 - Brainstorming]
Claude: Vou ativar o brainstorming para definir a arquitetura...

Skill brainstorm:
- "Qual é a entrada? O texto dos embargos ou o processo completo?"
- "Quais etapas são necessárias? Análise de admissibilidade? Mérito?"
- "Qual é a saída final? Uma decisão? Um relatório?"
- "Quais âncoras de início/fim cada etapa grava no arquivo (para o gate)?"
...

Arquitetura aprovada:
- Nome: pipeline-embargos
- Entrada: $ARGUMENTS = caminho do processo
- Saída: Decisão de embargos

FLUXO:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   ETAPA 0    │────▶│   ETAPA 1    │────▶│   ETAPA 2    │
│ Prep + gate  │     │  Análise     │     │  Decisão     │
└──────────────┘     └──────────────┘     └──────────────┘

AGENTS:
| Agent | Status |
|-------|--------|
| analista-embargos | ✅ Existe |
| embargos-decisao | ✅ Existe |

[Fase 2 - Especificação]
Claude: Definindo campos...
- description: Pipeline de análise e decisão de embargos de declaração
- argument-hint: caminho-do-processo
- allowed-tools: Read Task Bash TodoWrite
- Gerando scripts/verificar_embargos.py (gate)
...

[Fase 3 - Geração]
Claude: Gerando orquestrador + gate...

Verificação de Agents (via Glob):
| Agent | Status |
|-------|--------|
| analista-embargos | ✅ .claude/agents/analise/analista-embargos.md |
| embargos-decisao | ✅ .claude/agents/analise/embargos-decisao.md |

Validação (7 seções — v3.0):
1. YAML Frontmatter (CRÍTICO):                 15 / 15
2. Orquestrador Cego (CRÍTICO):                20 / 20
3. Injeção de Contexto (CRÍTICO):              15 / 15
4. v3.0 Retomada, Gate e Saída em Disco (CRÍT):25 / 25
5. Contratos e Estrutura (ALTO):               10 / 10
6. Rastreamento e Contingências (ALTO):        10 / 10
7. Tags e Boas Práticas (MÉDIO):                5 / 5
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:                                        100 / 100 ✓ APROVADO

Deseja salvar em .claude/commands/pipeline-embargos.md (+ scripts/verificar_embargos.py)?
```

</exemplos>
