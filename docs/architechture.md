# **System Architecture**

## **High-Level Design**
```text
 [ Browser ] 
      ^
      | HTTP
      v
+-----------------------+       +------------------+
|    FastAPI Backend    | <-->  |   Redis Cache    | (Hot Data)
+----------+------------+       +------------------+
           |
           | Load / Save Snapshot
    +------+-------+-------------------------+
    |              |                         |
    v              v                         v
+-------+    +--------------------------+   +---------------------+
|  SQL  |    |   C++ Recommendation     |   |   Logic Layers      |
|  DB   |    |         Engine           |   | 1. Cache (Redis)    |
+-------+    | (In-Memory Graph)        |   | 2. Graph (BFS/PPR)  |
             +--------------------------+   | 3. SQL Fallback     |
                                            +---------------------+
```
---  

## **Data Flow**

### **1\. Read Path (Recommendations)**

1. **Check Cache**: Backend queries Redis for recs:user:{id}. If found, return instantly (\<1ms).  
2. **Algorithm Selection**: If cache miss, Backend calls C++ Engine using the selected strategy:  
   * **Weighted BFS**: Traverses neighbor history with Time-Decay \+ Genre Boosting.  
   * **PageRank**: Simulates 10,000 random walks to find global influence.  
3. **Fallback**: If C++ returns empty, query SQL for "Global Trending".  
4. **Write-Back**: Save the result to Redis (TTL 5 mins).

### **2\. Fast Startup (Binary Serialization)**

1. **Check DB**: Backend checks graph\_snapshots table for a binary blob.  
2. **Download**: If found, downloads bytes to local graph.bin.  
3. **Load**: C++ Engine maps graph.bin directly into memory structures (std::unordered\_map).  
   * *Result:* Startup time becomes independent of interaction count (Disk I/O speed vs DB Query speed).
