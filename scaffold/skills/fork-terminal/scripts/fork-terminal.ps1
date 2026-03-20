<#
.SYNOPSIS
    Fork Terminal - Abre multiplas abas no Windows Terminal usando arquivos batch.

.EXAMPLE
    .\fork-terminal.ps1 -Prompts "/pipeline-sentenca data/decisao/proc1", "/pipeline-sentenca data/decisao/proc2"
#>

param(
    [Parameter(Mandatory=$true)]
    [string[]]$Prompts,

    [switch]$NoYolo
)

$workDir = (Get-Location).Path
$yolo = if ($NoYolo) { "" } else { "--dangerously-skip-permissions" }

# Validar
if ($Prompts.Count -eq 0) { Write-Error "Forneca pelo menos um prompt."; exit 1 }
if ($Prompts.Count -gt 10) { Write-Error "Maximo 10 abas."; exit 1 }

Write-Host "Fork Terminal - $($Prompts.Count) aba(s)" -ForegroundColor Cyan
Write-Host "YOLO: $(-not $NoYolo)" -ForegroundColor Yellow

# Diretorio temporario para os arquivos batch
$tempDir = Join-Path $env:TEMP "fork-terminal"
if (-not (Test-Path $tempDir)) {
    New-Item -ItemType Directory -Path $tempDir | Out-Null
}

# Criar arquivos batch e construir argumentos para wt.exe
$wtArgs = @()
$batchFiles = @()

for ($i = 0; $i -lt $Prompts.Count; $i++) {
    $prompt = $Prompts[$i]

    Write-Host "Aba $($i+1): $prompt" -ForegroundColor Green

    # Criar arquivo batch temporario
    $batchFile = Join-Path $tempDir "fork-$i-$(Get-Date -Format 'HHmmss').bat"
    $batchFiles += $batchFile

    # Conteudo do batch (sem CLAUDE_CONFIG_DIR - usa .claude padrao)
    $batchContent = "@echo off`r`ncd /d `"$workDir`"`r`n"
    $batchContent += "claude $yolo `"$prompt`"`r`n"

    # Escrever arquivo batch
    [System.IO.File]::WriteAllText($batchFile, $batchContent, [System.Text.Encoding]::ASCII)

    if ($i -eq 0) {
        # Primeira aba
        $wtArgs += "-d"
        $wtArgs += "`"$workDir`""
        $wtArgs += "cmd"
        $wtArgs += "/k"
        $wtArgs += "`"$batchFile`""
    } else {
        # Abas adicionais
        $wtArgs += ";"
        $wtArgs += "new-tab"
        $wtArgs += "-d"
        $wtArgs += "`"$workDir`""
        $wtArgs += "cmd"
        $wtArgs += "/k"
        $wtArgs += "`"$batchFile`""
    }
}

Write-Host "`nExecutando wt.exe com batch files..." -ForegroundColor Cyan

# Debug
Write-Host "Batch files criados:" -ForegroundColor DarkGray
foreach ($bf in $batchFiles) {
    Write-Host "  $bf" -ForegroundColor DarkGray
}

# Executar
try {
    Start-Process wt -ArgumentList $wtArgs
    Write-Host "OK: $($Prompts.Count) aba(s) aberta(s)" -ForegroundColor Green
} catch {
    Write-Error "Erro: $_"
    exit 1
}
