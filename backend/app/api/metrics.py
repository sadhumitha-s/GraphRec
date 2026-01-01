from fastapi import APIRouter
from ..core.recommender import get_engine

router = APIRouter()

@router.get("/")
def get_graph_metrics():
    engine = get_engine()
    return {
        "nodes_users": engine.get_user_count(),
        "nodes_items": engine.get_item_count(),
        "edges_interactions": engine.get_edge_count()
    }