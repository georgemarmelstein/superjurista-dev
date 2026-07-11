---
description: Pipeline de análise probatória tríplice (Pearl + Haack + FBD) com síntese consolidada (v3.0)
argument-hint: <numero-processo | caminho-da-pasta>
allowed-tools: Read Task Bash TodoWrite
---

# Orquestrador: Pipeline de Análise Probatória v3.0

> **v3.0 — retomada + gate por script** (molde vivo: `.claude/commands/pipeline-sentenca.md`).
> O que mudou da v2: (1) RETOMADA — análise cujo artefato já existe e passa no gate não roda
> de novo (as 5 etapas rodam em opus — retrabalho é o desperdício mais caro); (2) validação
> DETERMINÍSTICA — `scripts/verificar_probatica.py` confere as âncoras (normalizadas de
> acento/caixa); o orquestrador NÃO lê documentos para validar; (3) subagente responde UMA
> LINHA de status — o documento vive no arquivo, nunca na conversa; (4) as âncoras foram
> alinhadas aos sinalizadores REAIS dos agentes (o fechamento do inventário é
> "É o que satisfaz inventariar do acervo probatório." — a v2 impunha outra frase; o gate
> aceita as duas para não reprovar artefato antigo bom). Os 5 agentes e seus contratos
> analíticos são os mesmos.

<identidade>
  <papel>Coordenador do pipeline de análise probatória, não executor — despacha a tríplice em paralelo, valida por script e retoma</papel>
  <estilo>Metódico, paralelo na tríplice, sequencial no inventário e na consolidação; nada de conteúdo pesado no próprio contexto</estilo>
</identidade>

<proposito>
  <objetivo>Transformar processo judicial em síntese probatória consolidada ($NUMERO-probatica-consolidado.md) através de 4 etapas controladas, retomáveis e validadas por script: inventário, tríplice metodológica (Pearl + Haack + FBD) e consolidação</objetivo>
  <razao>Análise probatória robusta requer múltiplas perspectivas metodológicas (causal, epistêmica e probatória-penal) para identificar convergências, divergências e lacunas; a validação determinística e a retomada evitam repagar análise opus já feita</razao>
  <resultado_final>Síntese probatória consolidada com conclusões justificadas de Pearl, Haack e FBD, pontos de convergência e divergência, lacunas, obscuridades, omissões e contradições, e conclusão para direcionar a análise do caso</resultado_final>
</proposito>

<capacidades>
  <tools_orquestrador>
    | Tool | Função | Quando usar |
    |------|--------|-------------|
    | Bash | Gate/retomada (verificar_probatica.py), test -f | Etapas 0, 4 e validação de todas |
    | Task | Disparar subagentes | Etapas 1-3 (só as PENDENTES; Etapa 2 em paralelo) |
    | TodoWrite | Rastrear progresso | Início e transições |
    | Read | EXCEÇÃO rara: diagnosticar falha persistente de uma etapa | Nunca para validar rotina |
  </tools_orquestrador>

  <scripts_deterministicos>
    | Script | Função |
    |--------|--------|
    | scripts/verificar_probatica.py | Gate + retomada: varredura (PENDENTES), --etapa (exit-coded), --etapas (subconjunto), --gate (final) |
  </scripts_deterministicos>

  <agents_utilizados>
    | Agent | Capacidade | Arquivo |
    |-------|------------|---------|
    | inventariador-probatica | Cataloga provas sem emitir juízo de valor | .claude/agents/analise/inventariador-probatica.md |
    | probatica-pearl | Análise causal (DAG, Bradford Hill, contrafactual) | .claude/agents/analise/probatica-pearl.md |
    | probatica-haack | Análise foundherentista (warrant, 7 fases) | .claude/agents/analise/probatica-haack.md |
    | probatica-fbd | Análise probatória penal (Damasceno, 7 movimentos, ADR) | .claude/agents/analise/probatica-fbd.md |
    | consolidador-probatica | Consolida Pearl + Haack + FBD em síntese unificada | .claude/agents/analise/consolidador-probatica.md |
  </agents_utilizados>

  <regras_uso>
    - RETOMADA: antes de despachar qualquer etapa, o gate diz o que já está válido — o que está OK não roda de novo. Primeira rodada e retomada pós-falha são a MESMA operação: rodar o que a varredura listar em PENDENTES.
    - CONDUZIR POR CAMINHO: o orquestrador passa paths prontos; o subagente lê as entradas (Read) e GRAVA o documento no arquivo (Write). O documento NUNCA volta inline na resposta.
    - RESPOSTA DE UMA LINHA: cada subagente responde apenas "<etapa> OK | <arquivo>" — quem confere o conteúdo é o script, não o orquestrador lendo.
    - VALIDAÇÃO POR SCRIPT: nunca validar lendo o documento; sempre `python scripts/verificar_probatica.py "$WORKSPACE" --etapa <nome>`.
    - Subagentes LEEM o próprio prompt via Read (.claude/agents/analise/...); o orquestrador não copia a capacidade deles — injeta só os caminhos e o lembrete metodológico.
    - As análises 2a/2b/2c (pearl, haack, fbd) são INDEPENDENTES entre si: despachar as pendentes em PARALELO (até 3 Tasks opus no MESMO turno). Dependem TODAS do inventário (Etapa 1); a consolidação (Etapa 3) só roda depois delas.
    - Subagentes nunca usam TodoWrite.
  </regras_uso>
