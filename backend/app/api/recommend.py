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
    reason: str = "Personalized" # New field to show user why they see this

class RecResponse(BaseModel):
    user_id: int
    recommendations: List[ItemResponse]
    latency_ms: float

@router.get("/{user_id}", response_model=RecResponse)
def get_recommendations(user_id: int, k: int = 5, db: Session = Depends(session.get_db)):
    engine = get_engine()
    
    t0 = time.time()
    
    # 1. Attempt C++ Graph Recommendation (Personalized)
    rec_ids = engine.recommend(user_id, k)
    strategy = "Graph-Based (Personalized)"

    # 2. Fallback: Hybrid / Cold Start
    if not rec_ids:
        # A. Try Popular Items (Global Trending)
        rec_ids = crud.get_popular_item_ids(db, limit=k)
        strategy = "Global Trending (Popular)"
        
        # B. Safety Net (System Cold Start)
        # If NO interactions exist in the entire DB, just show catalog items
        if not rec_ids:
            rec_ids = crud.get_default_items(db, limit=k)
            strategy = "New Arrivals (Catalog)"

    t1 = time.time()
    
    # 3. Hydrate Data
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