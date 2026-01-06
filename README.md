# Graph-based Reccommendations System

- **Hybrid Architecture:** FastAPI orchestrates logic, while a compiled C++17 extension handles $O(1)$ graph mutations.  
- **Bipartite Graph Logic:** Uses Breadth-First Search (BFS) to traverse User $\\leftrightarrow$ Item connections for transparent, deterministic recommendations.  
- **Content-Aware Scoring:** Dynamically boosts graph edge weights based on user genre preferences, blending collaborative and content-based filtering.  
- **Waterfall Strategy:** Cascades from Personalized Graph $\\to$ Global Trending $\\to$ Catalog to ensure zero empty states.  
- **Time-Decay Scoring:** Applies gravity decay formulas within the C++ engine to prioritize recent interactions.  
- **Cloud-Ready Persistence:** Seamlessly integrates with PostgreSQL (Supabase) for production-grade concurrency and storage.  
- **Real-Time Updates:** Instantly updates the in-memory graph structure upon every "Like" or "Unlike".

---

## Project Structure  
```pqsql
graphrec-engine/
│
├── backend/                        # FastAPI Orchestrator
│   ├── requirements.txt            # Dependencies (FastAPI, SQLAlchemy, Psycopg2)
│   ├── recommender*.so             # Compiled C++ Module (Must be moved here after build)
│   │
│   └── app/
│       ├── main.py                 # App Entry: Handles DB startup & loads Graph data
│       ├── config.py               # Cloud DB Configuration (PostgreSQL/Supabase)
│       │
│       ├── api/
│       │   ├── interactions.py     # POST/DELETE endpoints for Real-time Graph updates
│       │   ├── recommend.py        # Logic: Waterfall Strategy (Graph -> Trending -> Catalog)
│       │   └── metrics.py          # System stats (Node/Edge counts)
│       │
│       ├── core/
│       │   └── recommender.py      # Python Wrapper/Singleton for C++ Engine
│       │
│       └── db/
│           ├── session.py          # Database Connection (SQLAlchemy)
│           ├── models.py           # Schema: Items, Interactions, UserPreferences
│           └── crud.py             # Smart Seeding, History Fetching, Genre Mapping
│
├── cpp_engine/                     # High-Performance Graph Core
│   ├── CMakeLists.txt              # Build Config (Pybind11 integration)
│   ├── include/
│   │   └── RecommendationEngine.h  # Header: Genre Maps & BFS Definitions
│   └── src/
│       ├── RecommendationEngine.cpp # Implementation: BFS, Time-Decay, Genre Boosting
│       └── bindings.cpp            # Pybind11 hooks to expose C++ class to Python
│
├── frontend/                       # Client Application (Vanilla JS)
│   ├── index.html                  # Main UI: Genre Cloud & Movie Catalog
│   ├── recommendations.html        # Results UI: Recommendations & Strategy Badges
│   ├── css/
│   │   └── styles.css              # Dark Mode Theme & Genre Color Palettes
│   └── js/
│       └── app.js                  # State Management, API Calls, Event Listeners
│
└── docs/                           
    ├── architecture.md             
    ├── algorithms.md               
    └── complexity.md               
```

---  

### Quick Start

1. **Compile the C++ Engine**  
   You must compile the core engine before running the Python backend.
```bash
cd cpp_engine/build
cmake ..
make
mv recommender*.so ../../backend/
```  
  
2. **Start the backend**  
```bash
cd path\to\graph-recommendation-engine\backend\
uvicorn app.main:app --reload
```

3. **Start the frontend**  
   In a new terminal:
```bash
cd path\to\graph-recommendation-engine\frontend\
python3 -m http.server 3000
```
3. Go to http://localhost:3000 to interact with the system.
