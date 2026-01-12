import sys
import os
import glob
from collections import defaultdict, Counter

# Global instance
_engine = None

class PythonFallbackEngine:
    """
    A pure-Python implementation of the graph engine.
    Used automatically if the C++ extension fails to load.
    """
    def __init__(self):
        self.users = set()
        self.items = set()
        self.interactions = []
        self.item_genres = {}
        self.user_adj = defaultdict(list)
        self.item_adj = defaultdict(list)

    def add_interaction(self, user_id: int, item_id: int, timestamp: int):
        self.users.add(user_id)
        self.items.add(item_id)
        self.interactions.append((user_id, item_id, timestamp))
        self.user_adj[user_id].append(item_id)
        self.item_adj[item_id].append(user_id)

    def set_item_genre(self, item_id: int, genre_id: int):
        self.items.add(item_id)
        self.item_genres[item_id] = genre_id

    def get_user_count(self): return len(self.users)
    def get_item_count(self): return len(self.items)
    def get_edge_count(self): return len(self.interactions)
    def save_model(self, path: str): pass 
    def load_model(self, path: str): pass 

    def recommend(self, user_id: int, k: int, pref_ids: list = None):
        target_history = set(self.user_adj[user_id])
        similar_users = []
        for item_id in target_history:
            for other_user in self.item_adj[item_id]:
                if other_user != user_id:
                    similar_users.append(other_user)
        
        candidates = []
        for other_user in similar_users:
            for item_id in self.user_adj[other_user]:
                if item_id not in target_history:
                    candidates.append(item_id)
        
        counts = Counter(candidates)
        if pref_ids:
            pref_set = set(pref_ids)
            for item_id in counts:
                if self.item_genres.get(item_id) in pref_set:
                    counts[item_id] += 2

        sorted_items = counts.most_common(k)
        return [item[0] for item in sorted_items]

    def recommend_ppr(self, user_id: int, k: int, walks: int, depth: int):
        return self.recommend(user_id, k)

def get_engine():
    global _engine
    if _engine:
        return _engine
    
    # --- DEBUGGING BLOCK ---
    # We leave this in to help track if the module is loading from the right path
    print(f"[Core Debug] Python Version: {sys.version}")
    
    try:
        import recommender
        # --- THE FIX IS HERE ---
        # Changed 'Recommender()' to 'Engine()' to match your C++ definition
        if hasattr(recommender, 'Engine'):
            _engine = recommender.Engine()
            print("[Core] ✅ C++ Optimization Engine Loaded (Class: Engine).")
        elif hasattr(recommender, 'Recommender'):
            _engine = recommender.Recommender()
            print("[Core] ✅ C++ Optimization Engine Loaded (Class: Recommender).")
        else:
            print(f"[Core] ❌ Module loaded, but class not found. Attributes: {dir(recommender)}")
            raise ImportError("C++ Class mismatch")
            
    except ImportError as e:
        print(f"[Core] ❌ C++ Module Import Failed. Error: {e}")
        print("[Core] Switching to SLOW Python fallback.")
        _engine = PythonFallbackEngine()
        
    return _engine