from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import time
from ..db import session, crud
from ..core.recommender import get_engine
from pydantic import BaseModel

router = APIRouter()

class ItemResponse(BaseModel):
    id: int
    title: str
    category: str

class RecResponse(BaseModel):
    user_id: int
    recommendations: List[ItemResponse]
    latency_ms: float

from pydantic import BaseModel # re-import for safety in file block

@router.get("/{user_id}", response_model=RecResponse)
def get_recommendations(user_id: int, k: int = 5, db: Session = Depends(session.get_db)):
    engine = get_engine()
    
    # 1. Run BFS Algorithm (C++)
    t0 = time.time()
    rec_ids = engine.recommend(user_id, k)
    t1 = time.time()
    
    # 2. Hydrate IDs with Metadata from DB
    # (In production, cache this item_map or query via IN clause)
    item_map = crud.get_item_map(db)
    
    results = []
    for item_id in rec_ids:
        meta = item_map.get(item_id, {"title": "Unknown", "category": "Unknown"})
        results.append({
            "id": item_id,
            "title": meta["title"],
            "category": meta["category"]
        })
        
    return {
        "user_id": user_id,
        "recommendations": results,
        "latency_ms": (t1 - t0) * 1000
    }