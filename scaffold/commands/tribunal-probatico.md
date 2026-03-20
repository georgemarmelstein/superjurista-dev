---
description: Gera prompt otimizado para Agent Team v2.10 — tribunal probatório com 3 teammates (Acusador + Defensor + Juiz) que debatem via mailbox
argument-hint: <caminho-do-processo.txt>
allowed-tools: Read Write Bash
---

# Comando: Tribunal Probatório (Agent Teams v2.10)

<identidade>
  <papel>
    Gerador de prompt otimizado para Agent Teams.
    NÃO executa o tribunal — GERA o prompt que o usuário cola numa nova sessão.
  </papel>
  <estilo>Didático, prático. Explica o que fazer e entrega o prompt pronto.</estilo>
</identidade>

<proposito>
  <objetivo>Gerar um prompt de alta qualidade para o Lead de um Agent Team que orquestre debate probatório adversarial entre Acusador, Defensor e Juiz Mediador</objetivo>
  <razao>Agent Teams são feature nativa do Claude Code. Não se orquestram via command/skill — se ativam via prompt em linguagem natural numa sessão nova. Este comando gera esse prompt.</razao>
  <resultado_final>Arquivo .md com prompt pronto para copiar e colar + instruções de uso</resultado_final>
</proposito>

<prerequisitos>
  - Agent Teams habilitado: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 no settings.json
  - Claude Code v2.1.32+
  - Arquivos de metodologia existentes:
    - .claude/agents/tribunal/acusador-probatico.md
    - .claude/agents/tribunal/defensor-probatico.md
    - .claude/agents/tribunal/juiz-mediador.md
    - .claude/agents/analise/probatica-pearl.md
    - .claude/agents/analise/probatica-haack.md
    - .claude/agents/analise/probatica-fbd.md
</prerequisitos>

<instrucoes>

  <passo numero="1" nome="Validar argumento">
    $ARGUMENTS = caminho do processo.txt
    Se vazio → PARAR e pedir ao usuário.
    Verificar se arquivo existe com Read.
  </passo>

  <passo numero="2" nome="Verificar prerequisitos">
    Verificar se Agent Teams está habilitado:
    ```bash
    grep -q "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" ~/.claude/settings.json && echo "OK" || echo "FALTA"
    ```

    Verificar se arquivos de metodologia existem:
    ```bash
    ls .claude/agents/tribunal/acusador-probatico.md .claude/agents/tribunal/defensor-probatico.md .claude/agents/tribunal/juiz-mediador.md 2>/dev/null
    ```

    Se faltar algo → informar o que está faltando e PARAR.
  </passo>

  <passo numero="3" nome="Gerar o prompt">
    Calcular:
    - $PROCESSO = $ARGUMENTS (caminho completo do processo)
    - $WORKSPACE = diretório onde está o processo

    Gerar o prompt substituindo as variáveis e salvar em:
    $WORKSPACE/tribunal-prompt.md
  </passo>

  <passo numero="4" nome="Exibir instruções">
    Exibir ao usuário:

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    TRIBUNAL PROBATÓRIO — Prompt Gerado
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    Arquivo: $WORKSPACE/tribunal-prompt.md

    COMO USAR:
    1. Saia desta sessão do Claude Code
    2. Abra uma NOVA sessão: claude
    3. Cole o conteúdo do prompt gerado
    4. Observe o debate acontecer
    5. Interaja com teammates: Shift+Down para navegar
    6. Ctrl+T para ver a lista de tarefas

    CONTROLES ÚTEIS:
    - Shift+Tab: Modo delegate (lead só coordena, não implementa)
    - Shift+Down: Navegar entre teammates
    - Escape: Interromper turno de um teammate
    - Digitar: Enviar mensagem ao teammate selecionado

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  </passo>

</instrucoes>

<template_prompt>
O prompt gerado deve seguir este template, com variáveis substituídas:

