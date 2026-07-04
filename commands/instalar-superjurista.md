# Command: instalar-superjurista v1.0

> **Propósito:** Instala o SuperJurista no projeto atual, copiando pipelines, agentes, skills e estrutura completa para processamento de processos judiciais
>
> **Tipo:** Command direto (executa fases sequencialmente, sem delegação a subagentes)

---
description: Instala o SuperJurista no projeto atual - copia pipelines, agentes, skills e estrutura completa para processamento de processos judiciais
argument-hint: (sem argumentos)
allowed-tools: Bash Read Write AskUserQuestion Glob
---

<identidade>
  <papel>Instalador do SuperJurista - responsável por copiar o scaffold completo para o projeto do usuário</papel>
  <estilo>Metódico, cauteloso com arquivos existentes, informativo sobre o que está fazendo</estilo>
</identidade>

<proposito>
  <objetivo>Instalar todos os componentes do SuperJurista (commands, agents, skills, mcp-servers, estrutura de dados) no diretório atual do usuário, respeitando arquivos já existentes</objetivo>
  <razao>A instalação manual seria trabalhosa e propensa a erros. Este command garante que a estrutura completa seja copiada corretamente, com tratamento de conflitos e validação.</razao>
  <resultado_final>Projeto configurado com todos os artefatos do SuperJurista, pronto para uso dos pipelines</resultado_final>
</proposito>

<restricoes>
  - NUNCA sobrescrever arquivos sem confirmação explícita do usuário
  - NUNCA copiar diretórios __pycache__ ou outros artefatos de build
  - NUNCA modificar o CLAUDE.md existente sem permissão
  - SEMPRE usar ${CLAUDE_PLUGIN_ROOT} para referenciar o scaffold
  - SEMPRE mostrar resumo final com componentes instalados
  - SEMPRE usar português brasileiro com acentos corretos
</restricoes>

<contingencias>
  <se_scaffold_ausente>
    Verificar se ${CLAUDE_PLUGIN_ROOT}/scaffold/ existe.
    Se NÃO existir → informar erro: "Diretório scaffold não encontrado em ${CLAUDE_PLUGIN_ROOT}/scaffold/. Verifique a instalação do plugin."
    → Abortar instalação
  </se_scaffold_ausente>

  <se_permissao_negada>
    Se qualquer operação de cópia falhar com "Permission denied":
    → Informar o usuário sobre o erro de permissão
    → Sugerir executar com permissões elevadas
    → Abortar instalação
  </se_permissao_negada>

  <se_copia_parcial>
    Se cópia falhar no meio do processo:
    → Informar quais diretórios foram copiados com sucesso
    → Informar quais falharam
    → Sugerir re-executar /instalar-superjurista
  </se_copia_parcial>
</contingencias>

<!-- ═══════════════════════════════════════════════════════════════════════════════ -->
<!-- FASES DA INSTALAÇÃO                                                            -->
<!-- ═══════════════════════════════════════════════════════════════════════════════ -->

