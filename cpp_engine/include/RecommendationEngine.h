#pragma once

#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <string>
#include <algorithm>
#include <iostream>
#include <ctime>
#include <cmath>

struct Interaction {
    int user_id;
    int item_id;
    long timestamp;
};

class RecommendationEngine {
private:
    // CHANGED: Adjacency Lists now store {ID, Timestamp} pairs
    // Maps User ID -> List of {Item ID, Timestamp}
    std::unordered_map<int, std::vector<std::pair<int, long>>> user_items;
    
    // Maps Item ID -> List of {User ID, Timestamp}
    std::unordered_map<int, std::vector<std::pair<int, long>>> item_users;

    bool has_interacted(int user_id, int item_id);

    // Helper to calculate decay
    double calculate_decay_score(long interaction_time, long current_time);

public:
    RecommendationEngine();
    
    void add_interaction(int user_id, int item_id, long timestamp);
    std::vector<int> recommend(int target_user_id, int k);
    void rebuild(const std::vector<Interaction>& data);
    
    int get_user_count() const;
    int get_item_count() const;
    long get_edge_count() const;
};