#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "../include/RecommendationEngine.h"

namespace py = pybind11;

PYBIND11_MODULE(recommender, m) {
    m.doc() = "C++ Graph-Based Recommendation Engine";

    py::class_<Interaction>(m, "Interaction")
        .def(py::init<int, int, long>())
        .def_readwrite("user_id", &Interaction::user_id)
        .def_readwrite("item_id", &Interaction::item_id)
        .def_readwrite("timestamp", &Interaction::timestamp);

    py::class_<RecommendationEngine>(m, "Engine")
        .def(py::init<>())
        .def("add_interaction", &RecommendationEngine::add_interaction)
        .def("remove_interaction", &RecommendationEngine::remove_interaction)
        // NEW: Expose set_item_genre
        .def("set_item_genre", &RecommendationEngine::set_item_genre)
        // UPDATED: recommend now takes a list of ints
        .def("recommend", &RecommendationEngine::recommend, 
             py::arg("target_user_id"), py::arg("k"), py::arg("preferred_genres") = std::vector<int>())

        // --- NEW: Save to disk bindings ---     
        .def("save_model", &RecommendationEngine::save_model)
        .def("load_model", &RecommendationEngine::load_model)

        .def("rebuild", &RecommendationEngine::rebuild)
        .def("get_user_count", &RecommendationEngine::get_user_count)
        .def("get_item_count", &RecommendationEngine::get_item_count)
        .def("get_edge_count", &RecommendationEngine::get_edge_count);
}