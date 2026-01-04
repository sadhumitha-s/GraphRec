from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .config import settings
from .db import session, models, crud
from .api import interactions, recommend, metrics
from .core.recommender import get_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=session.engine)
    db = session.SessionLocal()
    try:
        # 1. Seed & Load Item Metadata (Genres)
        all_items = crud.seed_items(db) # This now returns item objects
        engine = get_engine()
        
        print("🔄 [Startup] Loading Item Genres into C++...")
        for item in all_items:
            gid = crud.get_genre_id(item.category)
            # C++ method: set_item_genre(item_id, genre_id)
            if hasattr(engine, "set_item_genre"):
                engine.set_item_genre(item.id, gid)
        
        # 2. Load Interactions
        print("🔄 [Startup] Loading Interactions...")
        all_interactions = crud.get_all_interactions(db)
        for i in all_interactions:
            engine.add_interaction(i.user_id, i.item_id, i.timestamp)
            
        print("✅ [Startup] Engine Ready.")
    except Exception as e:
        print(f"❌ [Startup Error] {e}")
    finally:
        db.close()
    yield

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