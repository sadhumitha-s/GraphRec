# **GraphRec Engine (Hybrid C++ & Python)**  
A high-performance Recommendation Engine built with a hybrid architecture. It combines the speed of a custom C++ Graph Engine for traversal algorithms (BFS, PageRank) with the flexibility of Python/FastAPI for the web layer.

[Live Demo](https://graphrec-engine.onrender.com)  
*(Note: App hosted on free tier, may spin down after inactivity. Please wait 30s for wakeup!)*

## Features
* **Hybrid Architecture:** FastAPI orchestrates logic, while a compiled C++17 extension handles $O(1)$ graph mutations.  
* **Dual Algorithms:** switches between **Weighted BFS** (Local/Deterministic) and **Personalized PageRank** (Global/Probabilistic) strategies.  
* **Smart Caching:** implements a 'Cache-Aside' pattern using Redis (Local or Upstash) to serve frequent requests in <1ms, with automatic SSL handling for cloud environments.  
* **Self-Healing State:** serializes the C++ graph to a binary blob (graph.bin) for $O(1)$ startup.Automatically detects corruption/empty states and falls back to a **SQL Rebuild** to ensure data integrity.  
* **Content-Aware Scoring:** dynamically boosts graph edge weights based on user genre preferences.  
* **Waterfall Strategy:** cascades from Graph Algo $\\to$ Global Trending $\\to$ Catalog to ensure zero empty states.
* **Graceful Persistence:** automatically captures graph state changes on server shutdown (SIGTERM), syncing the in-memory graph to Postgres to survive container restarts.
* **Cloud-Native:** fully Dockerized single-container architecture that auto-configures for Local (SQLite/Local Redis) or Production (Supabase/Upstash) environments via environment variables.  

---  

## Architechture  
The system uses a single-container hybrid approach for maximum efficiency:  
1. **Compute Layer (C++):** A custom-built graph engine (using Pybind11) handles memory-intensive graph traversals (BFS, Personalized PageRank) in milliseconds.  
2. **API Layer (Python):** FastAPI handles HTTP requests, authentication, and orchestrates the C++ module.
3. **Storage (Supabase/Postgres):** Persists all user interactions (Likes/Clicks).
4. **Cache (Upstash/Redis):** Caches recommendation results for instant retrieval.
5. **State Management:** The graph state is computed in memory and snapshotted to the database on server shutdown.
  
---  

## **Project Structure**
```pqsql
graphrec-engine/  
│  
├── .dockerignore           # Docker build exclusions  
├── Dockerfile              # Multi-stage build (Compiles C++ & Runs Python)  
├── docker-compose.yml      # Orchestrates Backend, Frontend, and Redis  
│
├── render.yaml             # Render.com Deployment Blueprint
│
├── backend/                # FastAPI Orchestrator  
│   ├── recommender\*.so    # Compiled C++ Module  
│   ├── graph.bin           # Binary Graph Snapshot (Fast Load)  
│   │  
│   └── app/  
│       ├── main.py         # App Entry: Handles Binary Loading & DB Sync  
│       ├── config.py       # Configures SQLite/Postgres & Redis URLs  
│       ├── api/            # Endpoints (Interactions, Recommendations)  
│       ├── core/           # Redis Client & C++ Wrapper  
│       └── db/             # SQL Models & CRUD  
│  
├── cpp\_engine/            # High-Performance Core  
│   ├── include/            # Headers  
│   └── src/  
│       ├── RecommendationEngine.cpp  # BFS, PageRank, & Serialization Logic  
│       └── bindings.cpp    # Pybind11 hooks  
│  
├── frontend/               # Client Application  
│   ├── index.html          # Main UI
│   ├── recommendations.html  
│   └── js/app.js           # API Logic & State Management  
│  
└── docs/                   # Documentation
    ├── architecture.md             
    ├── algorithms.md               
    └── complexity.md               
```  
  
---  

## **Quick Start(Local Docker)**  
**1. Clone & Configure**  
```bash
git clone [https://github.com/YOUR_USERNAME/GraphRec.git](https://github.com/YOUR_USERNAME/GraphRec.git)
cd GraphRec

# Create environment file
touch backend/.env
```
**2. Set up Environment Variables**  
Add your credentials to `backend/.env`  
```bash
DATABASE_URL="postgresql://postgres.[PROJECT]:[PASSWORD]@aws-0-[REGION][.pooler.supabase.com:6543/postgres](https://.pooler.supabase.com:6543/postgres)"
REDIS_URL="redis://localhost:6379/0" # Or your Upstash URL
```
**3. Run**  
```bash
docker-compose up --build
```
Access the app at http://localhost:8000.  

  
