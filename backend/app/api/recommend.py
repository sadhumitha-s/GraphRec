from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
import time
from ..db import session, crud
from ..core.recommender import get_engine

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

# NEW: API to save preferences
class PrefRequest(BaseModel):
    user_id: int
    genres: List[str]

@router.post("/preferences")
def save_preferences(data: PrefRequest, db: Session = Depends(session.get_db)):
    crud.set_user_preferences(db, data.user_id, data.genres)
    return {"status": "success", "msg": "Preferences saved"}

@router.get("/{user_id}", response_model=RecResponse)
def get_recommendations(user_id: int, k: int = 5, db: Session = Depends(session.get_db)):
    engine = get_engine()
    t0 = time.time()
    
    seen_ids = crud.get_user_interacted_ids(db, user_id)
    
    # NEW: Fetch user's preferred genre IDs [1, 4, ...]
    pref_ids = crud.get_user_preference_ids(db, user_id)

    # 1. C++ Recommendation (Pass prefs)
    # The C++ engine will boost scores for items matching pref_ids
    raw_recs = engine.recommend(user_id, k, pref_ids)
    
    rec_ids = [pid for pid in raw_recs if pid not in seen_ids]
    strategy = "Graph-Based (Personalized + Taste)"

    # 2. Fallback
    if not rec_ids:
        candidates = crud.get_popular_item_ids(db, limit=k + len(seen_ids) + 5)
        rec_ids = [pid for pid in candidates if pid not in seen_ids][:k]
        if rec_ids: strategy = "Global Trending (Popular)"

    if not rec_ids:
        candidates = crud.get_default_items(db, limit=k + len(seen_ids) + 5)
        rec_ids = [did for did in candidates if did not in seen_ids][:k]
        strategy = "New Arrivals (Catalog)"

    t1 = time.time()
    
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
        
    return {
        "user_id": user_id,
        "recommendations": results,
        "latency_ms": (t1 - t0) * 1000
    }