<fases_pipeline>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 1: VERIFICAÇÃO DO AMBIENTE                                -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="1" nome="Verificação do Ambiente">
    <objetivo>Verificar se o diretório atual é adequado para instalação e detectar conflitos</objetivo>

    <acao>
      1. **Verificar se o scaffold existe:**
         ```bash
         ls ${CLAUDE_PLUGIN_ROOT}/scaffold/commands/ > /dev/null 2>&1
         ```
         Se falhar → abortar com mensagem de erro (ver contingência se_scaffold_ausente)

      2. **Verificar instalação existente:**
         Usar Glob para checar se `.claude/commands/` já tem arquivos:
         ```
         Glob: .claude/commands/*.md
         ```

      3. **Se .claude/commands/ já existe E contém arquivos .md:**
         Usar AskUserQuestion para perguntar ao usuário:

         ```
         O diretório .claude/ já existe neste projeto e contém arquivos.
         Como deseja prosseguir?

         (A) Sobrescrever tudo - substitui todos os arquivos existentes
         (B) Mesclar - copia apenas arquivos que não existem (preserva alterações)
         (C) Cancelar - abortar instalação
         ```

         Armazenar a escolha do usuário como $MODO_COPIA:
         - Se (A) → $MODO_COPIA = "sobrescrever"
         - Se (B) → $MODO_COPIA = "mesclar"
         - Se (C) → informar "Instalação cancelada pelo usuário." e PARAR

      4. **Se .claude/ não existe ou está vazio:**
         ```
         $MODO_COPIA = "instalar"
         ```
         Prosseguir diretamente (instalação limpa)
    </acao>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 2: CÓPIA DO SCAFFOLD                                      -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="2" nome="Cópia do Scaffold">
    <objetivo>Copiar commands, agents, skills e mcp-servers do scaffold para o projeto</objetivo>

    <acao>
      1. **Criar diretórios base:**
         ```bash
         mkdir -p .claude/commands .claude/agents .claude/skills .claude/mcp-servers scripts
         ```
         (`scripts/` na RAIZ do projeto — é onde vive o motor de gate `verificar_pipeline.py`
         que os pipelines v3.0 importam; não é `.claude/scripts/`.)

      2. **Copiar conteúdo conforme $MODO_COPIA:**

         <se_modo_sobrescrever_ou_instalar>
           Cópia completa (substitui tudo):
           ```bash
           cp -r "${CLAUDE_PLUGIN_ROOT}/scaffold/commands/"* .claude/commands/
           cp -r "${CLAUDE_PLUGIN_ROOT}/scaffold/agents/"* .claude/agents/
           cp -r "${CLAUDE_PLUGIN_ROOT}/scaffold/skills/"* .claude/skills/
           cp -r "${CLAUDE_PLUGIN_ROOT}/scaffold/mcp-servers/"* .claude/mcp-servers/
           cp -r "${CLAUDE_PLUGIN_ROOT}/scaffold/scripts/"* scripts/   # motor de gate v3.0 (verificar_pipeline.py)
           ```
         </se_modo_sobrescrever_ou_instalar>

         <se_modo_mesclar>
           Cópia sem sobrescrever (preserva arquivos existentes):
           ```bash
           cp -rn "${CLAUDE_PLUGIN_ROOT}/scaffold/commands/"* .claude/commands/
           cp -rn "${CLAUDE_PLUGIN_ROOT}/scaffold/agents/"* .claude/agents/
           cp -rn "${CLAUDE_PLUGIN_ROOT}/scaffold/skills/"* .claude/skills/
           cp -rn "${CLAUDE_PLUGIN_ROOT}/scaffold/mcp-servers/"* .claude/mcp-servers/
           cp -rn "${CLAUDE_PLUGIN_ROOT}/scaffold/scripts/"* scripts/   # motor de gate v3.0 (verificar_pipeline.py)
           ```
           (A flag -n / --no-clobber impede sobrescrita de arquivos existentes)
         </se_modo_mesclar>

      3. **Limpar artefatos de build copiados acidentalmente:**
         ```bash
         find .claude/ -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
         ```

      4. **Verificar sucesso:**
         Checar se os diretórios principais foram populados:
         ```bash
         ls .claude/commands/*.md > /dev/null 2>&1 && echo "commands OK" || echo "commands FALHOU"
         ls .claude/agents/analise/*.md > /dev/null 2>&1 && echo "agents OK" || echo "agents FALHOU"
         ls .claude/skills/pje-download/SKILL.md > /dev/null 2>&1 && echo "skills OK" || echo "skills FALHOU"
         ls .claude/mcp-servers/tjsc-eproc/server.py > /dev/null 2>&1 && echo "mcp-servers OK" || echo "mcp-servers FALHOU"
         ls scripts/verificar_pipeline.py > /dev/null 2>&1 && echo "scripts OK" || echo "scripts FALHOU"
         ```
         Se qualquer um falhou → reportar erro e parar
    </acao>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 3: ARQUIVOS RAIZ                                          -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="3" nome="Arquivos Raiz">
    <objetivo>Instalar CLAUDE.md, README.md e .gitignore na raiz do projeto</objetivo>

    <acao>
      1. **CLAUDE.md:**
         - Verificar se `./CLAUDE.md` já existe
         - Se NÃO existe:
           ```bash
           cp "${CLAUDE_PLUGIN_ROOT}/scaffold/project-claude.md" ./CLAUDE.md
           ```
         - Se já existe:
           Usar AskUserQuestion:
           ```
           O arquivo CLAUDE.md já existe neste projeto.
           Como deseja prosseguir?

           (A) Substituir pelo CLAUDE.md do SuperJurista
           (B) Anexar configurações do SuperJurista ao final do arquivo existente
           (C) Pular - manter o CLAUDE.md atual sem alterações
           ```
           - Se (A): copiar sobrescrevendo
           - Se (B): usar Bash para ler o conteúdo de ${CLAUDE_PLUGIN_ROOT}/scaffold/project-claude.md e
             fazer append no CLAUDE.md existente, separando com uma linha `---` e cabeçalho
             `## SuperJurista - Configuração Adicionada`
           - Se (C): pular

      2. **README.md:**
         - Verificar se `./README.md` já existe
         - Se NÃO existe:
           ```bash
           cp "${CLAUDE_PLUGIN_ROOT}/scaffold/project-readme.md" ./README.md
           ```
         - Se já existe: pular silenciosamente (não sobrescrever README do usuário)

      3. **.gitignore:**
         - Verificar se `./.gitignore` já existe
         - Se NÃO existe:
           ```bash
           cp "${CLAUDE_PLUGIN_ROOT}/scaffold/project-gitignore" ./.gitignore
           ```
         - Se já existe: pular silenciosamente (não sobrescrever .gitignore do usuário)
    </acao>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 4: ESTRUTURA DE DADOS                                     -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="4" nome="Estrutura de Dados">
    <objetivo>Criar diretórios para armazenamento de processos</objetivo>

    <acao>
      ```bash
      mkdir -p data/sentenca data/decisao
      ```

      Esses diretórios são onde os processos baixados e seus artefatos serão armazenados:
      - `data/sentenca/` - processos aguardando sentença
      - `data/decisao/` - processos aguardando decisão interlocutória
    </acao>
  </fase>

  <!-- ═══════════════════════════════════════════════════════════════ -->
  <!-- FASE 5: RESUMO                                                  -->
  <!-- ═══════════════════════════════════════════════════════════════ -->

  <fase numero="5" nome="Resumo">
    <objetivo>Exibir resumo completo da instalação</objetivo>

    <acao>
      Exibir o seguinte resumo para o usuário (contar arquivos reais copiados via Bash se possível):

      ```
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      SuperJurista instalado com sucesso!
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

      Componentes instalados:
        16 comandos (pipelines e utilitarios)
        49 agentes (7 categorias: analise, extracao, pesquisa, redacao, revisao, lista-trf, tribunal)
        6 skills (download PJE, conversao PDF, captura sessao, analise probatoria, erro medico, terminal)
        2 servidores MCP (TJSC eProc, TCU Jurisprudencia)

      Estrutura criada:
        .claude/commands/    -- pipelines e comandos
        .claude/agents/      -- agentes especializados
        .claude/skills/      -- skills com scripts
        .claude/mcp-servers/ -- servidores MCP locais
        scripts/             -- motor de gate v3.0 (verificar_pipeline.py)
        data/sentenca/       -- processos para sentenca
        data/decisao/        -- processos para decisao

      Dependencias externas necessarias:
        Python 3.8+ com: pip install requests beautifulsoup4 pdfplumber PyPDF2 pdf2image pytesseract
        Tesseract OCR com pacote de idioma portugues
        Poppler (Windows: extrair para ~/poppler/)

      Proximo passo: capture a sessao do PJE com /capturar-sessao-pje
      ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
      ```
    </acao>
  </fase>

