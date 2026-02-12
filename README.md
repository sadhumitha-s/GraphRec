# **GraphRec Engine (Hybrid C++ & Python + GraphSAGE ML)**  
A high-performance Recommendation Engine featuring three complementary algorithms: a custom C++ graph engine (BFS, PageRank) and a trained GraphSAGE neural network on TMDb movie data. Combines deterministic graph traversal with learned embeddings for semantic recommendations.

[Live Demo](https://graphrec-engine.onrender.com)  
*(Note: App hosted on free tier, may spin down after inactivity. Please wait 30s for wakeup!)*

## Features
* **Tri-Algorithm Engine:** Switch seamlessly between **Weighted BFS** (Local/Deterministic), **Personalized PageRank** (Global/Probabilistic), and **GraphSAGE** (Learned Embeddings) on the recommendations page.
* **GraphSAGE ML Integration:** 2-layer heterogeneous graph neural network trained on ~2k TMDb movies (1995–2023, 7 genres) using Bayesian Personalized Ranking loss. Embeddings cached in-database; zero production API calls.
* **Hybrid Architecture:** FastAPI orchestrates all three engines; C++17 extension handles $O(1)$ graph mutations; PyTorch Geometric handles neural inference.  
* **Smart Caching:** Cache-Aside pattern using Redis (Local or Upstash) serves frequent BFS requests in <1ms with automatic SSL for cloud environments. GraphSAGE/PPR skip cache to allow real-time experimentation.  
* **Self-Healing State:** Serializes C++ graph to `graph.bin` for $O(1)$ startup. Auto-detects corruption and falls back to SQL Rebuild. GraphSAGE embeddings persist in `graphsage_items` table.  
* **Content-Aware Scoring:** Boosts graph edges based on user genre preferences; GraphSAGE similarity scores refined by user embedding composition.  
* **Waterfall Strategy:** Cascades from Algorithm Engine $\\to$ Global Trending $\\to$ Catalog to guarantee zero empty states.  
* **Graceful Persistence:** Captures graph state changes on SIGTERM, syncing in-memory graph to Postgres. ML embeddings auto-reload from DB on restart.  
* **Cloud-Native:** Single-container Docker with multi-stage build (C++ compile → Python runtime). Auto-configures for Local (SQLite/Local Redis) or Production (Supabase/Upstash).  
* **User Authentication & Authorization:** Supabase Auth (email/password, JWT HS256). Maps Supabase UUIDs to sequential graph user IDs. Guest mode for exploration; registered users edit own profiles.  
* **Role-Based Access Control:** `canEdit()` logic enforces `myId == viewingId`. Interactions require JWT. Read-only profile browsing for all.  
* **Dynamic Genre Preferences:** Users select genres; preferences stored and influence BFS scoring dynamically. Loaded on login; clearable anytime.

---  

## **Architecture**  
Single-container hybrid system with four compute layers:  
1. **Auth Layer (Supabase JWT HS256):** Registration/login, token verification, UUID→user_id mapping.  
2. **Graph Engine (C++17 + Pybind11):** BFS & PageRank traversals in <50ms. Serializes to `graph.bin` for persistence.  
3. **ML Engine (PyTorch Geometric):** GraphSAGE inference on cached embeddings. 64-dim vectors from bipartite user-item interaction graph.  
4. **API Layer (FastAPI):** Orchestrates three recommendation algorithms, enforces auth, manages Redis cache.  
5. **Storage (Supabase Postgres):** Profiles, interactions, preferences, and `graphsage_items` embeddings table.  
6. **Cache (Upstash/Redis):** BFS results cached 1-hour TTL; GraphSAGE/PPR uncached for flexibility.
7. **State Management:** The graph state is computed in memory and snapshotted to the database on server shutdown.

---  

## **Project Structure**
```pqsql
graphrec-engine/  
│  
├── .dockerignore                 # Docker build exclusions  
├── Dockerfile                    # Multi-stage build (Compiles C++ & Runs Python)  
├── docker-compose.yml            # Orchestrates Backend, Frontend, and Redis  
│
├── render.yaml                   # Render.com Deployment Blueprint
│
├── backend/                 
│   ├── recommender\*.so          # Compiled C++ Module  
│   ├── graph.bin                 # Binary Graph Snapshot   
│   │  
│   └── app/  
│       ├── main.py               # FastAPI entry point: Initializes app, loads graph.bin, syncs DB on startup, handles SIGTERM gracefully
│       ├── config.py             # Environment config loader: DATABASE_URL, REDIS_URL, SUPABASE secrets, TMDB_API_KEY
│       ├── api/
│       │   ├── recommend.py          # Core recommendation endpoint: Orchestrates BFS/PPR/GraphSAGE, implements 3-tier fallback (Graph → Trending → Catalog), manages Redis cache
│       │   ├── interactions.py       # POST/DELETE /interaction/: Like/unlike items, validate JWT, invalidate cache on user edits
|       |   └── metrics.py            # GET /metrics/: Returns graph stats (node count, edge count) for dashboard display
│       ├── core/                 
│       │   ├── recommender.py        # C++17 engine wrapper: Init graph from DB, call .recommend_bfs() and .recommend_ppr() via Pybind11, load/save graph.bin
|       |   ├── redis_client.py       # Redis client factory: Handles local vs. cloud (Upstash) connections, auto SSL for rediss://
|       |   └── security.py           # JWT verification: Decode Supabase HS256 tokens, extract user UUID, look up internal user_id, enforce auth on all mutation endpoints
│       ├── ml/
│       │   ├── tmdb_dataset.py       # Data pipeline: Fetch from TMDb API (rate-limited), build HeteroData graph with pseudo-users, return TMDbBundle (data, item_titles, embeddings)
│       │   ├── train_dataset.py      # CLI entry point: Load TMDb data, train GraphSAGE 30 epochs, save embeddings to DB via graphsage_store.py, print catalog matches
│       │   ├── graphsage_model.py    # Model definition: 2-layer HeteroConv (SAGEConv), 64-dim hidden, mean aggregation, ReLU + 0.2 dropout, outputs user/item embeddings
│       │   ├── training.py           # Training loop: BPR loss with 1:5 negative sampling, Adam optimizer (lr=1e-3), epoch logging
│       │   ├── graphsage_serving.py  # Inference engine: Load embeddings from DB (thread-safe cache), normalize titles, compute user embedding as mean of liked items, dot-product scoring, cold-start fallback to popularity
│       │   ├── graphsage_store.py    # Persistence layer: Save trained embeddings to graphsage_items table (tmdb_id, title, title_norm, embedding bytes, popularity), store embedding_dim in graphsage_meta
│       │   └── data/
│       │       └── tmdb_cache.jsonl      # Local JSONL file: ~2k movies
│       └── db/                    
│           ├── crud.py               # SQLAlchemy ORM: Profile (uuid→user_id), Interaction (user_id, item_id, timestamp), Item (catalog), UserPreference (genre_id), GraphSageItem (embeddings), GraphSnapshot (graph.bin)
|           ├── models.py             # SQL helpers: get_item_map(), get_user_interacted_ids(), set_user_preferences(), get_user_preference_ids(), get_popular_item_ids(), seed_items() (24-movie catalog)
|           └── session.py            # SQLAlchemy engine + SessionLocal: Configures connection pooling (pool_pre_ping, pool_recycle=300), disable prepared statements for Supabase PGBouncer
│  
├── cpp_engine/                   # High-Performance Core  
│   ├── include/                  # Headers  
│   └── src/  
│       ├── RecommendationEngine.cpp  # BFS, PageRank, & Serialization Logic  
│       └── bindings.cpp              # Pybind11 hooks  
│  
├── frontend/               
│   ├── index.html                 # Main UI (Discover page with Taste profile)
│   ├── recommendations.html       # Recommendations (For you) page
|   ├── login.html                 # Auth UI (Register & Login)
│   ├── css/styles.css             # Responsive glass-morphism design
│   └── js/app.js                  # API Logic, State Management, & Auth Flow  
│  
└── docs/                          # Documentation
    ├── architecture.md             
    ├── algorithms.md               
    └── complexity.md               
```  
  
---  

## **Three Recommendation Algorithms**

### **1. Weighted BFS** (Graph Traversal)
- Local, deterministic exploration from user's liked items.
- Boosts weights by user's genre preferences in real-time.
- **Latency:** <10ms | **Cache:** Yes (1 hour TTL)

### **2. Personalized PageRank** (Global Ranking)
- Probabilistic graph ranking with convergence after 10 iterations.
- Balances personalization vs. global popularity.
- **Latency:** 20–50ms | **Cache:** No (always live)

### **3. GraphSAGE** (Neural Embeddings)
- 2-layer heterogeneous graph neural network trained on TMDb.
- User embedding = mean of liked-item embeddings.
- Scores unseen items via dot product similarity.
- **Latency:** <5ms (in-memory lookup) | **Cache:** No (live inference)
- **Training:** 30 epochs, BPR loss, 1:5 negative sampling, Adam (lr=1e-3).

---  

## **Data Pipeline for GraphSAGE model**  
- Fetch & Cache: tmdb_dataset.py queries TMDb API once; caches to tmdb_cache.jsonl.
- Build Graph: Pseudo-users = (genre_name, page_num) tuples; creates bipartite graph.
- Train Model: training.py optimizes 2-layer GraphSAGE with BPR loss.
- Persist: graphsage_store.py writes 64-dim float32 embeddings to DB.
- Serve: graphsage_serving.py loads from DB on startup; no external calls at runtime.

---  

## **Model Metrics (Current Training)**  
- Dataset: ~2k TMDb movies (1995–2023), 7 genres (Action, Animation, Comedy, Crime, Drama, Horror, Sci-Fi).
- Training Loss: 0.7279 → 0.6302 → 0.6007 (30 epochs, healthy descent).
- Model Size: 64-dim embeddings × 2k items ≈ 512 KB.
- Cold-Start Fallback: Rank by TMDb popularity if user has no liked items.

---  

## **User Flow**

**Guest Mode (Anonymous)**
- Browse catalog, view all user profiles (read-only).
- Test all three recommendation algorithms.
- Cannot like/dislike or set preferences.

**Registered User (Authenticated)**
- Sign up via email/password; assigned sequential user ID (1, 2, 3, ...).
- Full edit access to own profile: like/dislike movies, select genre preferences.
- Preferences dynamically influence BFS & GraphSAGE scoring.
- Can browse other profiles in read-only mode.

**Permission Model**
- `canEdit()` = `(myId != null && myId == viewingId)`
- All interactions (POST/DELETE) protected by JWT.
- Profile data visible to all; modifications restricted to owner.

---  

## **Performance**  
| Operation | Latency | Notes |
|-----------|---------|-------|
| BFS Traversal | <10ms | Local graph, $O(V+E)$ |
| PageRank | 20–50ms | 10 iterations, sparsity-aware |
| GraphSAGE Inference | <5ms | In-memory embedding lookup + dot product |
| Redis Cache Hit (BFS) | <1ms | 1-hour TTL |
| Graph Load (snapshot) | <100ms | Binary deserialization |
| DB Sync (cold start) | <500ms | Replay all interactions |
| GraphSAGE Embeddings Load | <200ms | Load ~2k vectors from DB to memory |   

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
DATABASE_URL="postgresql://postgres.[PROJECT]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
REDIS_URL="redis://localhost:6379/0"
SUPABASE_URL="https://[PROJECT].supabase.co"
SUPABASE_ANON_KEY="eyJ..."
SUPABASE_JWT_SECRET="[JWT_SIGNING_SECRET]"
TMDB_API_KEY="your-tmdb-api-key"
```  

**3. Run**  
```bash
docker-compose up --build
```
Access the app at http://localhost:8000.  
  

  
