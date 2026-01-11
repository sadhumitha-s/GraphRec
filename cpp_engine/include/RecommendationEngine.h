#pragma once

#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <string>
#include <algorithm>
#include <iostream>
#include <ctime>
#include <cmath>
#include <fstream> 
#include <random>

struct Interaction {
    int user_id;
    int item_id;
    long timestamp;
};

class RecommendationEngine {
private:
    std::unordered_map<int, std::vector<std::pair<int, long>>> user_items;
    std::unordered_map<int, std::vector<std::pair<int, long>>> item_users;
    std::unordered_map<int, int> item_genres;

    bool has_interacted(int user_id, int item_id);
    double calculate_decay_score(long interaction_time, long current_time);

public:
    RecommendationEngine();
    
    void add_interaction(int user_id, int item_id, long timestamp);
    void remove_interaction(int user_id, int item_id);
    void set_item_genre(int item_id, int genre_id);
    
    std::vector<int> recommend(int target_user_id, int k, const std::vector<int>& preferred_genres);

    std::vector<int> recommend_ppr(int target_user_id, int k, int num_walks, int walk_depth);

    void rebuild(const std::vector<Interaction>& data);
    
    // --- NEW: Serialization Methods ---
    void save_model(const std::string& filepath);
    void load_model(const std::string& filepath);
    
    int get_user_count() const;
    int get_item_count() const;
    long get_edge_count() const;
};