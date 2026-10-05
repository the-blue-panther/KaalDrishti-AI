import json
import os
import sqlite3
import jwt
import datetime
import secrets
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
import logging

# Basic logging config
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Ensure Lahiri sidereal gets globally locked on server boot
from chart_engine.engine import AstroEngine
from chart_engine.chart_state import ChartState


from dotenv import load_dotenv
load_dotenv(override=False)

from feature_extraction.extractor import FeatureExtractor
from intelligence_layer.ase import AstrologicalScoringEngine
from intelligence_layer.dis import DivisionalIntelligenceSystem
from ml.reliability import append_reliability_disclosure, references_for_response
from rag_bridge.graph_query_builder import AVAILABLE_DOMAINS, RAGCompiler
from agent_inference.core import AstroAgentCore

# --- AUTHENTICATION CONFIG ---
SECRET_KEY = os.getenv("ASTRO_AGENT_SECRET_KEY") or secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200 # 30 days for testing

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

# --- USER DATABASE INITIALIZATION ---
DB_PATH = "users.db"
db = sqlite3.connect(DB_PATH, check_same_thread=False)
db.row_factory = sqlite3.Row
db.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password_hash TEXT, preferred_language TEXT DEFAULT 'English')")
# Handle existing tables without the column
try:
    db.execute("ALTER TABLE users ADD COLUMN preferred_language TEXT DEFAULT 'English'")
except sqlite3.OperationalError:
    pass # Column already exists

# --- CHAT SESSIONS TABLE ---
db.execute("""
CREATE TABLE IF NOT EXISTS chat_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    profile_name TEXT NOT NULL,
    session_title TEXT DEFAULT 'New Chat',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
)
""")
db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_profile ON chat_sessions(user_id, profile_name)")

