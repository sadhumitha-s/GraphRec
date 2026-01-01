#pragma once

#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <string>
#include <algorithm>
#include <iostream>

// Represents a single user-item interaction
struct Interaction {
    int user_id;
    int item_id;
    long timestamp;
};

class RecommendationEngine {
private:
    // Graph Data Structures (Adjacency Lists)
    
    // Maps User ID -> List of Item IDs they interacted with
    std::unordered_map<int, std::vector<int>> user_items;
    
    // Maps Item ID -> List of User IDs who interacted with it
    std::unordered_map<int, std::vector<int>> item_users;

    // Helper to check if a user has already seen an item
    bool has_interacted(int user_id, int item_id);

public:
    RecommendationEngine();
    
    // 1. Add interaction to the graph (O(1) amortized)
    void add_interaction(int user_id, int item_id, long timestamp);
    
    // 2. The Core Algorithm: BFS-based Recommendation
    std::vector<int> recommend(int target_user_id, int k);
    
    // 3. Rebuild graph from bulk data
    void rebuild(const std::vector<Interaction>& data);
    
    // Metrics
    int get_user_count() const;
    int get_item_count() const;
    long get_edge_count() const;
};