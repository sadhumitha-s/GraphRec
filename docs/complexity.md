# **Complexity Analysis**

This document details the theoretical performance of the C++ Core Engine.

## **Definitions**

* $V\_U$: Number of Users.  
* $V\_I$: Number of Items.  
* $E$: Total Number of Interactions (Edges).  
* $H\_{avg}$: Average history size per user (Average degree of User nodes).  
* $P\_{avg}$: Average popularity per item (Average degree of Item nodes).

## **1\. Space Complexity**

The graph is stored using Adjacency Lists (Hash Maps of Vectors).

* **User Map**: Stores $V\_U$ keys. The sum of all vector sizes is $E$.  
* **Item Map**: Stores $V\_I$ keys. The sum of all vector sizes is $E$.

Total Memory Usage:

$$O(V\_U \+ V\_I \+ 2E) \\approx O(E)$$  
Since the number of interactions usually far exceeds the number of users or items, space complexity scales linearly with the number of interactions.

## **2\. Time Complexity**

### **A. Add Interaction (add\_interaction)**

* Operation: user\_map\[u\].push\_back(i) and item\_map\[i\].push\_back(u).  
* Complexity: $O(1)$ (Amortized).  
  * std::unordered\_map lookup is average $O(1)$.  
  * std::vector push\_back is amortized $O(1)$.

### **B. Recommendation (recommend)**

The traversal explores the local neighborhood of the target user.

1. **History Retrieval**: Iterate over target user's items.  
   * Cost: $O(H\_{user})$  
2. **Neighbor Discovery**: For each item in history, iterate over users who liked it.  
   * Cost: $O(H\_{user} \\times P\_{item\\\_avg})$  
3. **Candidate Scoring**: For each neighbor, iterate over their history.  
   * Cost: $O(H\_{user} \\times P\_{item\\\_avg} \\times H\_{neighbor\\\_avg})$

Worst Case:  
In the worst case (dense graph), this is roughly $O(|E|)$.  
Average Case (Sparse Graph):  
Real-world interaction graphs are highly sparse. The complexity is proportional to the number of paths of length 3 originating from the user.

$$O(N\_{paths})$$  
This is significantly faster than Matrix Factorization training $(O(n_{epochs} \times E \times k))$ or calculating full Cosine Similarity $(O(V_U^2))$.

### **C. Ranking**

* Sorting candidates. Let $C$ be the number of unique candidate items found.  
* Cost: $O(C \\log C)$.

## **Scalability Limits**

* **100k Interactions**: Instant (\< 1ms).  
* **1M Interactions**: Very Fast (\< 10ms).  
* **10M Interactions**: Fast (\< 100ms).  
* **100M+ Interactions**: Memory becomes the bottleneck (RAM usage). At this scale, distributed graph databases (like Neo4j) or Spark are required.
