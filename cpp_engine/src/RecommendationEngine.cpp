#include "../include/RecommendationEngine.h"

RecommendationEngine::RecommendationEngine() {}

double RecommendationEngine::calculate_decay_score(long interaction_time, long current_time) {
    if (interaction_time > current_time) return 1.0; 
    double diff_seconds = (double)(current_time - interaction_time);
    double diff_days = diff_seconds / 86400.0;
    double alpha = 0.05; 
    return 1.0 / (1.0 + (alpha * diff_days));
}

void RecommendationEngine::add_interaction(int user_id, int item_id, long timestamp) {
    user_items[user_id].push_back({item_id, timestamp});
    item_users[item_id].push_back({user_id, timestamp});
}

void RecommendationEngine::remove_interaction(int user_id, int item_id) {
    if (user_items.find(user_id) != user_items.end()) {
        auto& items = user_items[user_id];
        items.erase(std::remove_if(items.begin(), items.end(),
            [item_id](const std::pair<int, long>& p){ return p.first == item_id; }), items.end());
        if (items.empty()) user_items.erase(user_id);
    }
    if (item_users.find(item_id) != item_users.end()) {
        auto& users = item_users[item_id];
        users.erase(std::remove_if(users.begin(), users.end(),
            [user_id](const std::pair<int, long>& p){ return p.first == user_id; }), users.end());
        if (users.empty()) item_users.erase(item_id);
    }
}

// NEW: Store metadata
void RecommendationEngine::set_item_genre(int item_id, int genre_id) {
    item_genres[item_id] = genre_id;
}

// UPDATED: Now takes preferred_genres
std::vector<int> RecommendationEngine::recommend(int target_user_id, int k, const std::vector<int>& preferred_genres) {
    // Edge case handling...
    if (user_items.find(target_user_id) == user_items.end()) return {}; 

    long current_time = std::time(nullptr);
    const auto& target_history = user_items[target_user_id];
    std::unordered_set<int> seen_items;
    for(const auto& p : target_history) seen_items.insert(p.first);

    // Convert prefs to set for O(1) lookup
    std::unordered_set<int> pref_set(preferred_genres.begin(), preferred_genres.end());

    std::unordered_map<int, double> item_scores;

    // BFS Traversal
    for (const auto& [item_id, _] : target_history) {
        if (item_users.find(item_id) == item_users.end()) continue;
        const auto& neighbors = item_users[item_id];
        
        for (const auto& [neighbor_id, _] : neighbors) {
            if (neighbor_id == target_user_id) continue;
            if (user_items.find(neighbor_id) == user_items.end()) continue;
            
            const auto& candidate_items = user_items[neighbor_id];
            for (const auto& [candidate_id, timestamp] : candidate_items) {
                if (seen_items.count(candidate_id)) continue;

                // 1. Base Score (Time Decay)
                double score = calculate_decay_score(timestamp, current_time);
                
                // 2. Genre Boost
                // If the item's genre is in the user's preferred list, boost score by 1.5x
                if (item_genres.count(candidate_id)) {
                    int g_id = item_genres[candidate_id];
                    if (pref_set.count(g_id)) {
                        score *= 1.5; 
                    }
                }

                item_scores[candidate_id] += score;
            }
        }
    }

    // Rank
    std::vector<std::pair<int, double>> ranked_candidates;
    ranked_candidates.reserve(item_scores.size());
    for (const auto& kv : item_scores) ranked_candidates.push_back(kv);

    std::sort(ranked_candidates.begin(), ranked_candidates.end(),
              [](const std::pair<int, double>& a, const std::pair<int, double>& b) {
                  return a.second > b.second; 
              });

    std::vector<int> results;
    for (int i = 0; i < std::min((int)ranked_candidates.size(), k); ++i) {
        results.push_back(ranked_candidates[i].first);
    }
    return results;
}

// ... rebuild, get_user_count etc remain same ...
void RecommendationEngine::rebuild(const std::vector<Interaction>& data) {
    user_items.clear();
    item_users.clear();
    for (const auto& i : data) add_interaction(i.user_id, i.item_id, i.timestamp);
}
int RecommendationEngine::get_user_count() const { return user_items.size(); }
int RecommendationEngine::get_item_count() const { return item_users.size(); }
long RecommendationEngine::get_edge_count() const { 
    long edges = 0;
    for(auto const& [key, val] : user_items) edges += val.size();
    return edges;
}