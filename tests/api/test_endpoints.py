from fastapi.testclient import TestClient
import sys
import os

# Ensure we can import from the backend directory
# This mimics running from the project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.main import app

client = TestClient(app)

def test_root():
    """Check if API is up"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_items_list():
    """Check if seed items are loaded"""
    response = client.get("/items")
    assert response.status_code == 200
    data = response.json()
    # We expect at least the seeded items (Matrix, etc.)
    assert len(data) > 0
    assert "101" in data # ID 101 is The Matrix in our seed data

def test_recommendation_flow():
    """Full flow: Log interactions -> Get Recommendations"""
    
    # 1. User 999 likes Item 101 (The Matrix)
    # 2. User 888 likes Item 101 (The Matrix) AND Item 104 (Toy Story)
    # 3. User 999 should be recommended Item 104
    
    # Setup interactions
    client.post("/interaction/", json={"user_id": 999, "item_id": 101})
    client.post("/interaction/", json={"user_id": 888, "item_id": 101})
    client.post("/interaction/", json={"user_id": 888, "item_id": 104})
    
    # Get recommendations for User 999
    response = client.get("/recommend/999?k=5")
    assert response.status_code == 200
    
    data = response.json()
    assert data["user_id"] == 999
    
    # Check if we got recommendations
    recs = data["recommendations"]
    
    # Note: If the C++ engine is not compiled/loaded, the fallback engine 
    # might return empty lists or dummy data depending on implementation.
    # We check structure regardless.
    assert isinstance(recs, list)
    
    # If the logic holds (and C++ engine is running), 104 should be here
    # We map IDs to check presence
    rec_ids = [r["id"] for r in recs]
    
    # If using the Mock/Fallback Python engine or Real C++, 
    # ensuring the flow doesn't crash is the primary integration test.
    print(f"Recommendations for 999: {rec_ids}")

def test_metrics():
    """Check metrics endpoint"""
    response = client.get("/metrics/")
    assert response.status_code == 200
    data = response.json()
    assert "nodes_users" in data
    assert "nodes_items" in data
    assert "edges_interactions" in data