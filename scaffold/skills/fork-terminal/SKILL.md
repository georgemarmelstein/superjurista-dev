---
name: fork-terminal
description: Abre multiplas abas no Windows Terminal para execucao paralela de Claude Code
version: 2.0.0
author: SuperJurista
triggers:
  - fork terminal
  - abrir terminais
  - paralelo
  - pthread
  - multiplos processos
---

# Fork Terminal Skill

<identidade>
  <papel>Executor de paralelizacao via multiplas abas do Windows Terminal</papel>
  <dominio>Automacao de terminal, execucao paralela, P-Thread</dominio>
</identidade>

<proposito>
  <objetivo>Permitir execucao paralela de Claude Code em multiplas abas do Windows Terminal</objetivo>
  <razao>Processar multiplos processos judiciais simultaneamente, aumentando throughput</razao>
  <resultado>N abas abertas, cada uma executando Claude Code com um comando especifico</resultado>
</proposito>

<quando_usar>
  <gatilhos>
    - Usuario pede para "abrir terminais em paralelo"
    - Usuario menciona "fork terminal" ou "pthread"
    - Usuario quer processar multiplos processos judiciais ao mesmo tempo
    - Usuario pede para "rodar N instancias" de algo
  </gatilhos>

  <exclusoes>
    - NAO usar para tarefas que precisam de contexto compartilhado
    - NAO usar se usuario quer resultado consolidado (usar Task tool)
    - NAO usar para menos de 2 comandos (sem beneficio)
  </exclusoes>
</quando_usar>

<arquitetura>
  <problema>
    Passar comandos com espacos e barras via linha de comando envolve multiplas
    camadas de interpretacao (Git Bash -> PowerShell -> wt.exe -> CMD -> Claude).
    Cada camada tem regras diferentes de escape, causando corrupcao dos argumentos.
  </problema>

  <solucao>
    Usar arquivos batch temporarios elimina problemas de escape.
    Cada aba recebe seu proprio arquivo .bat com o comando completo.
    Os arquivos sao criados em %TEMP%/fork-terminal/ e executados via wt.exe.
  </solucao>

  <fluxo>
    1. Script PowerShell recebe array de prompts
    2. Para cada prompt, cria arquivo .bat em %TEMP%/fork-terminal/
    3. Cada .bat contem: cd, set CLAUDE_CONFIG_DIR, claude "prompt"
    4. wt.exe abre N abas, cada uma executando seu .bat
  </fluxo>
</arquitetura>

<scripts>
  <script nome="fork-terminal.ps1" caminho=".claude/skills/fork-terminal/scripts/fork-terminal.ps1">
    Script PowerShell que abre multiplas abas no Windows Terminal.

    Parametros:
    - -Prompts: Array de prompts para o Claude (obrigatorio)
    - -Claude: Conta do Claude - "claude", "claude1", "claude2" (default: claude2)
    - -NoYolo: Desabilita --dangerously-skip-permissions

    Execucao (IMPORTANTE - usar MSYS_NO_PATHCONV=1 no Git Bash):
    ```bash
    MSYS_NO_PATHCONV=1 powershell.exe -ExecutionPolicy Bypass -Command "& '.claude/skills/fork-terminal/scripts/fork-terminal.ps1' -Prompts @('prompt1', 'prompt2')"
    ```
  </script>
</scripts>

<instrucoes>
  <passo numero="1" nome="Identificar comandos">
    Identifique quais comandos o usuario quer executar em paralelo.
    - Se for pipeline-sentenca: extrair caminhos dos processos
    - Se for comando generico: usar diretamente
  </passo>

  <passo numero="2" nome="Construir array de prompts">
    Montar array PowerShell com os prompts:
    ```
    @('/pipeline-sentenca path1', '/pipeline-sentenca path2')
    ```
  </passo>

  <passo numero="3" nome="Executar script">
    Usar Bash com MSYS_NO_PATHCONV=1 para evitar conversao de paths:
    ```bash
    MSYS_NO_PATHCONV=1 powershell.exe -ExecutionPolicy Bypass -Command "& '.claude/skills/fork-terminal/scripts/fork-terminal.ps1' -Prompts @('/comando arg1', '/comando arg2') -Claude 'claude2'"
    ```
  </passo>

  <passo numero="4" nome="Confirmar execucao">
    Informar ao usuario:
    - Quantas abas foram abertas
    - Qual comando esta rodando em cada uma
    - Como acompanhar o progresso (Ctrl+Tab no Windows Terminal)
  </passo>
