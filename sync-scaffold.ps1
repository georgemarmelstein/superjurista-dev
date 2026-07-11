# sync-scaffold.ps1 — regenera o scaffold/ a partir do superjurista VIVO
#
# Regra de ouro (2026-07-11): o scaffold NUNCA é editado à mão. O projeto
# C:\Users\georg\superjurista é a fonte da verdade; o scaffold é uma release
# gerada. Rodar este script antes de cada bump de versão do plugin.
#
# Política de exclusões:
#   PESSOAIS  — artefatos do magistrado, nunca distribuir:
#               agents/pesquisa/pesquisador-george.md, agents/redacao/criar-palestra.md
#   META      — fornecidos pelo próprio plugin (commands/skills na raiz do -dev),
#               não duplicar no scaffold: criar-agente, criar-orquestrador,
#               criar-skill, criar-team, planejar-sistema (+ skills criar-skill,
#               criar-mcp-precedente)
#   HIGIENE   — __pycache__, *.pyc, credenciais, .env, sessões, logs, HAR
#   MCPs      — lista fixa de 5 (decisão v1.2.0): bnp-api, cjf-jurisprudencia e
#               tnu-eproc vêm da fonte única ~/.claude/mcp-servers; tcu e tjsc
#               vêm do projeto. hudoc-echr fica fora até decisão em contrário.
#
# Preservados (pertencem ao scaffold, não ao projeto):
#   project-claude.md, project-gitignore, project-readme.md

$ErrorActionPreference = 'Stop'

$Projeto  = 'C:\Users\georg\superjurista\.claude'
$ProjetoScripts = 'C:\Users\georg\superjurista\scripts'
$Global   = 'C:\Users\georg\.claude\mcp-servers'
$Scaffold = Join-Path $PSScriptRoot 'scaffold'

$ExcluirAgents   = @('pesquisa\pesquisador-george.md', 'redacao\criar-palestra.md')
$ExcluirCommands = @('criar-agente.md', 'criar-orquestrador.md', 'criar-skill.md',
                     'criar-team.md', 'planejar-sistema.md')
$ExcluirSkills   = @('criar-skill', 'criar-mcp-precedente')
$McpsGlobais     = @('bnp-api', 'cjf-jurisprudencia', 'tnu-eproc')
$McpsProjeto     = @('tcu-jurisprudencia', 'tjsc-eproc')
$Higiene         = @('__pycache__', '*.pyc', '*credentials*', '.env', '*.log',
                     'sessao*.json', 'pje_session*', '*.har', 'cookies*')

