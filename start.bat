@echo off
setlocal

set "ROOT=%~dp0"
set "POWERSHELL_EXE="

where pwsh.exe >nul 2>nul
if not errorlevel 1 (
    set "POWERSHELL_EXE=pwsh.exe"
) else (
    where powershell.exe >nul 2>nul
    if not errorlevel 1 (
        set "POWERSHELL_EXE=powershell.exe"
    )
)

if "%POWERSHELL_EXE%"=="" (
    echo PowerShell is not installed or is not on PATH.
    exit /b 1
)

"%POWERSHELL_EXE%" -NoProfile -ExecutionPolicy Bypass -File "%ROOT%start.ps1" %*
exit /b %ERRORLEVEL%