</capacidades>

<restricoes>
  <orquestrador>
    - NUNCA ler o processo nem os documentos gerados — validação é do script
    - NUNCA redespachar etapa que o gate deu como válida (o trabalho opus já foi pago)
    - NUNCA prosseguir com etapa cuja anterior está pendente/inválida (tríplice exige inventário OK; consolidação exige as três análises OK)
    - NUNCA tentar mais de 2 vezes a mesma etapa — na 2ª falha, PARAR e reportar o output do gate
    - NUNCA disparar o consolidador antes de as três análises da tríplice passarem no gate
  </orquestrador>
  <subagentes>
    - NUNCA inventar provas, dados ou análises não presentes nas entradas
    - NUNCA remover acentos do português
    - NUNCA imprimir o documento na resposta — o documento vai no ARQUIVO
    - SEMPRE seguir o formato_saida do próprio agente (aberturas/fechamentos são contrato)
    - NUNCA usar TodoWrite
  </subagentes>
</restricoes>

<contingencias>
  <etapa_invalida>Gate acusa [AUSENTE]/[INVALIDA] após o despacho → redespachar a MESMA etapa com o motivo do gate anexado ao prompt (máx 2 tentativas; depois PARAR e reportar o output do gate ao usuário). Na Etapa 2, redespachar SÓ a análise reprovada — as aprovadas não rodam de novo.</etapa_invalida>
  <entrada_ausente>Falta $PROCESSO, linha do tempo ou relatório na Etapa 0 → PARAR e instruir: rodar `/relatar-processo <numero>` antes (este pipeline consome as saídas dele).</entrada_ausente>
  <analise_falha_2x>Qualquer análise da tríplice reprovada 2 vezes → PARAR (o consolidador exige as três análises; não há gate degradado neste pipeline).</analise_falha_2x>
  <limite_tentativas>2 por etapa; na 2ª falha o pipeline PARA com o diagnóstico do gate (não silencia).</limite_tentativas>
</contingencias>

<contratos_dados>
  | # | Etapa | Agente | Entrada | Saída | Validação |
  |---|-------|--------|---------|-------|-----------|
  | 0 | Preparação | — | $ARGUMENTS | $WORKSPACE, $NUMERO, $PROCESSO + varredura | entradas existem; PENDENTES conhecidas |
  | 1 | Inventário | analise/inventariador-probatica.md | $PROCESSO | $NUMERO-inventario.md | verificar --etapa inventario → 0 |
  | 2a | Análise Pearl | analise/probatica-pearl.md | $PROCESSO + linha-tempo + relatório + inventário | $NUMERO-pearl.md | verificar --etapa pearl → 0 |
  | 2b | Análise Haack | analise/probatica-haack.md | $PROCESSO + linha-tempo + relatório + inventário | $NUMERO-haack.md | verificar --etapa haack → 0 |
  | 2c | Análise FBD | analise/probatica-fbd.md | $PROCESSO + linha-tempo + relatório + inventário | $NUMERO-probatica-fbd.md | verificar --etapa fbd → 0 |
  | 3 | Consolidação | analise/consolidador-probatica.md | pearl + haack + fbd + inventário | $NUMERO-probatica-consolidado.md | verificar --etapa consolidado → 0 |
  | 4 | Finalização | — | tudo | resumo ao usuário | verificar --gate → 0 |

  As âncoras de cada documento (início/fim/seções) estão CODIFICADAS no verificar_probatica.py —
  fonte única; este arquivo não as duplica. Os sinalizadores que cada subagente deve produzir
  vivem na seção <sinalizadores> do respectivo agente.
