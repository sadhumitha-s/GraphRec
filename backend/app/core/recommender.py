import sys
import os

# 1. Attempt to import the C++ module
# We look for it in the parent directory (backend/app) or current path
try:
    # This import assumes the .so file is inside backend/app/
    # If running from backend/app, simple import works
    import recommender 
    print("[Core] C++ Optimization Engine Loaded.")
    _is_cpp = True
except ImportError:
    print("[Core] C++ Module not found. Using SLOW Python fallback.")
    _is_cpp = False

class PythonFallbackEngine:
    """Used if C++ module is missing to prevent crash"""
    def __init__(self):
        self.data = []
    def add_interaction(self, u, i, t):
        self.data.append((u, i))
    def recommend(self, user_id, k):
        return [] # Dummy
    def rebuild(self, data):
        pass
    def get_user_count(self): return 0
    def get_item_count(self): return 0
    def get_edge_count(self): return 0

# 2. Instantiate the Engine Singleton
if _is_cpp:
    engine = recommender.Engine()
else:
    engine = PythonFallbackEngine()

def get_engine():
    return engine