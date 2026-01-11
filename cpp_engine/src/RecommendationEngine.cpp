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

// --- NEW: Personalized PageRank Implementation ---
std::vector<int> RecommendationEngine::recommend_ppr(int target_user_id, int k, int num_walks, int walk_depth) {
    if (user_items.find(target_user_id) == user_items.end()) return {};

    // 1. Setup Random Number Generation
    std::random_device rd;
    std::mt19937 gen(rd());
    
    // Map to store visit counts: ItemID -> Count
    std::unordered_map<int, int> visit_counts;
    
    // Identify items already seen by target (to exclude them later)
    std::unordered_set<int> seen_items;
    const auto& history = user_items[target_user_id];
    for(const auto& p : history) seen_items.insert(p.first);

    // 2. Perform Random Walks (Monte Carlo Simulation)
    for (int i = 0; i < num_walks; ++i) {
        int curr_user = target_user_id;
        int curr_item = -1;
        
        // Perform a single walk of specific depth
        // Pattern: User -> Item -> User -> Item ...
        for (int step = 0; step < walk_depth; ++step) {
            
            // A. Move User -> Item
            if (user_items.find(curr_user) == user_items.end()) break;
            const auto& u_items = user_items[curr_user];
            if (u_items.empty()) break;
            
            std::uniform_int_distribution<> dis_item(0, u_items.size() - 1);
            curr_item = u_items[dis_item(gen)].first;
            
            // If this is the end of the walk, record visit
            if (step == walk_depth - 1) {
                // Only count if not seen by target
                if (seen_items.find(curr_item) == seen_items.end()) {
                    visit_counts[curr_item]++;
                }
                break; 
            }

            // B. Move Item -> User
            if (item_users.find(curr_item) == item_users.end()) break;
            const auto& i_users = item_users[curr_item];
            if (i_users.empty()) break;

            std::uniform_int_distribution<> dis_user(0, i_users.size() - 1);
            curr_user = i_users[dis_user(gen)].first;
        }
    }

    // 3. Rank Results by Visit Count
    std::vector<std::pair<int, int>> ranked_candidates;
    ranked_candidates.reserve(visit_counts.size());
    
    for (const auto& kv : visit_counts) {
        ranked_candidates.push_back(kv);
    }

    // Sort Descending
    std::sort(ranked_candidates.begin(), ranked_candidates.end(),
              [](const std::pair<int, int>& a, const std::pair<int, int>& b) {
                  return a.second > b.second; 
              });

    // Extract Top K
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

// --- NEW: Save Memory to Disk ---
void RecommendationEngine::save_model(const std::string& filepath) {
    std::ofstream out(filepath, std::ios::binary);
    if (!out) {
        std::cerr << "Error: Cannot open file for writing: " << filepath << std::endl;
        return;
    }

    // 1. Save Genres
    size_t genre_size = item_genres.size();
    out.write(reinterpret_cast<const char*>(&genre_size), sizeof(genre_size));
    for (const auto& [item, genre] : item_genres) {
        out.write(reinterpret_cast<const char*>(&item), sizeof(item));
        out.write(reinterpret_cast<const char*>(&genre), sizeof(genre));
    }

    // 2. Save User Graph
    size_t user_size = user_items.size();
    out.write(reinterpret_cast<const char*>(&user_size), sizeof(user_size));
    for (const auto& [user, items] : user_items) {
        out.write(reinterpret_cast<const char*>(&user), sizeof(user));
        size_t vec_size = items.size();
        out.write(reinterpret_cast<const char*>(&vec_size), sizeof(vec_size));
        if (vec_size > 0) {
            out.write(reinterpret_cast<const char*>(items.data()), vec_size * sizeof(std::pair<int, long>));
        }
    }

    // 3. Save Item Graph
    size_t item_size = item_users.size();
    out.write(reinterpret_cast<const char*>(&item_size), sizeof(item_size));
    for (const auto& [item, users] : item_users) {
        out.write(reinterpret_cast<const char*>(&item), sizeof(item));
        size_t vec_size = users.size();
        out.write(reinterpret_cast<const char*>(&vec_size), sizeof(vec_size));
        if (vec_size > 0) {
            out.write(reinterpret_cast<const char*>(users.data()), vec_size * sizeof(std::pair<int, long>));
        }
    }
    
    out.close();
    std::cout << "[C++] Graph saved to " << filepath << std::endl;
}

// --- NEW: Load Memory from Disk ---
void RecommendationEngine::load_model(const std::string& filepath) {
    std::ifstream in(filepath, std::ios::binary);
    if (!in) throw std::runtime_error("Cannot open file for reading");

    user_items.clear();
    item_users.clear();
    item_genres.clear();

    // 1. Load Genres
    size_t genre_size;
    in.read(reinterpret_cast<char*>(&genre_size), sizeof(genre_size));
    for (size_t i = 0; i < genre_size; ++i) {
        int item, genre;
        in.read(reinterpret_cast<char*>(&item), sizeof(item));
        in.read(reinterpret_cast<char*>(&genre), sizeof(genre));
        item_genres[item] = genre;
    }

    // 2. Load User Graph
    size_t user_size;
    in.read(reinterpret_cast<char*>(&user_size), sizeof(user_size));
    for (size_t i = 0; i < user_size; ++i) {
        int user;
        size_t vec_size;
        in.read(reinterpret_cast<char*>(&user), sizeof(user));
        in.read(reinterpret_cast<char*>(&vec_size), sizeof(vec_size));
        
        std::vector<std::pair<int, long>> items(vec_size);
        if (vec_size > 0) {
            in.read(reinterpret_cast<char*>(items.data()), vec_size * sizeof(std::pair<int, long>));
        }
        user_items[user] = std::move(items);
    }

    // 3. Load Item Graph
    size_t item_size;
    in.read(reinterpret_cast<char*>(&item_size), sizeof(item_size));
    for (size_t i = 0; i < item_size; ++i) {
        int item;
        size_t vec_size;
        in.read(reinterpret_cast<char*>(&item), sizeof(item));
        in.read(reinterpret_cast<char*>(&vec_size), sizeof(vec_size));
        
        std::vector<std::pair<int, long>> users(vec_size);
        if (vec_size > 0) {
            in.read(reinterpret_cast<char*>(users.data()), vec_size * sizeof(std::pair<int, long>));
        }
        item_users[item] = std::move(users);
    }

    in.close();
    std::cout << "[C++] Graph loaded from " << filepath << std::endl;
}