from fastapi import APIRouter, Depends
from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import crud, session
from ..core.recommender import get_engine
from ..core import redis_client # <--- NEW IMPORT

router = APIRouter()

class InteractionRequest(BaseModel):
    user_id: int
    item_id: int

@router.post("/", summary="Log a user-item interaction (Like)")
def log_interaction(data: InteractionRequest, db: Session = Depends(session.get_db)):
    crud.create_interaction(db, data.user_id, data.item_id)
    engine = get_engine()
    engine.add_interaction(data.user_id, data.item_id, 0) # timestamp 0 for simplicity here or import time
    
    # NEW: Wipe cache so new like affects next recommendation
    redis_client.invalidate_user_cache(data.user_id)
    
    return {"status": "success", "msg": "Interaction logged"}

@router.delete("/", summary="Remove an interaction (Unlike)")
def delete_interaction(data: InteractionRequest, db: Session = Depends(session.get_db)):
    crud.delete_interaction(db, data.user_id, data.item_id)
    engine = get_engine()
    if hasattr(engine, "remove_interaction"):
        engine.remove_interaction(data.user_id, data.item_id)

    # NEW: Wipe cache
    redis_client.invalidate_user_cache(data.user_id)

    return {"status": "success", "msg": "Interaction removed"}

@router.get("/{user_id}", response_model=List[int])
def get_user_interactions(user_id: int, db: Session = Depends(session.get_db)):
    return list(crud.get_user_interacted_ids(db, user_id))