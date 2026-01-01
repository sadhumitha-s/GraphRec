# **Recommendation Algorithms**

This system utilizes a **Memory-Based Collaborative Filtering** approach implemented via **Bipartite Graph Traversal**. Instead of using matrix factorization or neural networks, we treat the recommendation problem as a "Link Prediction" problem on a graph.

## **The Graph Model**

The data is modeled as a **Bipartite Graph** consisting of two sets of nodes:

1. **User Nodes** ($U$)  
2. **Item Nodes** ($I$)

An edge $E$ exists between $u \\in U$ and $i \\in I$ if User $u$ has interacted with Item $i$.

(User 1\) \----+  
             |  
             \+---- (Item A)  
             |  
(User 2\) \----+---- (Item B)

## **The Algorithm: "Who also liked this?"**

We generate recommendations for a **Target User** by performing a Breadth-First Search (BFS) of depth 2 (or 3 steps depending on how you count).

### **Step-by-Step Execution**

1. **Input**: Target User ID ($u\_t$).  
2. **Level 1 Traversal (User History)**:  
   * Retrieve all items $I\_{history}$ connected to $u\_t$.  
   * $I\_{history} \= \\{ i \\mid (u\_t, i) \\in E \\}$  
3. **Level 2 Traversal (Similar Users)**:  
   * Find all users who have interacted with items in $I\_{history}$.  
   * These are "Neighbors".  
   * $U\_{neighbors} \= \\{ u \\mid (u, i) \\in E, i \\in I\_{history}, u \\neq u\_t \\}$  
4. **Level 3 Traversal (Candidate Items)**:  
   * Find items interacted with by the Neighbors.  
   * $I\_{candidates} \= \\{ i \\mid (u, i) \\in E, u \\in U\_{neighbors} \\}$  
5. **Filtering & Scoring**:  
   * **Filter**: Remove items that are already in $I\_{history}$ (items the user has already seen).  
   * **Score**: Count the frequency of occurrence (or path count).  
   * $Score(i) \= \\sum\_{u \\in U\_{neighbors}} \\mathbb{1}((u, i) \\in E)$  
   * *Intuition*: If 5 similar users liked Item X, and only 1 liked Item Y, Item X is a stronger recommendation.  
6. **Sorting**:  
   * Sort candidates by Score (Descending).  
   * Return top $K$.

## **Why C++?**

While this logic is simple to write in Python, Python's overhead for object iteration and dictionary lookups makes it slow for large graphs.

* **Python**: Overhead of interpreting bytecode for every loop iteration.  
* **C++**: Compiled to machine code. std::vector and std::unordered\_map provide cache-friendly, $O(1)$ average time complexity access patterns.