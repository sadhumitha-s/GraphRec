import os
import time # <--- Added for the sleep feature
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from .config import settings
from .db import session, models, crud
from .api import interactions, recommend, metrics
from .core.recommender import get_engine

BINARY_FILE = "graph.bin"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Init DB (Creates tables if they don't exist)
    models.Base.metadata.create_all(bind=session.engine)
    db = session.SessionLocal()
    engine = get_engine()
    
    try:
        print("[Startup] Checking Database for Graph Snapshot...", flush=True)
        
        # 2. Try to download snapshot from DB (Local SQLite or Cloud Postgres)
        snapshot_blob = crud.get_latest_snapshot(db)
        
        if snapshot_blob:
            print("[Startup] Snapshot found in DB. Downloading to local disk...", flush=True)
            # Write bytes to local file so C++ can read it
            with open(BINARY_FILE, "wb") as f:
                f.write(snapshot_blob)
            
            # Load into C++
            if hasattr(engine, "load_model"):
                engine.load_model(BINARY_FILE)
                print("[Startup] Graph loaded from Snapshot!", flush=True)
            else:
                print("[Startup] Engine missing load_model. Recompile C++.", flush=True)
        else:
            print("[Startup] No Snapshot in DB. Rebuilding from Rows (Slow)...", flush=True)
            # 3. Fallback: Load from SQL Rows
            load_from_sql_rows(db, engine)
            
            # 4. Save New Snapshot to DB
            if hasattr(engine, "save_model"):
                print("[Startup] Saving new snapshot locally...", flush=True)
                engine.save_model(BINARY_FILE)
                
                print("[Startup] Uploading snapshot to Database...", flush=True)
                with open(BINARY_FILE, "rb") as f:
                    file_content = f.read()
                    crud.save_snapshot(db, file_content)
                print("[Startup] Snapshot uploaded/synced.", flush=True)

    except Exception as e:
        print(f"[Startup Error] {e}", flush=True)
        # Final safety net: Try loading rows if snapshot failed
        load_from_sql_rows(db, engine)
    finally:
        db.close()
    
    # === APP RUNS HERE ===
    yield
    # =====================

    # --- SHUTDOWN LOGIC (Added Sleep Feature) ---
    print("------------------------------------------------", flush=True)
    print("[Shutdown] Saving Application State...", flush=True)
    
    # We open a new session because the startup one is closed
    db_shutdown = session.SessionLocal()
    
    try:
        if hasattr(engine, "save_model"):
            print("[Shutdown] Saving Graph to disk...", flush=True)
            engine.save_model(BINARY_FILE)
            
            print("[Shutdown] Uploading Snapshot to Supabase...", flush=True)
            with open(BINARY_FILE, "rb") as f:
                file_content = f.read()
                crud.save_snapshot(db_shutdown, file_content)
            print("[Shutdown] ✅ Snapshot successfully synced to DB.", flush=True)
    except Exception as e:
        print(f"[Shutdown Error] {e}", flush=True)
    finally:
        db_shutdown.close()
        # The specific sleep feature you requested
        # Ensures Docker captures the logs before killing the process
        time.sleep(1) 

def load_from_sql_rows(db, engine):
    """Helper: The slow way (Row by Row)"""
    # Genres
    all_items = crud.seed_items(db)
    for item in all_items:
        gid = crud.get_genre_id(item.category)
        if hasattr(engine, "set_item_genre"):
            engine.set_item_genre(item.id, gid)
    
    # Interactions
    all_interactions = crud.get_all_interactions(db)
    print(f"   - Processing {len(all_interactions)} interactions...", flush=True)
    for i in all_interactions:
        engine.add_interaction(i.user_id, i.item_id, i.timestamp)

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
app.include_router(interactions.router, prefix="/interaction", tags=["Interactions"])
app.include_router(recommend.router, prefix="/recommend", tags=["Recommendations"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])

# --- API Endpoints ---
@app.get("/api/health")
def health_check():
    return {"status": "online", "message": "GraphRec API is running"}

@app.get("/items")
def get_all_items_endpoint():
    db = session.SessionLocal()
    items = crud.get_item_map(db)
    db.close()
    return {k: v for k, v in items.items()}

# --- STATIC FILES & FRONTEND SERVING (For Production) ---

# Robust Path Finding
# 1. Get path to backend/app/main.py
current_file = os.path.abspath(__file__)
app_dir = os.path.dirname(current_file)       # .../backend/app
backend_dir = os.path.dirname(app_dir)        # .../backend

# 2. Try identifying Frontend Location
# Location A: Project Root (Local Dev) -> .../backend/../frontend
frontend_local = os.path.join(os.path.dirname(backend_dir), "frontend")
# Location B: Docker Container (/app/frontend) -> backend_dir is /app
frontend_docker = os.path.join(backend_dir, "frontend")

if os.path.exists(frontend_local):
    FRONTEND_DIR = frontend_local
elif os.path.exists(frontend_docker):
    FRONTEND_DIR = frontend_docker
else:
    # Fallback to current directory to prevent crash, though UI won't load
    print("Warning: Frontend directory not found.", flush=True)
    FRONTEND_DIR = backend_dir

# Mount CSS and JS folders
if os.path.exists(os.path.join(FRONTEND_DIR, "css")):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
if os.path.exists(os.path.join(FRONTEND_DIR, "js")):
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")

# Catch-all route to serve index.html or specific pages
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Pass through API calls if they slipped through routers
    if full_path.startswith("api") or full_path.startswith("interaction") or full_path.startswith("recommend/") or full_path.startswith("metrics") or full_path.startswith("items") or full_path.startswith("docs") or full_path.startswith("openapi"):
        return {"error": "Not Found"}
    
    # Try to serve specific file (e.g., recommendations.html)
    target_file = os.path.join(FRONTEND_DIR, full_path)
    if os.path.exists(target_file) and os.path.isfile(target_file):
        return FileResponse(target_file)
    
    # Default: Serve index.html (SPA-like behavior)
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"error": "Frontend not found"}