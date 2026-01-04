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
    // User -> {Item, Timestamp}
    std::unordered_map<int, std::vector<std::pair<int, long>>> user_items;
    // Item -> {User, Timestamp}
    std::unordered_map<int, std::vector<std::pair<int, long>>> item_users;
    
    // NEW: Item ID -> Genre ID mapping
    std::unordered_map<int, int> item_genres;

    bool has_interacted(int user_id, int item_id);
    double calculate_decay_score(long interaction_time, long current_time);

public:
    RecommendationEngine();
    
    void add_interaction(int user_id, int item_id, long timestamp);
    void remove_interaction(int user_id, int item_id);
    
    // NEW: Set metadata
    void set_item_genre(int item_id, int genre_id);
    
    // NEW: Accepts preferred_genres vector
    std::vector<int> recommend(int target_user_id, int k, const std::vector<int>& preferred_genres);
    
    void rebuild(const std::vector<Interaction>& data);
    int get_user_count() const;
    int get_item_count() const;
    long get_edge_count() const;
};