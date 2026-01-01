# **System Architecture**

## **Overview**

The Graph-Based Recommendation System is designed as a hybrid application that combines the ease of Python for API orchestration with the raw performance of C++ for graph computations. It follows a layered architecture where persistent storage is handled by a traditional SQL database, while real-time recommendations are served from an in-memory graph structure.

## **High-Level Design**

\[ User / Browser \]  
       |  
       | HTTP/JSON  
       v  
\+-----------------------+  
|    FastAPI Backend    |  \<--- Handles Auth, Validation, Routing  
|      (Python)         |  
\+----------+------------+  
           |  
           |  
    \+------+-------+  
    |              |  
    v              v  
\+-------+    \+--------------------------+  
| MySQL |    |   C++ Recommendation     |  
|  DB   |    |         Engine           |  
\+-------+    | (Compiled .so Extension) |  
             \+--------------------------+

## **Components**

### **1\. Frontend (Presentation Layer)**

* **Tech**: HTML5, CSS3, Vanilla JavaScript.  
* **Role**: Provides the user interface for logging in (simulated), viewing the catalog, interacting with items (Liking), and displaying recommendations.  
* **Communication**: Fetch API to talk to the Backend on port 8000\.

### **2\. Backend (Orchestration Layer)**

* **Tech**: Python 3, FastAPI, Uvicorn, SQLAlchemy.  
* **Role**:  
  * Exposes REST endpoints (/interaction, /recommend).  
  * Manages persistent data storage via SQLAlchemy.  
  * Acts as the bridge to the C++ engine using **pybind11**.  
* **Lifecycle**: On startup, it fetches all historical data from the Database and populates the C++ in-memory graph.

### **3\. Core Engine (Computation Layer)**

* **Tech**: C++17, STL (Standard Template Library).  
* **Role**:  
  * Maintains the graph structure in RAM.  
  * Executes the BFS traversal algorithms for recommendations.  
  * Optimized for high-throughput read operations.  
* **Interface**: Exposed to Python as a module named recommender.

### **4\. Database (Persistence Layer)**

* **Tech**: MySQL (Production) or SQLite (Dev/Test).  
* **Role**: Source of truth. If the server crashes, the C++ memory is wiped, but the DB persists. On restart, the graph is rebuilt from here.

## **Data Flow**

### **Write Path (User Likes an Item)**

1. Frontend sends POST /interaction {user\_id, item\_id}.  
2. FastAPI receives request.  
3. **Step A (Persistence)**: Interaction is saved to MySQL interactions table.  
4. **Step B (Memory)**: Interaction is passed to C++ engine.add\_interaction().  
5. C++ updates its unordered\_map adjacency lists immediately.

### **Read Path (Get Recommendations)**

1. Frontend sends GET /recommend/{user\_id}.  
2. FastAPI calls C++ engine.recommend(user\_id).  
3. C++ performs graph traversal and returns a list of item\_ids.  
4. FastAPI queries the database (or local cache) to convert item\_ids into full objects (Title, Category).  
5. JSON response is sent to Frontend.