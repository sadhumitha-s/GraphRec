#include "../include/RecommendationEngine.h"

RecommendationEngine::RecommendationEngine() {}

void RecommendationEngine::add_interaction(int user_id, int item_id, long timestamp) {
    // Add forward edge: User -> Item
    user_items[user_id].push_back(item_id);
    
    // Add backward edge: Item -> User
    item_users[item_id].push_back(user_id);
}

bool RecommendationEngine::has_interacted(int user_id, int item_id) {
    if (user_items.find(user_id) == user_items.end()) return false;
    const auto& items = user_items[user_id];
    // In a production system, user_items values might be a set for O(1) lookup,
    // but vector is faster for iteration which is our primary op.
    for (int id : items) {
        if (id == item_id) return true;
    }
    return false;
}

std::vector<int> RecommendationEngine::recommend(int target_user_id, int k) {
    // Step 0: Edge case - new user
    if (user_items.find(target_user_id) == user_items.end()) {
        return {}; 
    }

    // Target user's history
    const std::vector<int>& target_history = user_items[target_user_id];
    
    // Use a set for O(1) lookup of items to exclude (already seen)
    std::unordered_set<int> seen_items(target_history.begin(), target_history.end());

    // Map to store candidate item scores: ItemID -> Score
    std::unordered_map<int, double> item_scores;

    // --- Step 1: Find Similar Users (BFS Depth 2) ---
    // Traversal: TargetUser -> Items -> OtherUsers
    
    for (int item_id : target_history) {
        // Who else bought this?
        if (item_users.find(item_id) == item_users.end()) continue;
        
        const std::vector<int>& neighbors = item_users[item_id];
        
        for (int neighbor_id : neighbors) {
            if (neighbor_id == target_user_id) continue;

            // --- Step 2: Score Candidate Items from Neighbors ---
            // Traversal: OtherUser -> OtherItems
            if (user_items.find(neighbor_id) == user_items.end()) continue;
            
            const std::vector<int>& candidate_items = user_items[neighbor_id];
            
            for (int candidate : candidate_items) {
                // Ignore items the target user has already seen
                if (seen_items.count(candidate)) continue;

                // Simple Scoring: +1 for every path leading to this item.
                // This effectively counts how many "similar users" interacted with this candidate.
                // Advanced: You could weight this by (1 / neighbors.size()) to penalize popular items.
                item_scores[candidate] += 1.0;
            }
        }
    }

    // --- Step 3: Rank Results ---
    // Convert map to vector of pairs for sorting
    std::vector<std::pair<int, double>> ranked_candidates;
    ranked_candidates.reserve(item_scores.size());
    
    for (const auto& kv : item_scores) {
        ranked_candidates.push_back(kv);
    }

    // Sort by score descending
    std::sort(ranked_candidates.begin(), ranked_candidates.end(),
              [](const std::pair<int, double>& a, const std::pair<int, double>& b) {
                  return a.second > b.second; 
              });

    // Extract top K
    std::vector<int> results;
    for (int i = 0; i < std::min((int)ranked_candidates.size(), k); ++i) {
        results.push_back(ranked_candidates[i].first);
    }

    return results;
}

void RecommendationEngine::rebuild(const std::vector<Interaction>& data) {
    user_items.clear();
    item_users.clear();
    for (const auto& i : data) {
        add_interaction(i.user_id, i.item_id, i.timestamp);
    }
}

int RecommendationEngine::get_user_count() const { return user_items.size(); }
int RecommendationEngine::get_item_count() const { return item_users.size(); }
long RecommendationEngine::get_edge_count() const { 
    long edges = 0;
    for(auto const& [key, val] : user_items) {
        edges += val.size();
    }
    return edges;
}