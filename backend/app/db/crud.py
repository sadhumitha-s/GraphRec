from sqlalchemy.orm import Session
from . import models
import time

def create_interaction(db: Session, user_id: int, item_id: int):
    # Use current server time
    ts = int(time.time())
    db_interaction = models.Interaction(
        user_id=user_id, 
        item_id=item_id, 
        timestamp=ts
    )
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

def get_all_interactions(db: Session):
    return db.query(models.Interaction).all()

def get_item_map(db: Session):
    """Returns a dict {id: {title, category}} for fast lookup"""
    items = db.query(models.Item).all()
    return {i.id: {"title": i.title, "category": i.category} for i in items}

def seed_items(db: Session):
    """Populate initial items if table is empty"""
    if db.query(models.Item).count() == 0:
        initial_items = [
            models.Item(id=101, title="The Matrix", category="Sci-Fi"),
            models.Item(id=102, title="Inception", category="Sci-Fi"),
            models.Item(id=103, title="The Godfather", category="Crime"),
            models.Item(id=104, title="Toy Story", category="Animation"),
            models.Item(id=105, title="Pulp Fiction", category="Crime"),
            models.Item(id=106, title="Interstellar", category="Sci-Fi"),
            models.Item(id=107, title="Finding Nemo", category="Animation"),
            models.Item(id=108, title="Spirited Away", category="Animation"),
            models.Item(id=109, title="The Dark Knight", category="Action"),
        ]
        db.add_all(initial_items)
        db.commit()