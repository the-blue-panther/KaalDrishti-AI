# KaalDrishti AI

KaalDrishti is a Vedic astrology application with a deterministic chart engine, a FastAPI service, and a browser interface. It calculates chart positions and timing data, then provides conversational interpretations with optional graph retrieval.

## Features

- Lahiri sidereal planetary positions, whole-sign houses, divisional charts, and panchang details.
- Vimshottari and additional dasha timelines, plus transit snapshots and ingress calculations.
- Browser interface and profile-scoped local storage through the FastAPI service.
- Optional Gemini or Ollama inference and optional Neo4j-backed retrieval.

Astrological interpretation rules and several chart components remain experimental or heuristic. The application does not provide validated personal probabilities. See [`docs/astro_engine_audit.md`](docs/astro_engine_audit.md) for verification scope and known limitations.

## Quick start

Python 3.11 is recommended.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `ASTRO_AGENT_SECRET_KEY` in `.env` to a long random value. Set `GEMINI_API_KEY` to enable Gemini, and the `NEO4J_*` settings if using Neo4j. Ollama can be used locally; `OLLAMA_MODEL` defaults to `gemma:2b`.

Start the service from the project directory:

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000> in a browser. User profiles and the SQLite database are stored locally and excluded from Git.

## Repository layout

| Path | Purpose |
| --- | --- |
| `chart_engine/` | Astronomy, chart, dasha, and transit calculations |
| `feature_extraction/` | Structured chart feature extraction |
| `intelligence_layer/` | Domain scoring and divisional chart analysis |
| `rag_bridge/` | Optional Neo4j retrieval |
| `agent_inference/` | Conversational inference integrations |
| `frontend/` | Browser interface |
| `docs/` | Engine audits and project notes |

## Configuration and data

Copy `.env.example` to `.env` and configure only the services you use. Never commit `.env`, API keys, Neo4j exports, user profile data, local databases, or generated model artifacts. The repository `.gitignore` excludes these local files and generated outputs.

The optional Neo4j JSON fallback is configured with `NEO4J_JSON_BACKUP_PATH`. Without it, the application uses Neo4j when configured and otherwise reports retrieval as unavailable.