</instrucoes>

<exemplos>
  <exemplo nome="Processar 2 processos judiciais em paralelo">
    <entrada>
      Usuario: "Processa esses 2 processos em paralelo: data/decisao/0808008 e data/decisao/0805304"
    </entrada>
    <execucao>
      ```bash
      MSYS_NO_PATHCONV=1 powershell.exe -ExecutionPolicy Bypass -Command "& '.claude/skills/fork-terminal/scripts/fork-terminal.ps1' -Prompts @('/pipeline-sentenca data/decisao/0808008-27.2025.4.05.8100', '/pipeline-sentenca data/decisao/0805304-75.2024.4.05.8100') -Claude 'claude2'"
      ```
    </execucao>
    <resultado>
      2 abas abertas no Windows Terminal, cada uma processando um processo judicial.
    </resultado>
  </exemplo>

  <exemplo nome="Fork para revisar codigo com F-Thread">
    <entrada>
      Usuario: "Fork 3 terminais para revisar o modulo de autenticacao"
    </entrada>
    <execucao>
      ```bash
      MSYS_NO_PATHCONV=1 powershell.exe -ExecutionPolicy Bypass -Command "& '.claude/skills/fork-terminal/scripts/fork-terminal.ps1' -Prompts @('Review the authentication module for security issues', 'Review the authentication module for performance issues', 'Review the authentication module for code quality') -Claude 'claude2'"
      ```
    </execucao>
    <resultado>
      3 revisoes paralelas do mesmo codigo, cada uma com foco diferente.
      Depois o usuario pode consolidar os resultados (F-Thread / Fusion).
    </resultado>
  </exemplo>
</exemplos>

<restricoes>
  <regra tipo="NUNCA">Executar sem Windows Terminal instalado</regra>
  <regra tipo="NUNCA">Abrir mais de 10 abas (limite pratico por RAM/CPU)</regra>
  <regra tipo="SEMPRE">Usar YOLO mode para execucao nao-interativa</regra>
  <regra tipo="SEMPRE">Usar MSYS_NO_PATHCONV=1 antes do comando PowerShell</regra>
  <regra tipo="SEMPRE">Informar ao usuario quantas abas foram abertas</regra>
</restricoes>

<conhecimento>
  <conceito nome="P-Thread (Parallel Thread)">
    Conceito do framework Thread-Based Engineering de IndyDevDan.
    Multiplos agentes rodando em paralelo, cada um com seu contexto isolado.
    Usuario prompta no inicio, revisa no final de cada thread.
  </conceito>

  <conceito nome="F-Thread (Fusion Thread)">
    Variacao onde multiplos agentes recebem o MESMO prompt.
    Resultados sao consolidados/fundidos pelo usuario.
    Util para aumentar confianca em revisoes.
  </conceito>

  <conceito nome="YOLO Mode">
    Flag --dangerously-skip-permissions do Claude Code.
    Permite execucao sem confirmacao interativa.
    Necessario para automacao e paralelizacao.
  </conceito>

  <conceito nome="MSYS_NO_PATHCONV">
    Variavel de ambiente que desabilita conversao automatica de paths no Git Bash.
    Sem ela, /pipeline-sentenca vira C:/Program Files/Git/pipeline-sentenca.
    SEMPRE usar antes de chamar powershell.exe com paths que comecam com /.
  </conceito>

  <conceito nome="Arquivos Batch Temporarios">
    Solucao para evitar problemas de escape em multiplas camadas de shell.
    Cada comando e escrito em um arquivo .bat separado.
    O wt.exe executa os .bat, que contem o comando sem necessidade de escape.
  </conceito>
</conhecimento>

<dependencias>
  <dependencia nome="Windows Terminal" obrigatoria="true">
    Instalado via Microsoft Store ou winget.
    Comando: wt.exe
  </dependencia>
  <dependencia nome="PowerShell" obrigatoria="true">
    Ja vem instalado no Windows 10/11.
  </dependencia>
  <dependencia nome="Claude Code CLI" obrigatoria="true">
    Instalado globalmente: npm install -g @anthropic-ai/claude-code
  </dependencia>
</dependencias>

<limites>
  | Recurso | Limite | Razao |
  |---------|--------|-------|
  | Abas | 10 | RAM/CPU - cada instancia consome ~200-400MB |
  | Prompts | Sem limite de tamanho | Arquivos batch suportam comandos longos |
  | Contas Claude | claude, claude1, claude2 | Configuradas via CLAUDE_CONFIG_DIR |
</limites>
