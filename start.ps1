param(
    [switch]$Share,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Require-Command($Name, $InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Error "$Name is not installed. $InstallHint"
    }
}

function Stop-ProcessTree($Process) {
    if (-not $Process -or $Process.HasExited) {
        return
    }

    $Children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $($Process.Id)" -ErrorAction SilentlyContinue
    foreach ($Child in $Children) {
        $ChildProcess = Get-Process -Id $Child.ProcessId -ErrorAction SilentlyContinue
        if ($ChildProcess) {
            Stop-ProcessTree $ChildProcess
        }
    }

    Stop-Process -Id $Process.Id -Force -ErrorAction SilentlyContinue
}

function Stop-AppProcesses {
    Stop-ProcessTree $script:FrontendProcess
    Stop-ProcessTree $script:BackendProcess
}

function Run-InDirectory($Directory, $Command) {
    Push-Location $Directory
    try {
        & $Command
    } finally {
        Pop-Location
    }
}

function Wait-ForTcpPort($HostName, $Port, $TimeoutSeconds) {
    $Deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $Deadline) {
        if (($script:BackendProcess -and $script:BackendProcess.HasExited) -or ($script:FrontendProcess -and $script:FrontendProcess.HasExited)) {
            return $false
        }
        $Client = $null
        try {
            $Client = New-Object System.Net.Sockets.TcpClient
            $Connection = $Client.BeginConnect($HostName, $Port, $null, $null)
            if ($Connection.AsyncWaitHandle.WaitOne(1000)) {
                $Client.EndConnect($Connection)
                return $true
            }
        } catch {
        } finally {
            if ($Client) {
                $Client.Close()
            }
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Resolve-BrowserCandidate($Candidate) {
    foreach ($Path in $Candidate.Paths) {
        if (-not $Path) {
            continue
        }
        if (Test-Path $Path) {
            return @{
                Name = $Candidate.Name
                Path = $Path
                Args = $Candidate.Args
            }
        }
        $Command = Get-Command $Path -ErrorAction SilentlyContinue
        if ($Command) {
            return @{
                Name = $Candidate.Name
                Path = $Command.Source
                Args = $Candidate.Args
            }
        }
    }
    return $null
}

function Join-OptionalPath($Base, $Child) {
    if ($Base) {
        return Join-Path $Base $Child
    }
    return $null
}

function Get-TailscaleIp {
    $TailscaleCommand = Get-Command "tailscale" -ErrorAction SilentlyContinue
    if (-not $TailscaleCommand) {
        return $null
    }

    try {
        $Ip = & $TailscaleCommand.Source ip -4 2>$null | Select-Object -First 1
        if ($Ip -and $Ip.Trim().StartsWith("100.")) {
            return $Ip.Trim()
        }
    } catch {
        return $null
    }

    return $null
}

function Open-IsolatedBrowser($Url) {
    $Candidates = @(
        @{
            Name = "Google Chrome Guest"
            Paths = @(
                "chrome.exe",
                (Join-OptionalPath $env:ProgramFiles "Google\Chrome\Application\chrome.exe"),
                (Join-OptionalPath ${env:ProgramFiles(x86)} "Google\Chrome\Application\chrome.exe"),
                (Join-OptionalPath $env:LocalAppData "Google\Chrome\Application\chrome.exe")
            )
            Args = @("--guest", "--new-window")
        },
        @{
            Name = "Microsoft Edge InPrivate"
            Paths = @(
                "msedge.exe",
                (Join-OptionalPath $env:ProgramFiles "Microsoft\Edge\Application\msedge.exe"),
                (Join-OptionalPath ${env:ProgramFiles(x86)} "Microsoft\Edge\Application\msedge.exe"),
                (Join-OptionalPath $env:LocalAppData "Microsoft\Edge\Application\msedge.exe")
            )
            Args = @("--inprivate", "--new-window")
        },
        @{
            Name = "Brave Incognito"
            Paths = @(
                "brave.exe",
                (Join-OptionalPath $env:ProgramFiles "BraveSoftware\Brave-Browser\Application\brave.exe"),
                (Join-OptionalPath ${env:ProgramFiles(x86)} "BraveSoftware\Brave-Browser\Application\brave.exe"),
                (Join-OptionalPath $env:LocalAppData "BraveSoftware\Brave-Browser\Application\brave.exe")
            )
            Args = @("--incognito", "--new-window")
        },
        @{
            Name = "Firefox Private"
            Paths = @(
                "firefox.exe",
                (Join-OptionalPath $env:ProgramFiles "Mozilla Firefox\firefox.exe"),
                (Join-OptionalPath ${env:ProgramFiles(x86)} "Mozilla Firefox\firefox.exe")
            )
            Args = @("--private-window")
        }
    )

    foreach ($Candidate in $Candidates) {
        $Resolved = Resolve-BrowserCandidate $Candidate
        if ($Resolved) {
            Start-Process -FilePath $Resolved.Path -ArgumentList ($Resolved.Args + @($Url)) | Out-Null
            Write-Host "Opened app in $($Resolved.Name): $Url"
            return
        }
    }

    Start-Process $Url | Out-Null
    Write-Host "Opened app in the default browser: $Url"
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

    $ShareEnabled = $Share -or $env:SYR_SHARE -eq "1"
    $BindHost = "127.0.0.1"
    if ($ShareEnabled) {
        $BindHost = "0.0.0.0"
        Write-Host "SYR_SHARE enabled: binding to all interfaces."
    }
    $env:SYR_SHARE = if ($ShareEnabled) { "1" } else { "0" }
    $env:SYR_BIND_HOST = $BindHost
    $env:FRONTEND_PORT = "3001"

    $AppUrl = "http://localhost:3001"
    if ($ShareEnabled) {
        $TailscaleIp = Get-TailscaleIp
        if ($TailscaleIp) {
            $AppUrl = "http://${TailscaleIp}:3001"
        }
    }
    $LogDir = Join-Path ([System.IO.Path]::GetTempPath()) "smart-youtube-reader"
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
    $BackendOutLog = Join-Path $LogDir "backend.out.log"
    $BackendErrLog = Join-Path $LogDir "backend.err.log"
    $FrontendOutLog = Join-Path $LogDir "frontend.out.log"
    $FrontendErrLog = Join-Path $LogDir "frontend.err.log"

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
        -RedirectStandardOutput $BackendOutLog `
        -RedirectStandardError $BackendErrLog `
        -WindowStyle Hidden `
        -PassThru

    Write-Host "Starting frontend on http://localhost:3001"
    $FrontendCommand = '"' + $NpmExe + '" run dev -- -H ' + $BindHost + ' --port 3001'
    $script:FrontendProcess = Start-Process `
        -FilePath $env:ComSpec `
        -ArgumentList @("/d", "/c", $FrontendCommand) `
        -WorkingDirectory $FrontendDir `
        -RedirectStandardOutput $FrontendOutLog `
        -RedirectStandardError $FrontendErrLog `
        -WindowStyle Hidden `
        -PassThru

    Write-Host "Server logs: $LogDir"
    Write-Host "Waiting for frontend..."
    if (Wait-ForTcpPort "127.0.0.1" 3001 90) {
        if (-not $NoBrowser) {
            Open-IsolatedBrowser $AppUrl
        }
    } else {
        Write-Warning "Frontend did not become ready yet. Check logs in $LogDir"
    }

    Write-Host "App running: $AppUrl"
    Write-Host "Press Ctrl+C to stop."
    while ($true) {
        Start-Sleep -Seconds 2
        if ($script:BackendProcess.HasExited -or $script:FrontendProcess.HasExited) {
            throw "A server process exited. Check logs in $LogDir"
        }
    }
} finally {
    Stop-AppProcesses
}
