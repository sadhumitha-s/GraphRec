#include <iostream>
#include <cassert>
#include <vector>
#include <algorithm>
#include "../../cpp_engine/include/RecommendationEngine.h"

// Helper to check if a vector contains a specific item
bool contains(const std::vector<int>& vec, int item) {
    return std::find(vec.begin(), vec.end(), item) != vec.end();
}

void test_basic_similarity() {
    std::cout << "Running test_basic_similarity..." << std::endl;
    RecommendationEngine engine;

    // Scenario:
    // User 1 likes Item 10.
    // User 2 likes Item 10 and Item 20.
    // User 1 should be recommended Item 20 because they share Item 10 with User 2.

    engine.add_interaction(1, 10, 1000); // Shared item
    engine.add_interaction(2, 10, 1001); // Shared item
    engine.add_interaction(2, 20, 1002); // Target item

    std::vector<int> recs = engine.recommend(1, 5);

    assert(!recs.empty() && "Recommendations should not be empty");
    assert(recs[0] == 20 && "User 1 should be recommended Item 20");
    
    std::cout << "PASSED" << std::endl;
}

void test_exclude_seen_items() {
    std::cout << "Running test_exclude_seen_items..." << std::endl;
    RecommendationEngine engine;

    // Scenario:
    // User 1 likes Item A and Item B.
    // User 2 likes Item A and Item B.
    // User 1 should NOT be recommended Item B, because they already saw it.

    engine.add_interaction(1, 100, 1000);
    engine.add_interaction(1, 200, 1000); // User 1 already saw 200
    
    engine.add_interaction(2, 100, 1000);
    engine.add_interaction(2, 200, 1000);
    engine.add_interaction(2, 300, 1000); // New item

    std::vector<int> recs = engine.recommend(1, 5);

    assert(!contains(recs, 100) && "Should not recommend Item 100 (seen)");
    assert(!contains(recs, 200) && "Should not recommend Item 200 (seen)");
    assert(contains(recs, 300) && "Should recommend Item 300");

    std::cout << "PASSED" << std::endl;
}

void test_metrics() {
    std::cout << "Running test_metrics..." << std::endl;
    RecommendationEngine engine;

    engine.add_interaction(1, 50, 100);
    engine.add_interaction(2, 60, 100);

    assert(engine.get_user_count() == 2);
    assert(engine.get_item_count() == 2);
    assert(engine.get_edge_count() == 2);

    std::cout << "PASSED" << std::endl;
}

int main() {
    try {
        test_basic_similarity();
        test_exclude_seen_items();
        test_metrics();
        std::cout << "\nAll C++ tests passed successfully!" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Test failed with exception: " << e.what() << std::endl;
        return 1;
    }
    return 0;
}