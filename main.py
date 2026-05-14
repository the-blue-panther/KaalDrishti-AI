import json
import os
import sqlite3
import jwt
import datetime
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
from chart_engine.coordinate_transformer import ZODIAC_ORDER
from chart_engine.astrological_derivation import AstrologicalDerivation
env_path = r"d:\Downloads\Projects\Astro Agent\Neo4j-Astro DB knowledge graph details\Neo4j-Active-75546446.env"
from dotenv import load_dotenv
load_dotenv(dotenv_path=env_path, override=True)

from feature_extraction.extractor import FeatureExtractor
from intelligence_layer.ase import AstrologicalScoringEngine
from intelligence_layer.dis import DivisionalIntelligenceSystem
from rag_bridge.graph_query_builder import RAGCompiler
from agent_inference.core import AstroAgentCore

# --- AUTHENTICATION CONFIG ---
SECRET_KEY = "KAALDRISHTI_SECURE_TOKEN_2026" # In production, use env variable
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
    print(f"\n[❌ VALIDATION ERROR] {errors}\n")
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

class ChartImageRequest(BaseModel):
    chart_name: str
    varga_matrix: dict[str, str]

from chart_engine.chart_drawer import ChartDrawer

# Serve Frontend DOM
app.mount("/static", StaticFiles(directory="frontend"), name="static")

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
    
    # 1. Execute Consolidated Math Pipeline
    try:
        chart = core_engine.generate_chart(query.birth_data.local_time, query.birth_data.timezone, query.birth_data.latitude, query.birth_data.longitude)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Engine failure: {str(e)}")

    # 2. Semantic Feature Extraction
    features_obj = FeatureExtractor.generate_features(chart)
    features = features_obj.model_dump()
    
    # 3. Quantitative Intelligence Scoring
    base_career = AstrologicalScoringEngine.score_career(features_obj)
    intelligence_scores = DivisionalIntelligenceSystem.validate_career_d10(
        features_obj, base_career, chart["divisional_charts"]
    )
    
    # 4. RAG Integration via GraphDB
    rag_payload = rag_compiler.fetch_all_context(features)
    
    # 5. Persistence & Profile Meta (Scoped to Profile Name)
    profile_name = query.seeker_name.replace(" ", "_")
    profile_folder = f"users/{user_id}/profiles/{profile_name}"
    os.makedirs(profile_folder, exist_ok=True)

    metadata = chart["metadata"]
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
    
    # Cache matrix for re-hydration
    matrix_payload = {
        "metadata": metadata,
        "planetary_positions": chart["planetary_positions"],
        "divisional_charts": chart["divisional_charts"],
        "panchang": chart["panchang"],
        "dasha_timeline": chart["dasha_timeline"]
    }
    with open(f"{profile_folder}/chart_matrix.json", "w", encoding="utf-8") as f:
        json.dump(matrix_payload, f, indent=4)

    # 6. Execute Agent Inference
    history_file = f"{profile_folder}/chat_history.json"
    chat_history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                chat_history = json.load(f)
        except: pass

    ai_response = agent_core.generate_response(
        user_query=query.question,
        raw_chart=chart,
        features=features,
        quantitative_scores=intelligence_scores,
        neo4j_context=rag_payload,
        history=chat_history,
        gender=query.birth_data.gender,
        preferred_language=current_user["preferred_language"]
    )

    # 7. Save State
    chat_history.append({"role": "user", "content": query.question})
    chat_history.append({"role": "assistant", "content": ai_response})
    
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(chat_history[-20:], f, indent=4)

    return {
        "status": "success",
        "agent_response": ai_response,
        "rag_online": rag_payload.get("rag_online", False),
        "deterministic_astronomy": matrix_payload
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
            
            # --- LEGACY RECOVERY LOGIC ---
            vargas = data.get("divisional_charts", {})
            if vargas and "Sun" in vargas: # Legacy format detected
                new_v = {}
                for p_key, p_val in vargas.items():
                    if p_key == "D1_Main":
                        new_v["D1_Main"] = p_val
                        continue
                    for chart_name, sign in p_val.items():
                        if chart_name not in new_v:
                            new_v[chart_name] = {}
                        new_v[chart_name][p_key] = sign
                data["divisional_charts"] = new_v
            
            if "D1_Main" not in data.get("divisional_charts", {}):
                d1_matrix = {p: pos['sign'] for p, pos in data.get('planetary_positions', {}).items() if isinstance(pos, dict) and 'sign' in pos}
                if "metadata" in data and "ascendant" in data["metadata"]:
                     d1_matrix['Ascendant'] = data['metadata']['ascendant']
                data.setdefault("divisional_charts", {})["D1_Main"] = d1_matrix
            
            # Ensure Ascendant in all vargas
            asc_lon = data.get("metadata", {}).get("ascendant_longitude")
            if asc_lon:
                asc_vargas = AstrologicalDerivation.calculate_vargas(asc_lon, ZODIAC_ORDER)
                vargas = data.get("divisional_charts", {})
                for v_name, v_sign in asc_vargas.items():
                    if v_name in vargas and "Ascendant" not in vargas[v_name]:
                        vargas[v_name]["Ascendant"] = v_sign
            
            if "panchang" not in data:
                pp = data.get("planetary_positions", {})
                sun_pos = pp.get("Sun", {})
                moon_pos = pp.get("Moon", {})
                if sun_pos and moon_pos and "metadata" in data and "julian_day" in data["metadata"]:
                    sun_lon = sun_pos.get("longitude_ecliptic")
                    moon_lon = moon_pos.get("longitude_ecliptic")
                    if sun_lon is not None and moon_lon is not None:
                        data["panchang"] = AstrologicalDerivation.calculate_panchang(
                            data["metadata"]["julian_day"], sun_lon, moon_lon, 
                            data["metadata"].get("latitude", 22.5), data["metadata"].get("longitude", 88.3)
                        )
            
            return {"status": "success", "deterministic_astronomy": data}
        except Exception:
            return {"status": "error", "message": "Failed to parse matrix"}
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
        chart = core_engine.generate_chart(data.local_time, data.timezone, data.latitude, data.longitude)
        features_obj = FeatureExtractor.generate_features(chart)
        features = features_obj.model_dump()
        base_career = AstrologicalScoringEngine.score_career(features_obj)
        intelligence_scores = DivisionalIntelligenceSystem.validate_career_d10(
            features_obj, base_career, chart["divisional_charts"]
        )
        return {
            "status": "success",
            "deterministic_astronomy": chart,
            "semantic_features": features,
            "quantitative_intelligence": intelligence_scores
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
                    print(f"\n\n\n[📡 MOBILE ACCESS ONLINE]")
                    print(f"Public URL: {public_url}")
                    print(f"Local IP:   http://192.168.0.109:8000")
                    print(f"Scan this URL on your mobile to begin.\n\n\n")
                    return
        except:
            pass

        # 2. If not running, try to launch it automatically
        if os.path.exists(ngrok_path):
            print("\n[🛠️ MOBILE ACCESS] Initializing automatic ngrok tunnel...")
            try:
                # Launch ngrok in the background using the static domain
                subprocess.Popen(
                    [ngrok_path, "http", "--domain=unmurmuring-huggingly-penni.ngrok-free.dev", "8000"],
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
                                print(f"\n\n\n[📡 MOBILE ACCESS ONLINE]")
                                print(f"Public URL: {public_url}")
                                print(f"Local IP:   http://192.168.0.109:8000")
                                print(f"Scan this URL on your mobile to begin.\n\n\n")
                                return
                    except:
                        continue
            except Exception as e:
                print(f"\n[⚠️ MOBILE ACCESS] Could not auto-start ngrok: {e}\n")
        else:
            print("\n[⚠️ MOBILE ACCESS] ngrok.exe not found in ngrok-bin. Manual start required.\n")

    # Start URL logger in background
    threading.Thread(target=log_ngrok_url, daemon=True).start()

    # Test boot mapping
    uvicorn.run(app, host="0.0.0.0", port=8000)