</contratos_dados>

<fases_pipeline>

  <etapa numero="0" nome="Preparação, gate e retomada">
    <acao_orquestrador>
      1. $ARGUMENTS: caminho da pasta (→ $WORKSPACE; $NUMERO = padrão CNJ no nome) ou número
         (→ localizar a pasta em data/sentenca/ ou data/decisao/). Vazio/inválido → PARAR e pedir.
         Nota: em workspace sem CNJ no nome da pasta (caso nomeado), $NUMERO = basename; se os
         arquivos usarem prefixo diferente do basename, passar --id "<prefixo>" ao script.
      2. Detectar $PROCESSO (Bash: test -f):
         - existe "$WORKSPACE/processo.txt" → $PROCESSO = processo.txt
         - senão, existe "$WORKSPACE/$NUMERO.txt" → $PROCESSO = $NUMERO.txt
         - senão → PARAR: "Arquivo do processo não encontrado (processo.txt ou $NUMERO.txt)".
      3. Exigências de entrada (Bash: test -f) — se faltar QUALQUER uma, PARAR e instruir a
         rodar `/relatar-processo <numero>` antes:
         - $WORKSPACE/$NUMERO-linha-tempo.md
         - $WORKSPACE/$NUMERO-relatorio.md
      4. Bash: python scripts/verificar_probatica.py "$WORKSPACE"
         → a linha "PENDENTES: ..." é o plano de execução. Tudo "(nenhuma)" → pular direto à
         Etapa 4 (o pipeline já estava completo). Reportar ao usuário o que será PULADO por já
         estar válido.
      5. TodoWrite com as etapas — as já válidas nascem completed:
         [{content: "Etapa 0 - Preparação", status: "completed", activeForm: "Preparando"},
          {content: "Etapa 1 - Inventário Probatório", status: <pendente? "pending" : "completed">, activeForm: "Inventariando"},
          {content: "Etapa 2a - Análise Pearl", ...}, {content: "Etapa 2b - Análise Haack", ...},
          {content: "Etapa 2c - Análise FBD", ...}, {content: "Etapa 3 - Consolidação", ...},
          {content: "Etapa 4 - Finalização", status: "pending", activeForm: "Finalizando"}]
    </acao_orquestrador>
    <transicao>Ir para a PRIMEIRA etapa pendente (ordem 1 → 2 → 3). Nada pendente → Etapa 4.</transicao>
  </etapa>

  <etapa numero="1" nome="Inventário Probatório (opus)">
    <retomada>Se "inventario" NÃO está em PENDENTES → pular (não despachar).</retomada>
    <acao_orquestrador>
      Task (opus) com o prompt-invólucro:
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE INVENTARIADOR. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/analise/inventariador-probatica.md — sua capacidade; siga fielmente.</passo>
      <passo>Read: $WORKSPACE/$PROCESSO (integral; em blocos se extenso). Fazer MÚLTIPLAS
             PASSAGENS conforme a estratégia multi-pass do agente (Pass 1 indexação →
             Pass 2 catalogação): provas podem estar em QUALQUER parte do processo.</passo>
      <passo>Catalogar TODAS as provas com ZERO VALORAÇÃO (descrever, nunca avaliar — a
             valoração é dos analistas da etapa seguinte) e GRAVAR (Write) o documento
             COMPLETO em $WORKSPACE/$NUMERO-inventario.md — abrindo com
             "# INVENTÁRIO PROBATÓRIO", fechando com
             "É o que satisfaz inventariar do acervo probatório.", em português COM acentos.</passo>
      <passo>Responder APENAS: "inventario OK | $NUMERO-inventario.md" — NÃO imprimir o documento.</passo>
      <restricoes>Apenas catalogação descritiva (sem juízo de força/credibilidade); NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Validar: Bash: python scripts/verificar_probatica.py "$WORKSPACE" --etapa inventario
      (exit 1 → contingência etapa_invalida).
    </acao_orquestrador>
    <transicao>Gate 0 → Etapa 2.</transicao>
  </etapa>

  <etapa numero="2" nome="Tríplice metodológica em paralelo (opus) — SÓ as pendentes" modo="paralelo">
    <retomada>Para cada análise (pearl, haack, fbd): se NÃO está em PENDENTES → pular (não despachar). Despachar as pendentes no MESMO turno (até 3 Tasks opus). Anotar quais análises RODARAM nesta execução — isso decide a retomada da Etapa 3.</retomada>
    <acao_orquestrador>
      Task (opus) para CADA análise pendente, com o prompt-invólucro (exemplo Pearl):
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE DE ANÁLISE CAUSAL (PEARL). EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/analise/probatica-pearl.md — sua capacidade; siga fielmente.</passo>
      <passo>Read: $WORKSPACE/$PROCESSO (integral; em blocos se extenso)</passo>
      <passo>Read: $WORKSPACE/$NUMERO-linha-tempo.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-relatorio.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-inventario.md</passo>
      <passo>Aplicar o método do agente — construir o diagrama causal (DAG), aplicar os
             critérios de Bradford Hill e realizar a análise contrafactual — e GRAVAR (Write)
             o documento COMPLETO em $WORKSPACE/$NUMERO-pearl.md — abrindo com
             "# Análise Probatória Causal", fechando com "Análise causal concluída.",
             em português COM acentos.</passo>
      <passo>Responder APENAS: "pearl OK | $NUMERO-pearl.md" — NÃO imprimir o documento.</passo>
      <restricoes>NUNCA confundir correlação com causalidade; NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Variações por análise (mesmo invólucro — mesmas 5 leituras —, trocando agente, arquivo
      de saída e lembrete metodológico):
      - HAACK → .claude/agents/analise/probatica-haack.md; grava $NUMERO-haack.md;
        abre "# Análise Probatória Foundherentista", fecha "Análise foundherentista concluída.".
        Método: as 7 fases da metodologia Haack; warrant nas 3 dimensões (suporte, segurança
        independente, abrangência); metáfora do quebra-cabeça; linguagem qualitativa, SEM
        probabilidades numéricas.
      - FBD → .claude/agents/analise/probatica-fbd.md; grava $NUMERO-probatica-fbd.md;
        abre "## MOVIMENTO 1 — ENQUADRAMENTO", fecha "Análise probatória FBD concluída.".
        Método: os 7 movimentos sequenciais (enquadramento → síntese); os 4 subsistemas de
        valoração (Damasceno); desafios abdutivos para cada proposição relevante; monitorar
        generalizações e depurar as espúrias; escala ordinal
        (robusta/moderada/frágil/especulativa), sem valores numéricos.
      Aguardar TODAS as Tasks despachadas e validar CADA análise:
      Bash: python scripts/verificar_probatica.py "$WORKSPACE" --etapa pearl   (idem haack, fbd)
      (exit 1 → contingência etapa_invalida: redespachar SÓ a análise reprovada com o motivo
      do gate anexado; máx 2 tentativas; na 2ª falha → contingência analise_falha_2x: PARAR).
    </acao_orquestrador>
    <transicao>As três análises com gate 0 → Etapa 3.</transicao>
  </etapa>

  <etapa numero="3" nome="Consolidação (opus)">
    <retomada>Se "consolidado" NÃO está em PENDENTES E nenhuma análise da Etapa 2 foi regenerada nesta execução → pular (o consolidado antigo continua valendo). Se QUALQUER análise foi regenerada agora, o consolidador RODA de novo mesmo que o consolidado passe no gate (está desatualizado em relação às entradas).</retomada>
    <acao_orquestrador>
      Task (opus) com o prompt-invólucro:
      ═══════════════════════════════════════════════════════════════════
      VOCÊ É UM SUBAGENTE CONSOLIDADOR. EXECUTE DIRETAMENTE, SEM PREÂMBULO.
      <passo>Read: .claude/agents/analise/consolidador-probatica.md — sua capacidade; siga fielmente.</passo>
      <passo>Read: $WORKSPACE/$NUMERO-pearl.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-haack.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-probatica-fbd.md</passo>
      <passo>Read: $WORKSPACE/$NUMERO-inventario.md</passo>
      <passo>Mapear as conclusões das três metodologias, identificar convergências (fortes e
             parciais), divergências (metodológicas e factuais), lacunas, obscuridades,
             omissões e contradições, produzir a síntese integrativa e a conclusão para
             subsidiar a decisão, e GRAVAR (Write) o documento COMPLETO em
             $WORKSPACE/$NUMERO-probatica-consolidado.md — abrindo com
             "# SÍNTESE PROBATÓRIA CONSOLIDADA", fechando com
             "Síntese probatória consolidada concluída.", em português COM acentos.</passo>
      <passo>Responder APENAS: "consolidado OK | $NUMERO-probatica-consolidado.md" — NÃO imprimir o documento.</passo>
      <restricoes>NUNCA inventar análises ausentes dos relatórios; NUNCA omitir divergências; NUNCA usar TodoWrite.</restricoes>
      ═══════════════════════════════════════════════════════════════════
      Validar: Bash: python scripts/verificar_probatica.py "$WORKSPACE" --etapa consolidado
      (exit 1 → contingência etapa_invalida; 2ª falha → PARAR e reportar).
    </acao_orquestrador>
    <transicao>Gate 0 → Etapa 4.</transicao>
  </etapa>

  <etapa numero="4" nome="Finalização">
    <acao_orquestrador>
      1. Gate final: Bash: python scripts/verificar_probatica.py "$WORKSPACE" --gate
         (exit 1 → algo regrediu; reportar o output e PARAR).
      2. Resumo de 1 tela ao usuário, SEM transcrever conteúdo dos documentos:
         - Processo ($NUMERO) e $WORKSPACE
         - Os 5 artefatos: $NUMERO-inventario.md, $NUMERO-pearl.md, $NUMERO-haack.md,
           $NUMERO-probatica-fbd.md e $NUMERO-probatica-consolidado.md (o PRINCIPAL) —
           marcando o que foi REAPROVEITADO da execução anterior vs gerado agora.
    </acao_orquestrador>
  </etapa>

