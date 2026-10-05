$ErrorActionPreference = 'Stop'
$ProjectDir = $PSScriptRoot
$VenvPython = Join-Path $ProjectDir '.venv\Scripts\python.exe'
$NgrokExe = Join-Path $ProjectDir 'ngrok-bin\ngrok.exe'
$AppPort = 8000
$LocalUrl = "http://localhost:$AppPort"

Write-Host 'Astro Agent / KaalDrishti launcher' -ForegroundColor Cyan

if (-not (Test-Path $VenvPython)) {
    Write-Error "Python 3.11 venv is missing. Create it with: py -3.11 -m venv `"$ProjectDir\.venv`"; then install requirements.txt and requirements-dev.txt."
    exit 1
}

$PythonVersion = & $VenvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($PythonVersion -ne '3.11') {
    Write-Error "Expected Python 3.11, but this venv uses Python $PythonVersion. Recreate it with py -3.11."
    exit 1
}

try {
    & $VenvPython -c 'import fastapi, swisseph, uvicorn'
    if ($LASTEXITCODE -ne 0) { throw 'Required runtime packages are missing.' }
} catch {
    Write-Error "Runtime dependencies are incomplete. Run: `"$VenvPython`" -m pip install -r `"$ProjectDir\requirements.txt`""
    exit 1
}

$env:PYTHONPATH = $ProjectDir
$Server = Start-Process -FilePath $VenvPython `
    -ArgumentList @('-m', 'uvicorn', 'main:app', '--host', '0.0.0.0', '--port', "$AppPort", '--reload') `
    -WorkingDirectory $ProjectDir -PassThru

Start-Sleep -Seconds 5
if ($Server.HasExited) {
    Write-Error 'The API server exited during startup. Check the server process output and application logs.'
    exit 1
}

if (Test-Path $NgrokExe) {
    Start-Process -FilePath $NgrokExe -ArgumentList @('http', "$AppPort") -WorkingDirectory (Split-Path $NgrokExe)
}

Start-Process $LocalUrl
Write-Host "Server is running at $LocalUrl using Python 3.11." -ForegroundColor Green
Write-Host 'Stop the API server from its process window when finished.'
