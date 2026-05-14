@echo off
title 🔮 Astro Agent - Launcher
color 0A
cls

echo ============================================================
echo         🔮  ASTRO AGENT / KAALDRISHTI  LAUNCHER
echo ============================================================
echo.

:: ── CONFIG ──────────────────────────────────────────────────
set PROJECT_DIR=d:\Downloads\Projects\Astro Agent
set VENV_PYTHON=%PROJECT_DIR%\venv\Scripts\python.exe
set VENV_ACTIVATE=%PROJECT_DIR%\venv\Scripts\activate.bat
set NGROK_EXE=%PROJECT_DIR%\ngrok-bin\ngrok.exe
set APP_PORT=8000
set LOCAL_URL=http://localhost:%APP_PORT%
:: ─────────────────────────────────────────────────────────────

:: ── STEP 1: Verify venv exists ───────────────────────────────
echo [1/4]  Checking virtual environment...
if not exist "%VENV_PYTHON%" (
    echo  [ERROR] venv not found at: %VENV_PYTHON%
    echo  Run:  python -m venv "%PROJECT_DIR%\venv"
    echo  Then: pip install -r requirements.txt
    pause
    exit /b 1
)
echo  [OK]   venv found.
echo.

:: ── STEP 2: Set PYTHONPATH ────────────────────────────────────
echo [2/4]  Setting PYTHONPATH...
set PYTHONPATH=%PROJECT_DIR%
echo  [OK]   PYTHONPATH = %PYTHONPATH%
echo.

:: ── STEP 3: Launch FastAPI server in a new window ────────────
echo [3/4]  Starting FastAPI server (port %APP_PORT%)...
start "🔮 Astro Agent - FastAPI Server" /D "%PROJECT_DIR%" cmd /k "call "%VENV_ACTIVATE%" && set PYTHONPATH=%PROJECT_DIR% && python main.py"
echo  [OK]   Server window launched.
echo.

:: ── Wait for server to boot (5 seconds grace period) ─────────
echo  Waiting 5 seconds for server to boot...
timeout /t 5 /nobreak >nul
echo.

:: ── STEP 4: Launch ngrok tunnel in a new window ──────────────
echo [4/4]  Starting ngrok tunnel...
if not exist "%NGROK_EXE%" (
    echo  [WARN] ngrok not found at: %NGROK_EXE%
    echo  Skipping ngrok. Use your local IP: http://192.168.0.109:%APP_PORT%
) else (
    REM If you have a reserved domain, you can change the command to: 
    REM ngrok http --domain YOUR_DOMAIN %APP_PORT%
    start "🌐 Astro Agent - ngrok Tunnel" /D "%PROJECT_DIR%\ngrok-bin" cmd /k "ngrok http %APP_PORT%"
    echo  [OK]   ngrok window launched.
    echo        Check the ngrok window (or wait for the server console) for your public URL.
)
echo.

:: ── Open browser ─────────────────────────────────────────────
echo  Opening browser at %LOCAL_URL% ...
timeout /t 2 /nobreak >nul
start "" "%LOCAL_URL%"
echo.

:: ── Done ─────────────────────────────────────────────────────
echo ============================================================
echo   ✅  All systems launched! 
echo.
echo   📡  Local :  %LOCAL_URL%
echo   🌐  Ngrok :  Check the ngrok window for the public URL
echo.
echo   To STOP everything: close the two terminal windows,
echo   or press Ctrl+C inside each one.
echo ============================================================
echo.
pause