function Copiar-Filtrado($origem, $destino) {
    robocopy $origem $destino /E /XD ($Higiene | Where-Object { $_ -notmatch '\*' }) `
        /XF ($Higiene | Where-Object { $_ -match '\*' }) /NFL /NDL /NJH /NJS /NP | Out-Null
    if ($LASTEXITCODE -ge 8) { throw "robocopy falhou: $origem -> $destino" }
}

Write-Output "[INICIO] sync-scaffold: $Projeto -> $Scaffold"

# 1. Limpar as áreas geradas (preserva project-*.md e project-gitignore)
foreach ($area in 'agents', 'commands', 'skills', 'scripts', 'mcp-servers') {
    $alvo = Join-Path $Scaffold $area
    if (Test-Path $alvo) { Remove-Item -Recurse -Force $alvo }
}

# 2. Agents (menos os pessoais)
Copiar-Filtrado (Join-Path $Projeto 'agents') (Join-Path $Scaffold 'agents')
foreach ($a in $ExcluirAgents) {
    $f = Join-Path $Scaffold "agents\$a"
    if (Test-Path $f) { Remove-Item -Force $f; Write-Output "[OK] excluido (pessoal): agents\$a" }
}

# 3. Commands (menos os meta, que o plugin fornece)
Copiar-Filtrado (Join-Path $Projeto 'commands') (Join-Path $Scaffold 'commands')
foreach ($c in $ExcluirCommands) {
    $f = Join-Path $Scaffold "commands\$c"
    if (Test-Path $f) { Remove-Item -Force $f; Write-Output "[OK] excluido (meta): commands\$c" }
}

# 4. Skills (menos as meta)
Copiar-Filtrado (Join-Path $Projeto 'skills') (Join-Path $Scaffold 'skills')
foreach ($s in $ExcluirSkills) {
    $d = Join-Path $Scaffold "skills\$s"
    if (Test-Path $d) { Remove-Item -Recurse -Force $d; Write-Output "[OK] excluido (meta): skills\$s" }
}

# 5. Scripts do motor de validação (sem testes)
New-Item -ItemType Directory -Force (Join-Path $Scaffold 'scripts') | Out-Null
Get-ChildItem $ProjetoScripts -File -Filter '*.py' |
    Where-Object { $_.Name -notlike 'test_*' } |
    Copy-Item -Destination (Join-Path $Scaffold 'scripts')

# 6. MCPs (lista fixa; fonte única global + locais do projeto)
foreach ($m in $McpsGlobais)  { Copiar-Filtrado (Join-Path $Global $m) (Join-Path $Scaffold "mcp-servers\$m") }
foreach ($m in $McpsProjeto)  { Copiar-Filtrado (Join-Path $Projeto "mcp-servers\$m") (Join-Path $Scaffold "mcp-servers\$m") }

# 6.5 Motor /criar-sistema — fonte da verdade: global ~/.claude
#     Os 5 agentes e os references/assets da skill são IDÊNTICOS por contrato
#     (cópia só quando o conteúdo real divergir, ignorando EOL). O SKILL.md do
#     plugin é ADAPTADO (${CLAUDE_PLUGIN_ROOT} + subagent_type namespaced) —
#     NUNCA copiar cego; o script só avisa se o global mudou depois dele.
$GlobalClaude = 'C:\Users\georg\.claude'
function Sync-SeDivergir($origem, $destino) {
    $a = (Get-Content -Raw $origem) -replace "`r`n", "`n"
    $b = if (Test-Path $destino) { (Get-Content -Raw $destino) -replace "`r`n", "`n" } else { $null }
    if ($a -ne $b) {
        New-Item -ItemType Directory -Force (Split-Path $destino) | Out-Null
        Copy-Item $origem $destino -Force
        Write-Output "[OK] motor sincronizado: $(Split-Path -Leaf $destino)"
    }
}
foreach ($g in Get-ChildItem "$GlobalClaude\agents\geradores" -Filter '*.md') {
    Sync-SeDivergir $g.FullName (Join-Path $PSScriptRoot "agents\$($g.Name)")
}
foreach ($sub in 'references', 'assets') {
    Get-ChildItem "$GlobalClaude\skills\criar-sistema\$sub" -File -Recurse |
        Where-Object { $_.FullName -notmatch '__pycache__' } |
        ForEach-Object {
            $rel = $_.FullName.Substring("$GlobalClaude\skills\criar-sistema\".Length)
            Sync-SeDivergir $_.FullName (Join-Path $PSScriptRoot "skills\criar-sistema\$rel")
        }
}
$skillGlobal = Get-Item "$GlobalClaude\skills\criar-sistema\SKILL.md"
$skillPlugin = Get-Item (Join-Path $PSScriptRoot 'skills\criar-sistema\SKILL.md')
if ($skillGlobal.LastWriteTime -gt $skillPlugin.LastWriteTime) {
    Write-Output "[AVISO] SKILL.md global do criar-sistema mudou depois da versao adaptada do plugin - readaptar manualmente."
}

# 7. Varredura final de segredos (defesa em profundidade)
$suspeitos = Get-ChildItem $Scaffold -Recurse -File |
    Where-Object { $_.Name -match 'credential|\.env$|sessao.*\.json|pje_session|\.har$' }
if ($suspeitos) {
    $suspeitos | ForEach-Object { Write-Output "[ERRO] segredo no scaffold: $($_.FullName)" }
    throw 'Scaffold contem arquivos suspeitos - revisar antes de commitar.'
}

$total = (Get-ChildItem $Scaffold -Recurse -File | Measure-Object).Count
Write-Output "[FIM] scaffold regenerado: $total arquivos. Revisar 'git diff --stat' antes do commit."
exit 0  # robocopy devolve 1 em copia bem-sucedida; nao deixar vazar como erro