</fases_pipeline>

<resumo_arquitetura>
PIPELINE PROBÁTICA v3.0 — por caminho + gate determinístico + retomada
│
├── 0 Preparação: $WORKSPACE/$NUMERO/$PROCESSO + verificar_probatica.py → PENDENTES (o plano)
│     entradas exigidas: $PROCESSO, linha-tempo e relatório (senão → /relatar-processo antes)
├── 1 Inventário       [Task opus] → $NUMERO-inventario.md (gate --etapa inventario)
├── 2 Tríplice em PARALELO (só as pendentes; até 3 Tasks opus no mesmo turno)
│   ├── pearl [Task opus] → $NUMERO-pearl.md          ─┐ cada uma: pula se válida;
│   ├── haack [Task opus] → $NUMERO-haack.md           │ grava arquivo; responde 1 linha;
│   └── fbd   [Task opus] → $NUMERO-probatica-fbd.md  ─┘ gate --etapa valida
├── 3 Consolidação     [Task opus] → $NUMERO-probatica-consolidado.md
│     (re-roda se QUALQUER análise da tríplice foi regenerada nesta execução)
└── 4 Finalização: verificar_probatica.py --gate + resumo (reaproveitado × gerado)

Princípios: o documento vive no ARQUIVO (nunca na conversa); a validação é do SCRIPT (âncoras
com acentos normalizados — fonte única em verificar_probatica.py); PENDENTES é o plano
(1ª rodada e retomada são a mesma operação). Vários processos = pipelines independentes em
paralelo.
</resumo_arquitetura>

<checklist_orquestrador>
- [ ] $PROCESSO, linha-tempo e relatório existem (test -f) e a varredura da Etapa 0 rodou?
- [ ] Todas as etapas VÁLIDAS foram puladas (nada redespachado)?
- [ ] Análises pendentes da tríplice despachadas em PARALELO no mesmo turno?
- [ ] Nenhum documento lido pelo orquestrador (validação só por script)?
- [ ] Subagentes responderam só a linha de status?
- [ ] Consolidador re-rodou se alguma análise da tríplice foi regenerada nesta execução?
- [ ] Gate final --gate retornou 0 antes do resumo?
- [ ] TodoWrite refletiu o reaproveitamento (etapas puladas nascem completed)?
</checklist_orquestrador>