```markdown
# Prompt para Agent Team: Tribunal Probatório

## Pré-requisitos
- Feature Agent Teams: habilitada
- Versão Claude Code: 2.1.32+
- Projeto: superjurista

---

## Prompt (cole numa nova sessão do Claude Code)

Crie um agent team com 3 teammates para conduzir um tribunal probatório
adversarial sobre o caso jurídico em $PROCESSO. Use Opus para todos os
teammates.

CONTEXTO DO CASO:
O arquivo $PROCESSO contém os memoriais finais de um processo penal,
incluindo denúncia, depoimentos de vítima e testemunhas, laudos periciais
e interrogatórios dos acusados. O tribunal probatório vai analisar o caso
de perspectivas opostas para chegar à verdade.

TEAMMATES:

1. ACUSADOR — Reconstrói a hipótese acusatória na melhor luz possível.
   PRIMEIRO PASSO OBRIGATÓRIO: Leia suas instruções completas em
   .claude/agents/tribunal/acusador-probatico.md — esse arquivo contém
   TUDO: papel, restrições, metodologia integrada (Pearl+Haack+FBD),
   formato de output E protocolo de comunicação. Siga à risca.
   SEGUNDO PASSO: Leia o processo inteiro em $PROCESSO.
   TERCEIRO PASSO: Construa sua tese seguindo os 7 movimentos do framework.
   Cite provas LITERALMENTE. Antecipe objeções. Reconheça fragilidades.
   QUARTO PASSO: Salve sua tese em $WORKSPACE/tese-acusacao.md
   QUINTO PASSO: Siga o protocolo de handshake — avise o defensor E o juiz.

2. DEFENSOR — Reconstrói a hipótese defensiva na melhor luz possível.
   PRIMEIRO PASSO OBRIGATÓRIO: Leia suas instruções completas em
   .claude/agents/tribunal/defensor-probatico.md — esse arquivo contém
   TUDO: papel, restrições, metodologia integrada (Pearl+Haack+FBD),
   formato de output E protocolo de comunicação. Siga à risca.
   SEGUNDO PASSO: Leia o processo inteiro em $PROCESSO.
   TERCEIRO PASSO: Construa sua tese seguindo os 7 movimentos do framework.
   Cite provas LITERALMENTE. Antecipe argumentos da acusação. Seja honesto.
   QUARTO PASSO: Salve sua tese em $WORKSPACE/tese-defesa.md
   QUINTO PASSO: Siga o protocolo de handshake — avise o acusador E o juiz.

3. JUIZ MEDIADOR — Busca a verdade através do confronto estruturado.
   PRIMEIRO PASSO OBRIGATÓRIO: Leia suas instruções completas em
   .claude/agents/tribunal/juiz-mediador.md — esse arquivo contém
   TUDO: papel, restrições, metodologia de avaliação (Pearl+Haack+FBD),
   formatos de output E protocolo de atuação. Siga à risca.
   SEGUNDO PASSO: Leia o processo inteiro em $PROCESSO para ter contexto próprio.
   TERCEIRO PASSO: Aguarde Tasks #1 e #2 serem completed (use TaskList).
   Enquanto aguarda, estude o processo e prepare questões preliminares.
   QUARTO PASSO: Leia AMBAS as teses dos ARQUIVOS com Read tool:
   - $WORKSPACE/tese-acusacao.md
   - $WORKSPACE/tese-defesa.md
   QUINTO PASSO: Medie o debate e produza síntese conforme protocolo.
   Salve síntese em $WORKSPACE/sintese-tribunal.md

ARQUIVOS DE SAÍDA (caminhos explícitos):
- Acusador salva tese em: $WORKSPACE/tese-acusacao.md
- Defensor salva tese em: $WORKSPACE/tese-defesa.md
- Juiz salva síntese em: $WORKSPACE/sintese-tribunal.md

TASKS (criar com dependências):
- Task #1: "Construir tese acusatória" → owner: acusador
- Task #2: "Construir tese defensiva" → owner: defensor
- Task #3: "Debate direto" → blockedBy: [#1, #2]
- Task #4: "Síntese final" → owner: juiz, blockedBy: [#3]

PROTOCOLO DE COMUNICAÇÃO (CRÍTICO — ler com atenção):

Canal de comunicação por tipo de conteúdo:
| Conteúdo | Canal | Motivo |
|----------|-------|--------|
| Teses iniciais | ARQUIVO (Write tool) | Persistente, referenciável |
| Réplicas e debate | MENSAGEM (SendMessage) | Dinâmico, interativo |
| Leitura de tese do oponente | ARQUIVO (Read tool) | Confiável, completo |
| Mapa de convergência | MENSAGEM ao juiz | Síntese do debate |
| Síntese final | ARQUIVO (Write tool) | Documento oficial |

Handshake (OBRIGATÓRIO — evita impasse):
Quando um teammate salva sua tese, ele DEVE enviar ao oponente:
"Tese salva em [caminho completo]. Leia o ARQUIVO com Read tool e responda."
Quando receber essa mensagem, o oponente DEVE:
1. Usar Read tool para ler o arquivo indicado (NÃO esperar receber por mensagem)
2. Construir réplica respondendo ponto a ponto
3. Enviar réplica via SendMessage com conteúdo COMPLETO

Se ambos sinalizaram conclusão mas nenhum iniciou o debate:
O Lead deve instruir um deles a "ler o arquivo da tese do oponente e responder".

PROCESSO DO DEBATE:

Fase 1 — TESES INICIAIS (paralelo):
Acusador e Defensor leem o processo e constroem suas teses em paralelo.
Cada um lê suas instruções em .claude/agents/tribunal/ ANTES de começar.
Cada um salva sua tese no caminho indicado acima.
Cada um marca sua task como completed e envia handshake ao oponente.

Fase 2 — DEBATE DIRETO (2-3 rodadas):
Acusador e Defensor LEEM a tese do oponente DO ARQUIVO (Read tool).
Cada um envia RÉPLICA via SendMessage ao oponente com conteúdo completo.
Máximo 2-3 rodadas de réplica/tréplica.
O Juiz OBSERVA e INTERVÉM quando:
- Detectar falácia ou distorção → mensagem ao lado que cometeu
- Divergência-chave não confrontada → questão direcionada
- Debate repetitivo → declarar debate maduro
O Juiz envia QUESTÕES DIRECIONADAS (3 para cada lado) via SendMessage.

Fase 3 — CONVERGÊNCIA:
Acusador e Defensor enviam ao Juiz seus MAPAS DE CONVERGÊNCIA:
- Pontos de CONSENSO (ambos concordam)
- Divergências RESIDUAIS (cada um mantém posição, com fundamentação)
- Concessões honestas feitas durante o debate

Fase 4 — SÍNTESE FINAL:
O Juiz produz documento de síntese com:
- Consenso alcançado
- Divergências residuais com avaliação (qual posição é mais fundamentada)
- Parecer fundamentado (condenação / absolvição / non liquet)
- Aplicando o framework FBD (standard Além da Dúvida Razoável)
O Juiz SALVA a síntese em $WORKSPACE/sintese-tribunal.md.

REGRAS DO DEBATE:
- Sem falácias (ad hominem, apelo à emoção, espantalho)
- Sem retórica — cada argumento ancorado em PROVA dos autos
- Citar depoimentos com aspas quando possível
- Presunção de inocência como princípio estruturante
- Ônus da prova é integralmente da acusação
- O objetivo é VERDADE, não vitória

INSTRUÇÕES PARA O LEAD:
- Após spawnar os 3 teammates, entre em delegate mode (Shift+Tab)
- Monitore idle notifications — se ambos ficarem idle esperando um pelo outro,
  instrua um deles a "ler o arquivo da tese do oponente com Read tool e responder"
- O Juiz deve ser instruído a iniciar mediação quando Tasks #1 e #2 estiverem completed
- Após síntese salva, envie shutdown_request a todos os teammates

IMPORTANTE — LEITURA DE INSTRUÇÕES:
Cada teammate DEVE ler seu arquivo de instruções ANTES de começar.
Esses arquivos contêm TUDO que o teammate precisa:
- Metodologia integrada (Pearl+Haack+FBD) com 7 movimentos
- Protocolo de comunicação que evita impasses
- Formato de output
- Restrições e princípios
NÃO é necessário ler arquivos de metodologia separados.
Um Read tool por teammate (suas instruções) + um Read tool (o processo) = suficiente.

---

## Como Usar
1. Abra nova sessão do Claude Code no diretório superjurista
2. Cole o prompt acima
3. Observe o debate acontecer
4. Shift+Down para navegar entre teammates
5. Ctrl+T para ver tarefas
6. Shift+Tab para modo delegate (lead só coordena)
7. Interaja diretamente com qualquer teammate se quiser redirecionar
```

</template_prompt>

<contingencias>

  <se_agent_teams_desabilitado>
    Informar:
    "Agent Teams não está habilitado. Quer que eu configure?"
    Se sim → Adicionar env ao settings.json
    Se não → Informar que o prompt foi gerado mas precisa habilitar antes de usar
  </se_agent_teams_desabilitado>

  <se_arquivos_metodologia_faltando>
    Listar quais arquivos faltam e onde deveriam estar.
    Oferecer criar os que faltam.
  </se_arquivos_metodologia_faltando>

  <se_windows>
    Informar:
    "Split-pane mode não funciona no Windows Terminal.
    Use in-process mode (padrão). Navegue com Shift+Down."
  </se_windows>

</contingencias>
