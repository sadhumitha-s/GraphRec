from fastapi import APIRouter, Depends
from typing import List
from pydantic import BaseModel
from sqlalchemy.orm import Session
import time

from app.db import crud, session
from app.core.recommender import get_engine
from app.utils.redis import redis_client # <--- UPDATED IMPORT (Uses the SSL fix)

router = APIRouter()

class InteractionRequest(BaseModel):
    user_id: int
    item_id: int

@router.post("/", summary="Log a user-item interaction (Like)")
def log_interaction(data: InteractionRequest, db: Session = Depends(session.get_db)):
    # 1. Save to DB
    interaction = crud.create_interaction(db, data.user_id, data.item_id)
    
    # 2. Update C++ Engine
    engine = get_engine()
    # Use the actual timestamp from the DB interaction
    if hasattr(engine, "add_interaction"):
        engine.add_interaction(data.user_id, data.item_id, interaction.timestamp) 
    
    # 3. Wipe Cache (Standard Redis Logic)
    if redis_client:
        try:
            # Find all keys for this user (e.g. rec:101:bfs:5, rec:101:ppr:5)
            for key in redis_client.scan_iter(f"rec:{data.user_id}:*"):
                redis_client.delete(key)
        except Exception as e:
            print(f"⚠️ Redis Delete Error: {e}")
    
    return {"status": "success", "msg": "Interaction logged"}

@router.delete("/", summary="Remove an interaction (Unlike)")
def delete_interaction(data: InteractionRequest, db: Session = Depends(session.get_db)):
    crud.delete_interaction(db, data.user_id, data.item_id)
    
    engine = get_engine()
    if hasattr(engine, "remove_interaction"):
        engine.remove_interaction(data.user_id, data.item_id)

    # Wipe Cache
    if redis_client:
        try:
            for key in redis_client.scan_iter(f"rec:{data.user_id}:*"):
                redis_client.delete(key)
        except Exception as e:
            print(f"⚠️ Redis Delete Error: {e}")

    return {"status": "success", "msg": "Interaction removed"}

@router.get("/{user_id}", response_model=List[int])
def get_user_interactions(user_id: int, db: Session = Depends(session.get_db)):
    return list(crud.get_user_interacted_ids(db, user_id))