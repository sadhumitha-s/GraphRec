from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .db import session, models, crud
from .api import interactions, recommend, metrics
from .core.recommender import get_engine

# --- Lifecycle Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Executes on startup and shutdown.
    1. Creates DB tables if they don't exist.
    2. Seeds initial items for the demo.
    3. LOADS DATA from SQL -> C++ Memory.
    """
    # 1. Create DB Tables
    models.Base.metadata.create_all(bind=session.engine)
    
    db = session.SessionLocal()
    try:
        # 2. Seed Initial Items (if empty)
        crud.seed_items(db)
        
        # 3. Load Interactions from DB to C++ Engine
        print("🔄 [Startup] Loading interactions from DB into C++ Graph...")
        all_interactions = crud.get_all_interactions(db)
        
        engine = get_engine()
        
        count = 0
        for i in all_interactions:
            # Add to C++ In-Memory Graph
            engine.add_interaction(i.user_id, i.item_id, i.timestamp)
            count += 1
            
        print(f"✅ [Startup] Loaded {count} historical interactions into Graph.")
        
    except Exception as e:
        print(f"❌ [Startup Error] Failed to load graph data: {e}")
    finally:
        db.close()
    
    yield
    # (Shutdown logic goes here if needed)

# --- App Definition ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

# --- CORS Configuration ---
# Allow requests from your frontend (HTML/JS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Register Routers ---
app.include_router(interactions.router, prefix="/interaction", tags=["Interactions"])
app.include_router(recommend.router, prefix="/recommend", tags=["Recommendations"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])

# --- Root Endpoints ---

@app.get("/")
def root():
    return {
        "message": "GraphRec API is running", 
        "docs_url": "/docs",
        "status": "online"
    }

@app.get("/items")
def get_all_items_endpoint():
    """Helper endpoint for the frontend to list all available items."""
    db = session.SessionLocal()
    try:
        items = crud.get_item_map(db) 
        # Return as a dictionary for easy JS lookup: {101: {...}, 102: {...}}
        return {k: v for k, v in items.items()}
    finally:
        db.close()