# --- PROFILE MEMORY TABLE ---
db.execute("""
CREATE TABLE IF NOT EXISTS profile_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    profile_name TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    source TEXT DEFAULT 'auto',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
db.execute("CREATE INDEX IF NOT EXISTS idx_memory_user_profile ON profile_memory(user_id, profile_name)")
db.commit()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if user is None:
        raise credentials_exception
    return user

app = FastAPI(title="Astro Agent RAG API", version="1.0.0")

# --- MIDDLEWARE & ERRORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Force print to console for visibility
    print(f"\n[âŒ VALIDATION ERROR] {errors}\n")
    logging.error(f"Validation Error: {errors}")
    return JSONResponse(
        status_code=400,
        content={"detail": "Validation Error", "errors": errors},
    )

# Singleton initializations to save memory between requests
core_engine = AstroEngine()
rag_compiler = RAGCompiler()
agent_core = AstroAgentCore()

# --- SCHEMAS ---
class UserCreate(BaseModel):
    username: str
    password: str

class BirthData(BaseModel):
    local_time: str # Format: "YYYY-MM-DD HH:MM:SS"
    timezone: str   # Format: "Asia/Kolkata"
    latitude: float
    longitude: float
    location_name: str = ""
    gender: str = "Male" # Added for v3.0 context

class ChatQuery(BaseModel):
    seeker_name: str = "Seeker"
    birth_data: BirthData
    question: str
    session_id: Optional[int] = None
    selected_domains: Optional[list[str]] = None

class ChartImageRequest(BaseModel):
    chart_name: str
    varga_matrix: dict[str, str]

class SessionCreate(BaseModel):
    profile_name: str
    session_title: str = "New Chat"

class SessionUpdate(BaseModel):
    session_title: str

from chart_engine.chart_drawer import ChartDrawer

CHART_ENGINE_PAYLOAD_KEYS = [
    "metadata",
    "planetary_positions",
    "divisional_charts",
    "dasha_timeline",
    "panchang",
    "current_transits",
    "shadbala",
    "shadbala_summary",
    "ashtakavarga",
    "graha_drishti",
    "combustion",
    "jaimini_system",
    "kp_system",
    "vargottama",
    "special_features",
    "predictive_tech",
    "navatara_chakra",
]

REQUIRED_CHART_MATRIX_KEYS = CHART_ENGINE_PAYLOAD_KEYS + [
    "semantic_features",
    "quantitative_intelligence",
    "prediction_calibration",
    "empirical_predictions",
]

def build_chart_matrix_payload(chart: ChartState, features: dict, intelligence_scores: dict, prediction_calibration: dict | None = None) -> dict:

    """Build the API/cache projection from the canonical ChartState."""
    serialized_chart = chart.to_chart_payload()
    payload = {key: serialized_chart.get(key, {}) for key in CHART_ENGINE_PAYLOAD_KEYS}
    payload["semantic_features"] = features
    payload["quantitative_intelligence"] = intelligence_scores
    calibration = prediction_calibration or {"status": "calibration_unavailable"}
    payload["prediction_calibration"] = calibration
    payload["empirical_predictions"] = calibration  # Deprecated API compatibility alias.
    return payload


def build_prediction_calibration(chart: ChartState, features_obj) -> dict:
    """Return the calibration gate, never a direct chart-to-life-event estimate.

    Kept under the legacy API field/function name for compatibility. Historical
    event-age experiments remain offline research artifacts; production ML is
    reserved for calibrating astrology-generated candidate windows.
    """
    return {
        "status": "calibration_unavailable",
        "model_role": "candidate_window_reliability_and_timing_calibration",
        "candidate_windows": [],
        "message": (
            "No domain prediction-window engine and resolved prediction-case "
            "calibrator are configured. Direct chart-to-event models are "
            "research-only and are not served as astrological predictions."
        ),
    }


# Serve Frontend DOM
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "astro-agent"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("frontend/favicon.png")

@app.get("/")
async def root():
    return FileResponse(
        "frontend/index.html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache"
        }
    )

# --- AUTH ENDPOINTS ---

@app.get("/api/existing_profiles")
async def list_existing_profiles(q: str = "", current_user = Depends(get_current_user)):
    user_id = current_user["username"]
    profiles_dir = f"users/{user_id}/profiles"
    if not os.path.exists(profiles_dir): return []

    matches = []
    for d in os.listdir(profiles_dir):
        if q.lower() in d.lower():
            matches.append(d)
    return matches

@app.post("/api/signup")
async def signup(user: UserCreate):
    # Sanitize username (Windows doesn't allow trailing spaces in folder names)
    clean_username = user.username.strip()

    db.row_factory = sqlite3.Row
    cursor = db.execute("SELECT id FROM users WHERE username = ?", (clean_username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pass = pwd_context.hash(user.password)
    db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (clean_username, hashed_pass))
    db.commit()

    # Create user base folder
    user_folder = f"users/{clean_username}/profiles"
    os.makedirs(user_folder, exist_ok=True)

    return {"status": "success", "message": "Account created successfully"}

@app.post("/api/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Sanitize login username
    clean_username = form_data.username.strip()

    user_row = db.execute("SELECT * FROM users WHERE username = ?", (clean_username,)).fetchone()
    if not user_row or not pwd_context.verify(form_data.password, user_row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": clean_username})
    return {"access_token": access_token, "token_type": "bearer", "username": user_row["username"], "preferred_language": user_row["preferred_language"]}

@app.get("/api/settings")
async def get_settings(current_user = Depends(get_current_user)):
    return {"preferred_language": current_user["preferred_language"]}

@app.post("/api/settings")
async def update_settings(settings: dict, current_user = Depends(get_current_user)):
    new_lang = settings.get("preferred_language", "English")
    db.execute("UPDATE users SET preferred_language = ? WHERE username = ?", (new_lang, current_user["username"]))
    db.commit()
    return {"status": "success", "message": "Settings updated successfully"}

@app.get("/api/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return {"username": current_user["username"]}

# --- CHAT SESSION ENDPOINTS ---

@app.get("/api/sessions")
async def get_sessions(profile_name: str = None, current_user = Depends(get_current_user)):
    user_id = current_user["username"]
    if not profile_name:
        return []

    sessions = db.execute(
        "SELECT id, user_id, profile_name, session_title, created_at, updated_at, is_active FROM chat_sessions WHERE user_id = ? AND profile_name = ? ORDER BY updated_at DESC",
        (user_id, profile_name)
    ).fetchall()
    return [dict(s) for s in sessions]

@app.post("/api/sessions")
async def create_session(session: SessionCreate, current_user = Depends(get_current_user)):
    user_id = current_user["username"]

    # Sanitize profile name
    profile_name = session.profile_name.replace(" ", "_")

    # Check if profile exists
    profile_folder = f"users/{user_id}/profiles/{profile_name}"
    if not os.path.exists(profile_folder):
        raise HTTPException(status_code=404, detail="Profile not found")

    # Create session record
    cursor = db.execute(
        "INSERT INTO chat_sessions (user_id, profile_name, session_title) VALUES (?, ?, ?)",
        (user_id, profile_name, session.session_title)
    )
    db.commit()
    session_id = cursor.lastrowid

    # Create session history file
    sessions_folder = f"{profile_folder}/sessions"
    os.makedirs(sessions_folder, exist_ok=True)
    session_path = f"{sessions_folder}/session_{session_id}.json"
    with open(session_path, "w", encoding="utf-8") as f:
        json.dump([], f)

    return {
        "id": session_id,
        "user_id": user_id,
        "profile_name": profile_name,
        "session_title": session.session_title,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "updated_at": datetime.datetime.utcnow().isoformat(),
        "is_active": 1
    }

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: int, current_user = Depends(get_current_user)):
    user_id = current_user["username"]

    # Get session details
    session = db.execute(
        "SELECT user_id, profile_name FROM chat_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id)
    ).fetchone()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete session record
    db.execute("DELETE FROM chat_sessions WHERE id = ? AND user_id = ?", (session_id, user_id))
    db.commit()

    # Delete session history file
    session_path = f"users/{user_id}/profiles/{session['profile_name']}/sessions/session_{session_id}.json"
    if os.path.exists(session_path):
        os.remove(session_path)

    return {"status": "success", "message": "Session deleted successfully"}

@app.put("/api/sessions/{session_id}")
async def update_session(session_id: int, session: SessionUpdate, current_user = Depends(get_current_user)):
    user_id = current_user["username"]

    # Check if session exists and belongs to user
    existing = db.execute(
        "SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id)
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update session title
    db.execute(
        "UPDATE chat_sessions SET session_title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (session.session_title, session_id, user_id)
    )
    db.commit()

    return {"status": "success", "message": "Session updated successfully"}

@app.post("/api/sessions/{session_id}/generate_title")
async def generate_session_title(session_id: int, current_user = Depends(get_current_user)):
    """
    Generate a concise title for a session based on the first user message.
    Uses the Universal Web LLM Bridge for title generation.
    """
    user_id = current_user["username"]

    # Get session details
    session = db.execute(
        "SELECT user_id, profile_name, session_title FROM chat_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id)
    ).fetchone()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # If title is not "New Chat", it already has a title
    if session["session_title"] != "New Chat":
        return {"status": "success", "title": session["session_title"], "message": "Title already exists"}

    # Get session history
    session_path = f"users/{user_id}/profiles/{session['profile_name']}/sessions/session_{session_id}.json"
    if not os.path.exists(session_path):
        raise HTTPException(status_code=404, detail="Session history not found")

    with open(session_path, "r", encoding="utf-8") as f:
        history = json.load(f)

    # Find the first user message
    first_user_msg = None
    for turn in history:
        if turn.get("role") == "user":
            first_user_msg = turn.get("content", "")
            break

    if not first_user_msg:
        return {"status": "error", "message": "No user messages found in this session"}

    # Generate title using the bridge
    try:
        import requests
        url = "http://localhost:8001/v1/chat/completions"
        prompt = f"""Generate a very short, concise title (max 5 words) for a chat session based on this first user message.
User message: "{first_user_msg[:500]}"

Return ONLY the title, nothing else. No quotes, no punctuation at the end. Keep it under 5 words."""

        payload = {
            "model": "gemini-web",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.5,
            "stream": False
        }

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        title = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        # Clean up the title: remove quotes, limit length
        title = title.strip('"\'')
        if len(title) > 60:
            title = title[:60] + "..."
        if not title:
            title = "Chat"

        # Update session title
        db.execute(
            "UPDATE chat_sessions SET session_title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (title, session_id, user_id)
        )
        db.commit()

        return {"status": "success", "title": title}
    except Exception as e:
        return {"status": "error", "message": f"Title generation failed: {str(e)}"}

@app.get("/api/sessions/{session_id}/history")
async def get_session_history(session_id: int, current_user = Depends(get_current_user)):
    user_id = current_user["username"]

    # Get session details
    session = db.execute(
        "SELECT user_id, profile_name FROM chat_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id)
    ).fetchone()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Read session history
    session_path = f"users/{user_id}/profiles/{session['profile_name']}/sessions/session_{session_id}.json"
    if not os.path.exists(session_path):
        return []

    with open(session_path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- PROFILE MEMORY ENDPOINTS ---

class MemoryItem(BaseModel):
    key: str
    value: str
    source: str = "auto"

@app.get("/api/profile_memory")
async def get_profile_memory(profile_name: str, current_user = Depends(get_current_user)):
    user_id = current_user["username"]
    if not profile_name:
        return []

    memories = db.execute(
        "SELECT id, user_id, profile_name, key, value, source, created_at, updated_at FROM profile_memory WHERE user_id = ? AND profile_name = ? ORDER BY created_at DESC",
        (user_id, profile_name.replace(" ", "_"))
    ).fetchall()
    return [dict(m) for m in memories]

@app.post("/api/profile_memory")
async def add_profile_memory(memory: MemoryItem, current_user = Depends(get_current_user)):
    user_id = current_user["username"]
    profile_name = memory.key.split("_")[0] if "_" in memory.key else "unknown"

    # Check if profile exists
    profile_folder = f"users/{user_id}/profiles/{profile_name}"
    if not os.path.exists(profile_folder):
        raise HTTPException(status_code=404, detail="Profile not found")

    cursor = db.execute(
        "INSERT INTO profile_memory (user_id, profile_name, key, value, source) VALUES (?, ?, ?, ?, ?)",
        (user_id, profile_name, memory.key, memory.value, memory.source)
    )
    db.commit()

    return {
        "id": cursor.lastrowid,
        "user_id": user_id,
        "profile_name": profile_name,
        "key": memory.key,
        "value": memory.value,
        "source": memory.source,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "updated_at": datetime.datetime.utcnow().isoformat()
    }

@app.delete("/api/profile_memory/{memory_id}")
async def delete_profile_memory(memory_id: int, current_user = Depends(get_current_user)):
    user_id = current_user["username"]

    # Check if memory exists and belongs to user
    memory = db.execute(
        "SELECT id FROM profile_memory WHERE id = ? AND user_id = ?",
        (memory_id, user_id)
    ).fetchone()
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")

    db.execute("DELETE FROM profile_memory WHERE id = ? AND user_id = ?", (memory_id, user_id))
    db.commit()

    return {"status": "success", "message": "Memory deleted successfully"}

@app.put("/api/profile_memory/{memory_id}")
async def update_profile_memory(memory_id: int, memory: MemoryItem, current_user = Depends(get_current_user)):
    user_id = current_user["username"]

    # Check if memory exists and belongs to user
    existing = db.execute(
        "SELECT id FROM profile_memory WHERE id = ? AND user_id = ?",
        (memory_id, user_id)
    ).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="Memory not found")

    db.execute(
        "UPDATE profile_memory SET key = ?, value = ?, source = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (memory.key, memory.value, memory.source, memory_id, user_id)
    )
    db.commit()

    return {"status": "success", "message": "Memory updated successfully"}

# --- PROTECTED DATA ENDPOINTS ---

@app.get("/api/profiles")
async def get_user_profiles(current_user = Depends(get_current_user)):
    user_id = current_user["username"]
    profiles_dir = f"users/{user_id}/profiles"
    profiles = []
    if os.path.exists(profiles_dir):
        for profile_name in os.listdir(profiles_dir):
            detail_path = f"{profiles_dir}/{profile_name}/birth_details.json"
            if os.path.exists(detail_path):
                with open(detail_path, "r", encoding="utf-8") as f:
                    profiles.append(json.load(f))
    return profiles

@app.post("/agent_chat")
async def agent_chat(query: ChatQuery, current_user = Depends(get_current_user)):
    user_id = current_user["username"]

    if query.question != "[INITIALIZATION]":
        if not query.selected_domains:
            raise HTTPException(status_code=422, detail="Select at least one question domain tag.")
        invalid_domains = set(query.selected_domains) - set(AVAILABLE_DOMAINS)
        if invalid_domains:
            raise HTTPException(status_code=422, detail="One or more question domain tags are not supported.")
        if "general" in query.selected_domains and len(set(query.selected_domains)) > 1:
            raise HTTPException(status_code=422, detail="General / Other cannot be combined with another domain tag.")

        # 1. Execute Consolidated Math Pipeline
    try:
        chart = core_engine.generate_chart(
            query.birth_data.local_time,
            query.birth_data.timezone,
            query.birth_data.latitude,
            query.birth_data.longitude,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine failure: {str(e)}")

    # 2. Semantic Feature Extraction
    features_obj = FeatureExtractor.generate_features(chart)

    features = features_obj.model_dump()


    # 3. Quantitative Intelligence Scoring
    base_career = AstrologicalScoringEngine.score_career(features_obj)
    intelligence_scores = DivisionalIntelligenceSystem.validate_career_d10(
        features_obj, base_career, chart
    )

    uncertainty = chart.metadata.uncertainty_score
    prediction_calibration = build_prediction_calibration(chart, features_obj)

    # 4. RAG Integration via GraphDB
    rag_payload = {}
    if query.question != "[INITIALIZATION]":
        rag_payload = rag_compiler.fetch_all_context(
            features,
            user_query=query.question,
            selected_domains=query.selected_domains,
        )

    # 5. Persistence & Profile Meta (Scoped to Profile Name)
        profile_name = query.seeker_name.replace(" ", "_")
    profile_folder = f"users/{user_id}/profiles/{profile_name}"
    os.makedirs(profile_folder, exist_ok=True)


    metadata = chart.to_chart_payload()["metadata"]
    metadata.update({
        "seeker_name": query.seeker_name,
        "local_time": query.birth_data.local_time,
        "timezone": query.birth_data.timezone,
        "location": query.birth_data.location_name,
        "lat": query.birth_data.latitude,
        "lon": query.birth_data.longitude,
        "gender": query.birth_data.gender
    })

    with open(f"{profile_folder}/birth_details.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)


    # Cache matrix for re-hydration (includes every chart engine feature)
    matrix_payload = build_chart_matrix_payload(chart, features, intelligence_scores, prediction_calibration)
    with open(f"{profile_folder}/chart_matrix.json", "w", encoding="utf-8") as f:
        json.dump(matrix_payload, f, indent=4)

    # 6. Load Global Profile Memory
    global_memory = []
    memory_rows = db.execute(
        "SELECT key, value, source FROM profile_memory WHERE user_id = ? AND profile_name = ? ORDER BY created_at DESC",
        (user_id, profile_name)
    ).fetchall()
    for row in memory_rows:
        global_memory.append({"key": row["key"], "value": row["value"], "source": row["source"]})

    # 7. Execute Agent Inference
    # Determine which history to use: session-specific or legacy profile history
    chat_history = []
    history_file = None

    if query.session_id:
        # Use session-specific history
        session = db.execute(
            "SELECT profile_name FROM chat_sessions WHERE id = ? AND user_id = ?",
            (query.session_id, user_id)
        ).fetchone()
        if session:
            session_path = f"{profile_folder}/sessions/session_{query.session_id}.json"
            if os.path.exists(session_path):
                try:
                    with open(session_path, "r", encoding="utf-8") as f:
                        chat_history = json.load(f)
                except: pass
            # Keep only last 5 messages for context
            chat_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
    else:
        # Legacy: use profile-level history
        history_file = f"{profile_folder}/chat_history.json"
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    chat_history = json.load(f)
            except: pass

    if query.question == "[INITIALIZATION]":
        ai_response = f"Profile for {query.seeker_name} created successfully. What would you like to know about the chart?"
    else:
        ai_response = agent_core.generate_response(
            user_query=query.question,
            chart=chart,
            features=features,
            quantitative_scores=intelligence_scores,
            neo4j_context=rag_payload,
            history=chat_history,
            gender=query.birth_data.gender,
            preferred_language=current_user["preferred_language"],
            global_memory=global_memory,
            prediction_calibration=prediction_calibration,
        )

    # 8. Extract and Store New Memories from the conversation
    ai_response, reliability_references = references_for_response(ai_response)
    ai_response = append_reliability_disclosure(ai_response, reliability_references)
    try:
        memory_extraction = agent_core.extract_memories(
            user_query=query.question,
            assistant_response=ai_response,
            existing_memory=global_memory
        )
        if memory_extraction and isinstance(memory_extraction, list):
            for mem in memory_extraction:
                if isinstance(mem, dict) and "key" in mem and "value" in mem:
                    existing = db.execute(
                        "SELECT id FROM profile_memory WHERE user_id = ? AND profile_name = ? AND key = ?",
                        (user_id, profile_name, mem["key"])
                    ).fetchone()
                    if existing:
                        db.execute(
                            "UPDATE profile_memory SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (mem["value"], existing["id"])
                        )
                    else:
                        db.execute(
                            "INSERT INTO profile_memory (user_id, profile_name, key, value, source) VALUES (?, ?, ?, ?, ?)",
                            (user_id, profile_name, mem["key"], mem["value"], "auto")
                        )
                    db.commit()
    except Exception as e:
        print(f"[Memory Extraction] Warning: {e}")

    # 9. Save State
    chat_history.append({"role": "user", "content": query.question})
    chat_history.append({"role": "assistant", "content": ai_response})

    if query.session_id:
        # Save to session-specific file
        session_path = f"{profile_folder}/sessions/session_{query.session_id}.json"
        os.makedirs(os.path.dirname(session_path), exist_ok=True)
        with open(session_path, "w", encoding="utf-8") as f:
            # Keep last 20 messages for session
            json.dump(chat_history[-20:], f, indent=4)
        # Update session timestamp
        db.execute(
            "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
            (query.session_id, user_id)
        )
        db.commit()
    else:
        # Legacy: save to profile-level history
        if history_file:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(chat_history[-20:], f, indent=4)

    return {
        "status": "success",
        "agent_response": ai_response,
        "reliability_references": reliability_references,
        "rag_online": rag_payload.get("rag_online", False),
        "domain_retrieval": {
            "domains": rag_payload.get("domains", []),
            "charts": rag_payload.get("selected_charts", []),
            "route_source": rag_payload.get("domain_route_source", "unknown"),
            "retrieval_status": rag_payload.get("retrieval_status", {}),
        },
        "deterministic_astronomy": matrix_payload,
        "prediction_calibration": prediction_calibration,
        "empirical_predictions": prediction_calibration,
    }

@app.get("/api/chat_history")
async def get_chat_history(profile: str = None, current_user = Depends(get_current_user)):
    user_id = current_user["username"]
    if not profile: return []
    history_path = f"users/{user_id}/profiles/{profile.replace(' ', '_')}/chat_history.json"
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.delete("/api/profiles/{profile_name}")
async def delete_profile(profile_name: str, current_user = Depends(get_current_user)):
    user_id = current_user["username"]
    profile_path = f"users/{user_id}/profiles/{profile_name.replace(' ', '_')}"

    if os.path.exists(profile_path):
        import shutil
        shutil.rmtree(profile_path)
        return {"status": "success", "message": f"Profile {profile_name} deleted successfully"}

    raise HTTPException(status_code=404, detail="Profile not found")

@app.get("/api/chart_matrix")
async def get_chart_matrix(profile: str = None, current_user = Depends(get_current_user)):
    user_id = current_user["username"]
    if not profile: return {"status": "error", "message": "No profile specified"}
    matrix_path = f"users/{user_id}/profiles/{profile.replace(' ', '_')}/chart_matrix.json"

    if os.path.exists(matrix_path):
        try:
            with open(matrix_path, "r", encoding="utf-8") as f:
                data = json.load(f)

                        # Cached chart_matrix.json is a derived artifact, never a computational source.
            # Regenerate legacy, incomplete, or schema-mismatched data through AstroEngine.
            metadata = data.get("metadata", {})
            regen_keys = REQUIRED_CHART_MATRIX_KEYS
            needs_regen = (
                metadata.get("schema_version") != "1.0"
                or any(not data.get(k) for k in regen_keys)
            )

            if needs_regen:
                try:
                    metadata = data.get("metadata", {})
                    local_time = metadata.get("local_time")
                    timezone = metadata.get("timezone")
                    lat = metadata.get("lat") or metadata.get("latitude")
                    lon = metadata.get("lon") or metadata.get("longitude")

                    # Load from birth_details.json if missing in metadata
                    birth_details_path = f"users/{user_id}/profiles/{profile.replace(' ', '_')}/birth_details.json"
                    if os.path.exists(birth_details_path):
                        try:
                            with open(birth_details_path, "r", encoding="utf-8") as bf:
                                b_details = json.load(bf)
                            local_time = local_time or b_details.get("local_time")
                            timezone = timezone or b_details.get("timezone")
                            lat = lat or b_details.get("lat") or b_details.get("latitude") or 22.5
                            lon = lon or b_details.get("lon") or b_details.get("longitude") or 88.3
                        except Exception as e:
                            print(f"Failed to read birth details: {e}")

                    if not lat: lat = 22.5
                    if not lon: lon = 88.3

                    if local_time and timezone:

                        # Regenerate full chart to ensure all components are correct
                        new_chart = core_engine.generate_chart(local_time, timezone, lat, lon)

                        features_obj = FeatureExtractor.generate_features(new_chart)

                        features = features_obj.model_dump()
                        base_career = AstrologicalScoringEngine.score_career(features_obj)

                        intelligence_scores = DivisionalIntelligenceSystem.validate_career_d10(
                            features_obj, base_career, new_chart
                        )
                        prediction_calibration = build_prediction_calibration(new_chart, features_obj)

                        data = build_chart_matrix_payload(new_chart, features, intelligence_scores, prediction_calibration)

                        with open(matrix_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4)
                except Exception as ex:
                    import traceback
                    logging.error(f"Dynamic feature regeneration failed: {ex}\n{traceback.format_exc()}")
                    print(f"Dynamic feature regeneration failed: {ex}\n{traceback.format_exc()}")

            return {
                "status": "success",
                "deterministic_astronomy": data,
                "semantic_features": data.get("semantic_features", {}),
                "quantitative_intelligence": data.get("quantitative_intelligence", {}),
                "empirical_predictions": data.get("empirical_predictions", {"status": "not_provided"}),
                "prediction_calibration": data.get("prediction_calibration", {"status": "calibration_unavailable"}),
                "navatara_chakra": data.get("navatara_chakra", {}),
            }
        except Exception as parse_err:
            import traceback
            logging.error(f"[get_chart_matrix] Failed to parse/regenerate matrix: {parse_err}\n{traceback.format_exc()}")
            return {"status": "error", "message": f"Failed to parse matrix: {str(parse_err)}"}
    return {"status": "error", "message": "Matrix not found"}

@app.post("/generate_chart_image")
async def generate_chart_image(request: ChartImageRequest):
    try:
        planets_by_sign = {}
        for p, sign in request.varga_matrix.items():
            if str(sign).strip() == "": continue
            sn = str(sign).replace("ZodiacSign.", "").replace("<", "").replace(">", "").strip().capitalize()
            if not sn: continue
            abbrev = p[:2].capitalize() if p.lower() != "ascendant" else "Asc"
            if sn not in planets_by_sign:
                planets_by_sign[sn] = []
            planets_by_sign[sn].append(abbrev)

        b64_str = ChartDrawer.draw_east_indian_chart(request.chart_name, planets_by_sign)
        return {"status": "success", "image_base64": b64_str}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_chart_data")
async def generate_chart_data(data: BirthData, current_user = Depends(get_current_user)):
    try:
        chart = core_engine.generate_chart(
            data.local_time,
            data.timezone,
            data.latitude,
            data.longitude,
        )

        features_obj = FeatureExtractor.generate_features(chart)
        features = features_obj.model_dump()
        base_career = AstrologicalScoringEngine.score_career(features_obj)
        intelligence_scores = DivisionalIntelligenceSystem.validate_career_d10(
            features_obj, base_career, chart
        )
        uncertainty = chart.metadata.uncertainty_score
        prediction_calibration = build_prediction_calibration(chart, features_obj)
        return {
            "status": "success",
            "deterministic_astronomy": build_chart_matrix_payload(chart, features, intelligence_scores, prediction_calibration),
            "semantic_features": features,
            "quantitative_intelligence": intelligence_scores,
            "prediction_calibration": prediction_calibration,
            "empirical_predictions": prediction_calibration,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    import threading
    import time
    import requests

    def log_ngrok_url():
        import subprocess
        import os

        ngrok_path = os.path.join(os.getcwd(), "ngrok-bin", "ngrok.exe")

        # 1. Check if ngrok is already running (via API)
        try:
            response = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=2)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get("tunnels", [])
                if tunnels:
                    public_url = tunnels[0].get("public_url")
                    print("[MOBILE ACCESS ONLINE]")
                    print(f"Public URL: {public_url}")
                    print("The tunnel is ready for remote access.")
                    return
        except:
            pass

        # 2. If not running, try to launch it automatically
        if os.path.exists(ngrok_path):
            print("[MOBILE ACCESS] Starting ngrok tunnel...")
            try:
                # Launch ngrok using its configured account
                subprocess.Popen(
                    [ngrok_path, "http", "8000"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                # Wait a bit and try to get the URL
                for _ in range(10):
                    time.sleep(2)
                    try:
                        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=1)
                        if resp.status_code == 200:
                            data = resp.json()
                            tunnels = data.get("tunnels", [])
                            if tunnels:
                                public_url = tunnels[0].get("public_url")
                                print("[MOBILE ACCESS ONLINE]")
                                print(f"Public URL: {public_url}")
                                print("The tunnel is ready for remote access.")
                                return
                    except:
                        continue
            except Exception as e:
                print(f"[MOBILE ACCESS] Could not start ngrok: {e}")
        else:
            print("[MOBILE ACCESS] ngrok.exe was not found; skipping remote access.")

    # Start URL logger in background
    threading.Thread(target=log_ngrok_url, daemon=True).start()

    # Test boot mapping
    uvicorn.run(app, host="0.0.0.0", port=8000)
