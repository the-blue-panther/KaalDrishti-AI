@echo off
setlocal
title Astro Agent / KaalDrishti

cd /d "%~dp0"
set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo [ERROR] Python 3.11 virtual environment not found.
    echo Create it with: py -3.11 -m venv .venv
    echo Then install:   .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

"%VENV_PYTHON%" -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 11) else 1)"
if errorlevel 1 (
    echo [ERROR] The project venv must use Python 3.11.
    "%VENV_PYTHON%" --version
    pause
    exit /b 1
)

echo Starting Astro Agent with Python 3.11...
"%VENV_PYTHON%" -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
