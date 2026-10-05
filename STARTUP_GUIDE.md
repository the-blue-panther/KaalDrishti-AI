# Local setup

## Requirements

- Windows and Python 3.11
- Optional: Gemini API access, Neo4j credentials, or a local Ollama installation

## Install

From the project directory, create a virtual environment and install dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `ASTRO_AGENT_SECRET_KEY` in `.env` to a long random value. Configure `GEMINI_API_KEY` or the `NEO4J_*` variables only if you use those services.

## Run

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. Local profile and database files stay in the project directory and are excluded from Git.

The Windows launcher scripts expect a Python 3.11 environment named `venv`. If you use the `.venv` name above, run the Uvicorn command directly.
