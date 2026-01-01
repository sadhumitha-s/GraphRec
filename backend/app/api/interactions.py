from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..db import crud, session
from ..core.recommender import get_engine

router = APIRouter()

class InteractionRequest(BaseModel):
    user_id: int
    item_id: int

@router.post("/", summary="Log a user-item interaction")
def log_interaction(data: InteractionRequest, db: Session = Depends(session.get_db)):
    # 1. Persist to Database (MySQL/SQLite)
    interaction = crud.create_interaction(db, data.user_id, data.item_id)
    
    # 2. Update In-Memory C++ Graph
    engine = get_engine()
    engine.add_interaction(interaction.user_id, interaction.item_id, interaction.timestamp)
    
    return {"status": "success", "msg": "Interaction logged", "id": interaction.id}