from fastapi import APIRouter
from app.core.recommender import get_engine

router = APIRouter()

@router.get("/")
def get_graph_metrics():
    """
    Returns statistics about the currently loaded graph in memory.
    """
    engine = get_engine()
    
    # We use hasattr checks to be safe in case the C++ engine is being recompiled or methods are missing
    return {
        "nodes_users": engine.get_user_count() if hasattr(engine, "get_user_count") else 0,
        "nodes_items": engine.get_item_count() if hasattr(engine, "get_item_count") else 0,
        "edges_interactions": engine.get_edge_count() if hasattr(engine, "get_edge_count") else 0
    }