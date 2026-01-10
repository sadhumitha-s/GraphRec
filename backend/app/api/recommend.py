from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import time
from ..db import session, crud
from ..core.recommender import get_engine
from ..core import redis_client # <--- NEW IMPORT

router = APIRouter()

class ItemResponse(BaseModel):
    id: int
    title: str
    category: str
    reason: str 

class RecResponse(BaseModel):
    user_id: int
    recommendations: List[ItemResponse]
    latency_ms: float
    source: str = "Compute" # New field to debug (Compute vs Cache)

class PrefRequest(BaseModel):
    user_id: int
    genres: List[str]

@router.post("/preferences")
def save_preferences(data: PrefRequest, db: Session = Depends(session.get_db)):
    crud.set_user_preferences(db, data.user_id, data.genres)
    # NEW: Invalidate cache because tastes changed
    redis_client.invalidate_user_cache(data.user_id)
    return {"status": "success", "msg": "Preferences saved"}

@router.get("/{user_id}", response_model=RecResponse)
def get_recommendations(user_id: int, k: int = 5, db: Session = Depends(session.get_db)):
    t0 = time.time()

    # --- 1. TRY CACHE ---
    cached_recs = redis_client.get_cached_recommendations(user_id)
    if cached_recs is not None:
        t1 = time.time()
        return {
            "user_id": user_id,
            "recommendations": cached_recs,
            "latency_ms": (t1 - t0) * 1000,
            "source": "Redis Cache ⚡"
        }

    # --- 2. COMPUTE (If cache miss) ---
    engine = get_engine()
    seen_ids = crud.get_user_interacted_ids(db, user_id)
    pref_ids = crud.get_user_preference_ids(db, user_id)

    # C++ Logic
    raw_recs = engine.recommend(user_id, k, pref_ids)
    rec_ids = [pid for pid in raw_recs if pid not in seen_ids]
    strategy = "Graph-Based (Personalized + Taste)"

    # Fallbacks
    if not rec_ids:
        candidates = crud.get_popular_item_ids(db, limit=k + len(seen_ids) + 5)
        rec_ids = [pid for pid in candidates if pid not in seen_ids][:k]
        if rec_ids: strategy = "Global Trending (Popular)"

    if not rec_ids:
        candidates = crud.get_default_items(db, limit=k + len(seen_ids) + 5)
        rec_ids = [did for did in candidates if did not in seen_ids][:k]
        strategy = "New Arrivals (Catalog)"

    # Hydrate
    item_map = crud.get_item_map(db)
    results = []
    for item_id in rec_ids:
        meta = item_map.get(item_id, {"title": f"Unknown {item_id}", "category": "Unknown"})
        results.append({
            "id": item_id,
            "title": meta["title"],
            "category": meta["category"],
            "reason": strategy
        })

    t1 = time.time()

    # --- 3. SAVE TO CACHE ---
    # Only cache if we actually found something
    if results:
        redis_client.set_cached_recommendations(user_id, results)

    return {
        "user_id": user_id,
        "recommendations": results,
        "latency_ms": (t1 - t0) * 1000,
        "source": "C++ Engine ⚙️"
    }