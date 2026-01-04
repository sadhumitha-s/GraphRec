from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from . import models
import time

# --- MAPPING CONFIG (Alphabetical Order) ---
# Action=1, Animation=2, Comedy=3, Crime=4, Drama=5, Horror=6, Sci-Fi=7
GENRE_MAP = {
    "Action": 1,
    "Animation": 2,
    "Comedy": 3,
    "Crime": 4,
    "Drama": 5,
    "Horror": 6,
    "Sci-Fi": 7,
    "Unknown": 0
}

def get_genre_id(category: str) -> int:
    return GENRE_MAP.get(category, 0)

# --- INTERACTION HELPERS ---

def create_interaction(db: Session, user_id: int, item_id: int):
    # Check for duplicates
    existing = db.query(models.Interaction).filter(
        and_(models.Interaction.user_id == user_id, models.Interaction.item_id == item_id)
    ).first()
    
    if existing: 
        return existing

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

def delete_interaction(db: Session, user_id: int, item_id: int):
    db.query(models.Interaction).filter(
        and_(models.Interaction.user_id == user_id, models.Interaction.item_id == item_id)
    ).delete(synchronize_session=False)
    db.commit()

def get_all_interactions(db: Session):
    return db.query(models.Interaction).all()

def get_item_map(db: Session):
    items = db.query(models.Item).all()
    return {i.id: {"title": i.title, "category": i.category} for i in items}

def get_user_interacted_ids(db: Session, user_id: int):
    results = db.query(models.Interaction.item_id)\
                .filter(models.Interaction.user_id == user_id)\
                .all()
    return {r[0] for r in results}

# --- FALLBACK HELPERS ---

def get_popular_item_ids(db: Session, limit: int):
    results = db.query(models.Interaction.item_id)\
                .group_by(models.Interaction.item_id)\
                .order_by(func.count(models.Interaction.item_id).desc())\
                .limit(limit)\
                .all()
    return [r[0] for r in results]

def get_default_items(db: Session, limit: int):
    items = db.query(models.Item.id).limit(limit).all()
    return [i.id for i in items]

# --- PREFERENCE HELPERS ---

def set_user_preferences(db: Session, user_id: int, genre_names: list[str]):
    # 1. Delete existing preferences for this user
    db.query(models.UserPreference).filter(models.UserPreference.user_id == user_id).delete()
    
    # 2. Add new preferences
    for name in genre_names:
        gid = get_genre_id(name)
        if gid != 0:
            db.add(models.UserPreference(user_id=user_id, genre_id=gid))
    db.commit()

def get_user_preference_ids(db: Session, user_id: int):
    """Returns list of INT genre IDs [1, 4, ...] for C++ engine"""
    results = db.query(models.UserPreference.genre_id)\
                .filter(models.UserPreference.user_id == user_id)\
                .all()
    return [r[0] for r in results]

# --- CATALOG SEEDING ---

def seed_items(db: Session):
    """
    Smart Seeding: Checks if items exist, and adds them if missing.
    """
    catalog = [
        {"id": 101, "title": "The Matrix", "category": "Sci-Fi"},
        {"id": 102, "title": "Inception", "category": "Sci-Fi"},
        {"id": 103, "title": "The Godfather", "category": "Crime"},
        {"id": 104, "title": "Toy Story", "category": "Animation"},
        {"id": 105, "title": "Pulp Fiction", "category": "Crime"},
        {"id": 106, "title": "Interstellar", "category": "Sci-Fi"},
        {"id": 107, "title": "Finding Nemo", "category": "Animation"},
        {"id": 108, "title": "Spirited Away", "category": "Animation"},
        {"id": 109, "title": "The Dark Knight", "category": "Action"},
        
        # Extended
        {"id": 110, "title": "Avengers: Endgame", "category": "Action"},
        {"id": 111, "title": "Mad Max: Fury Road", "category": "Action"},
        {"id": 112, "title": "John Wick", "category": "Action"},
        {"id": 113, "title": "Get Out", "category": "Horror"},
        {"id": 114, "title": "The Shining", "category": "Horror"},
        {"id": 115, "title": "Superbad", "category": "Comedy"},
        {"id": 116, "title": "The Hangover", "category": "Comedy"},
        {"id": 117, "title": "Forrest Gump", "category": "Drama"},
        {"id": 118, "title": "Parasite", "category": "Drama"},
        {"id": 119, "title": "Coco", "category": "Animation"},
        {"id": 120, "title": "Dune", "category": "Sci-Fi"},
    ]

    for item_data in catalog:
        exists = db.query(models.Item).filter(models.Item.id == item_data["id"]).first()
        if not exists:
            # print(f"➕ Adding new movie: {item_data['title']}")
            new_item = models.Item(
                id=item_data["id"], 
                title=item_data["title"], 
                category=item_data["category"]
            )
            db.add(new_item)
    
    db.commit()
    
    # Return all items to be loaded into C++
    return db.query(models.Item).all()