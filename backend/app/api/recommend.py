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

@router.get("/{user_id}", response_model=RecResponse)
def get_recommendations(user_id: int, k: int = 5, db: Session = Depends(session.get_db)):
    engine = get_engine()
    t0 = time.time()
    
    # 1. Fetch "Blacklist" (Items user has already seen)
    # We convert to a set for fast O(1) checking
    seen_ids = crud.get_user_interacted_ids(db, user_id)

    # 2. Strategy A: Graph-Based (Personalized)
    # Ask C++ Engine
    raw_recs = engine.recommend(user_id, k)
    
    # Strict Filter: Remove any item that is in seen_ids
    # (Even if C++ is supposed to do it, we do it here again to be 100% sure)
    rec_ids = [pid for pid in raw_recs if pid not in seen_ids]
    strategy = "Graph-Based (Personalized)"

    # 3. Strategy B: Global Trending (Fallback)
    # If Strategy A failed (empty list), try Popular items
    if not rec_ids:
        # Fetch more than k (k + len(seen) + buffer) to ensure we have enough after filtering
        candidates = crud.get_popular_item_ids(db, limit=k + len(seen_ids) + 5)
        
        # Filter again
        rec_ids = [pid for pid in candidates if pid not in seen_ids][:k]
        
        if rec_ids:
            strategy = "Global Trending (Popular)"

    # 4. Strategy C: Safety Net (Catalog)
    # If even Popular returned nothing (e.g., system has 0 likes total, or user has seen all popular items)
    if not rec_ids:
        candidates = crud.get_default_items(db, limit=k + len(seen_ids) + 5)
        rec_ids = [did for did in candidates if did not in seen_ids][:k]
        strategy = "New Arrivals (Catalog)"

    t1 = time.time()
    
    # 5. Hydrate Data (ID -> Title/Category)
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