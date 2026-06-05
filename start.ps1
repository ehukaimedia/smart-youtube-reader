param(
    [switch]$Share
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Require-Command($Name, $InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Error "$Name is not installed. $InstallHint"
    }
}

function Stop-AppProcesses {
    if ($script:BackendProcess -and -not $script:BackendProcess.HasExited) {
        Stop-Process -Id $script:BackendProcess.Id -Force -ErrorAction SilentlyContinue
    }
    if ($script:FrontendProcess -and -not $script:FrontendProcess.HasExited) {
        Stop-Process -Id $script:FrontendProcess.Id -Force -ErrorAction SilentlyContinue
    }
}

function Run-InDirectory($Directory, $Command) {
    Push-Location $Directory
    try {
        & $Command
    } finally {
        Pop-Location
    }
}

try {
    Write-Host "Starting Smart YouTube Reader..."

    Require-Command "ffmpeg" "Install FFmpeg and make sure it is on PATH."
    Require-Command "ollama" "Install Ollama from https://ollama.com/download"
    Require-Command "python" "Install Python 3.11+ and make sure it is on PATH."
    Require-Command "node" "Install Node.js 20+ and make sure it is on PATH."
    Require-Command "npm" "Install npm with Node.js."
    # Prefer npm.cmd on Windows; npm.ps1 can misparse scriptblock invocations.
    $NpmCommand = Get-Command "npm.cmd" -ErrorAction SilentlyContinue
    if (-not $NpmCommand) {
        $NpmCommand = Get-Command "npm"
    }
    $NpmExe = $NpmCommand.Source

    $Model = if ($env:SMART_READER_MODEL) { $env:SMART_READER_MODEL } else { "gemma4:12b" }
    ollama list *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Ollama is not running. Start Ollama, then re-run .\start.ps1"
    }
    $InstalledModels = ollama list | Select-Object -Skip 1 | ForEach-Object { ($_ -split "\s+")[0] }
    if ($InstalledModels -notcontains $Model) {
        Write-Host "Pulling local model $Model with Ollama..."
        ollama pull $Model
        if ($LASTEXITCODE -ne 0) {
            throw "Could not pull $Model"
        }
    }
    $env:SMART_READER_MODEL = $Model

    $BindHost = "127.0.0.1"
    if ($Share -or $env:SYR_SHARE -eq "1") {
        $BindHost = "0.0.0.0"
        Write-Host "SYR_SHARE enabled: binding to all interfaces."
    }

    $BackendDir = Join-Path $Root "backend"
    $VenvDir = Join-Path $BackendDir ".venv"
    $PythonExe = Join-Path $VenvDir "Scripts\python.exe"
    if (-not (Test-Path $VenvDir)) {
        Write-Host "Creating backend virtualenv..."
        python -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) { throw "could not create backend virtualenv" }
        & $PythonExe -m pip install -r (Join-Path $BackendDir "requirements.txt")
        if ($LASTEXITCODE -ne 0) { throw "backend dependency install failed" }
    }

    $FrontendDir = Join-Path $Root "frontend"
    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        Write-Host "Installing frontend dependencies..."
        if (Test-Path (Join-Path $FrontendDir "package-lock.json")) {
            Run-InDirectory $FrontendDir { & $NpmExe ci }
        } else {
            Run-InDirectory $FrontendDir { & $NpmExe install }
        }
        if ($LASTEXITCODE -ne 0) { throw "frontend dependency install failed" }
    }

    Write-Host "Starting backend on http://localhost:8001"
    $script:BackendProcess = Start-Process `
        -FilePath $PythonExe `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--reload", "--host", $BindHost, "--port", "8001") `
        -WorkingDirectory $BackendDir `
        -PassThru

    Write-Host "Starting frontend on http://localhost:3001"
    $script:FrontendProcess = Start-Process `
        -FilePath $NpmExe `
        -ArgumentList @("run", "dev", "--", "-H", $BindHost, "--port", "3001") `
        -WorkingDirectory $FrontendDir `
        -PassThru

    Write-Host "App running: http://localhost:3001"
    Write-Host "Press Ctrl+C to stop."
    while ($true) {
        Start-Sleep -Seconds 2
        if ($script:BackendProcess.HasExited -or $script:FrontendProcess.HasExited) {
            throw "A server process exited."
        }
    }
} finally {
    Stop-AppProcesses
}
