import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
        print("[Startup] Checking Database for Graph Snapshot...")
        
        # 2. Try to download snapshot from DB (Local SQLite or Cloud Postgres)
        snapshot_blob = crud.get_latest_snapshot(db)
        
        if snapshot_blob:
            print("[Startup] Snapshot found in DB. Downloading to local disk...")
            # Write bytes to local file so C++ can read it
            with open(BINARY_FILE, "wb") as f:
                f.write(snapshot_blob)
            
            # Load into C++
            if hasattr(engine, "load_model"):
                engine.load_model(BINARY_FILE)
                print("[Startup] Graph loaded from Snapshot!")
            else:
                print("[Startup] Engine missing load_model. Recompile C++.")
        else:
            print("[Startup] No Snapshot in DB. Rebuilding from Rows (Slow)...")
            # 3. Fallback: Load from SQL Rows
            load_from_sql_rows(db, engine)
            
            # 4. Save New Snapshot to DB
            if hasattr(engine, "save_model"):
                print("[Startup] Saving new snapshot locally...")
                engine.save_model(BINARY_FILE)
                
                print("[Startup] Uploading snapshot to Database...")
                with open(BINARY_FILE, "rb") as f:
                    file_content = f.read()
                    crud.save_snapshot(db, file_content)
                print("[Startup] Snapshot uploaded/synced.")

    except Exception as e:
        print(f"[Startup Error] {e}")
        # Final safety net: Try loading rows if snapshot failed
        load_from_sql_rows(db, engine)
    finally:
        db.close()
    yield

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
    print(f"   - Processing {len(all_interactions)} interactions...")
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

app.include_router(interactions.router, prefix="/interaction", tags=["Interactions"])
app.include_router(recommend.router, prefix="/recommend", tags=["Recommendations"])
app.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])

@app.get("/")
def root(): return {"message": "GraphRec API", "status": "online"}

@app.get("/items")
def get_all_items_endpoint():
    db = session.SessionLocal()
    items = crud.get_item_map(db)
    db.close()
    return {k: v for k, v in items.items()}