</fases_pipeline>

<resumo_arquitetura>
FLUXO /instalar-superjurista:

  FASE 1: Verificação do Ambiente
  │  Detecta instalação existente
  │  Pergunta ao usuário: Sobrescrever / Mesclar / Cancelar
  │
  ▼
  FASE 2: Cópia do Scaffold
  │  ${CLAUDE_PLUGIN_ROOT}/scaffold/commands/    → .claude/commands/
  │  ${CLAUDE_PLUGIN_ROOT}/scaffold/agents/      → .claude/agents/
  │  ${CLAUDE_PLUGIN_ROOT}/scaffold/skills/      → .claude/skills/
  │  ${CLAUDE_PLUGIN_ROOT}/scaffold/mcp-servers/ → .claude/mcp-servers/
  │  ${CLAUDE_PLUGIN_ROOT}/scaffold/scripts/     → scripts/ (motor de gate v3.0)
  │
  ▼
  FASE 3: Arquivos Raiz
  │  ${CLAUDE_PLUGIN_ROOT}/scaffold/project-claude.md   → ./CLAUDE.md
  │  ${CLAUDE_PLUGIN_ROOT}/scaffold/project-readme.md   → ./README.md
  │  ${CLAUDE_PLUGIN_ROOT}/scaffold/project-gitignore   → ./.gitignore
  │
  ▼
  FASE 4: Estrutura de Dados
  │  mkdir -p data/sentenca data/decisao
  │
  ▼
  FASE 5: Resumo
     Exibe componentes instalados e próximos passos
</resumo_arquitetura>
