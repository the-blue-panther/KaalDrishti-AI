# ============================================================
#   🔮 ASTRO AGENT / KAALDRISHTI — One-Click Launcher
#   PowerShell Version — Run as: .\START_ASTRO_AGENT.ps1
# ============================================================

$Host.UI.RawUI.WindowTitle = "🔮 Astro Agent Launcher"

function Write-Banner {
    Write-Host ""
    Write-Host "  ============================================================" -ForegroundColor Cyan
    Write-Host "          🔮  ASTRO AGENT / KAALDRISHTI  LAUNCHER" -ForegroundColor Yellow
    Write-Host "  ============================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step($num, $total, $msg) {
    Write-Host "  [$num/$total]  $msg" -ForegroundColor White
}

function Write-Ok($msg) {
    Write-Host "         ✅  $msg" -ForegroundColor Green
}

function Write-Warn($msg) {
    Write-Host "         ⚠️   $msg" -ForegroundColor Yellow
}

function Write-Err($msg) {
    Write-Host "         ❌  $msg" -ForegroundColor Red
}

# ── CONFIG ────────────────────────────────────────────────────
$ProjectDir  = "d:\Downloads\Projects\Astro Agent"
$VenvPython  = "$ProjectDir\venv\Scripts\python.exe"
$VenvActivate= "$ProjectDir\venv\Scripts\Activate.ps1"
$NgrokExe    = "$ProjectDir\ngrok-bin\ngrok.exe"
$AppPort     = 8000
$LocalUrl    = "http://localhost:$AppPort"
# ─────────────────────────────────────────────────────────────

Write-Banner

# ── STEP 1: Verify venv ───────────────────────────────────────
Write-Step 1 4 "Checking virtual environment..."
if (-not (Test-Path $VenvPython)) {
    Write-Err "venv not found at: $VenvPython"
    Write-Warn "Run the following to fix it:"
    Write-Host ""
    Write-Host "    python -m venv `"$ProjectDir\venv`"" -ForegroundColor Gray
    Write-Host "    pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Ok "venv found."
Write-Host ""

# ── STEP 2: Set PYTHONPATH ────────────────────────────────────
Write-Step 2 4 "Setting PYTHONPATH..."
$env:PYTHONPATH = $ProjectDir
Write-Ok "PYTHONPATH = $env:PYTHONPATH"
Write-Host ""

# ── STEP 3: Launch FastAPI server ─────────────────────────────
Write-Step 3 4 "Starting FastAPI server on port $AppPort ..."

$serverArgs = @(
    "-NoExit",
    "-Command",
    "& { `$env:PYTHONPATH='$ProjectDir'; & '$VenvActivate'; python '$ProjectDir\main.py' }"
)

Start-Process powershell `
    -ArgumentList $serverArgs `
    -WorkingDirectory $ProjectDir `
    -WindowStyle Normal

Write-Ok "Server window launched."
Write-Host ""

# ── Wait for server boot ──────────────────────────────────────
Write-Host "         ⏳  Waiting 5 seconds for server to initialise..." -ForegroundColor DarkGray
Start-Sleep -Seconds 5
Write-Host ""

# ── STEP 4: Launch ngrok ──────────────────────────────────────
Write-Step 4 4 "Starting ngrok tunnel..."
if (-not (Test-Path $NgrokExe)) {
    Write-Warn "ngrok.exe not found at: $NgrokExe — skipping tunnel."
} else {
    $ngrokArgs = @(
        "-NoExit",
        "-Command",
        "& '$NgrokExe' http $AppPort"
    )
    Start-Process powershell `
        -ArgumentList $ngrokArgs `
        -WorkingDirectory "$ProjectDir\ngrok-bin" `
        -WindowStyle Normal
    Write-Ok "ngrok tunnel window launched."
}
Write-Host ""

# ── Open browser ──────────────────────────────────────────────
Write-Host "         🌐  Opening browser at $LocalUrl ..." -ForegroundColor Magenta
Start-Sleep -Seconds 2
Start-Process $LocalUrl
Write-Host ""

# ── Summary ───────────────────────────────────────────────────
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host "    ✅  All systems are GO!" -ForegroundColor Green
Write-Host ""
Write-Host "    📡  Local  :  $LocalUrl" -ForegroundColor White
Write-Host "    🌐  Ngrok  :  Check the ngrok window for the public URL" -ForegroundColor White
Write-Host ""
Write-Host "    To STOP: press Ctrl+C in each launched terminal window." -ForegroundColor DarkGray
Write-Host "  ============================================================" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to close this launcher"
