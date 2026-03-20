---
description: Abre multiplas abas no Windows Terminal para execucao paralela de Claude Code
argument-hint: [caminhos de processos separados por espaco]
allowed-tools: Bash Read
---

# /fork-terminal

<identidade>
  <papel>Executor de paralelizacao via Windows Terminal</papel>
</identidade>

<proposito>
  Abrir multiplas abas no Windows Terminal, cada uma executando Claude Code com YOLO mode.
  Permite processar multiplos processos judiciais em paralelo (P-Thread).
</proposito>

<instrucoes>
  <passo numero="1" nome="Parsear argumentos">
    $ARGUMENTS contem os caminhos de processos separados por espaco.

    Formato esperado:
    - `data/sentenca/proc1 data/sentenca/proc2 data/sentenca/proc3`
    - `data/decisao/0808008-27.2025.4.05.8100 data/decisao/0805304-75.2024.4.05.8100`

    Extrair cada caminho e construir o prompt `/pipeline-sentenca <caminho>` para cada.
  </passo>

  <passo numero="2" nome="Construir array de prompts">
    Montar array PowerShell no formato:
    ```
    @('/pipeline-sentenca path1', '/pipeline-sentenca path2', ...)
    ```

    Limite: maximo 10 caminhos (10 abas).
  </passo>

  <passo numero="3" nome="Executar fork">
    IMPORTANTE: Usar MSYS_NO_PATHCONV=1 para evitar conversao de paths no Git Bash.

    ```bash
    MSYS_NO_PATHCONV=1 powershell.exe -ExecutionPolicy Bypass -Command "& '.claude/skills/fork-terminal/scripts/fork-terminal.ps1' -Prompts @('/pipeline-sentenca path1', '/pipeline-sentenca path2') -Claude 'claude2'"
    ```
  </passo>

  <passo numero="4" nome="Reportar">
    Informar ao usuario:
    - Quantas abas foram abertas
    - O que cada aba esta executando
    - Como alternar entre abas (Ctrl+Tab no Windows Terminal)
  </passo>
</instrucoes>

<exemplos>
  <exemplo>
    Entrada: /fork-terminal data/decisao/0808008-27.2025.4.05.8100 data/decisao/0805304-75.2024.4.05.8100
    Execucao:
    ```bash
    MSYS_NO_PATHCONV=1 powershell.exe -ExecutionPolicy Bypass -Command "& '.claude/skills/fork-terminal/scripts/fork-terminal.ps1' -Prompts @('/pipeline-sentenca data/decisao/0808008-27.2025.4.05.8100', '/pipeline-sentenca data/decisao/0805304-75.2024.4.05.8100') -Claude 'claude2'"
    ```
    Resultado: 2 abas processando decisoes em paralelo
  </exemplo>

  <exemplo>
    Entrada: /fork-terminal data/sentenca/0814624 data/sentenca/0807674 data/sentenca/0812345
    Execucao:
    ```bash
    MSYS_NO_PATHCONV=1 powershell.exe -ExecutionPolicy Bypass -Command "& '.claude/skills/fork-terminal/scripts/fork-terminal.ps1' -Prompts @('/pipeline-sentenca data/sentenca/0814624', '/pipeline-sentenca data/sentenca/0807674', '/pipeline-sentenca data/sentenca/0812345') -Claude 'claude2'"
    ```
    Resultado: 3 abas processando sentencas em paralelo
  </exemplo>
</exemplos>

<restricoes>
  - NUNCA abrir mais de 10 abas
  - SEMPRE usar YOLO mode (--dangerously-skip-permissions)
  - SEMPRE usar MSYS_NO_PATHCONV=1 antes do powershell.exe
  - SEMPRE usar -Claude 'claude2' (conta padrao)
</restricoes>
