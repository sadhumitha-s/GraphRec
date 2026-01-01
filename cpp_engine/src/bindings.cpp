#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "../include/RecommendationEngine.h"

namespace py = pybind11;

PYBIND11_MODULE(recommender, m) {
    m.doc() = "C++ Graph-Based Recommendation Engine using Pybind11";

    py::class_<Interaction>(m, "Interaction")
        .def(py::init<int, int, long>())
        .def_readwrite("user_id", &Interaction::user_id)
        .def_readwrite("item_id", &Interaction::item_id)
        .def_readwrite("timestamp", &Interaction::timestamp);

    py::class_<RecommendationEngine>(m, "Engine")
        .def(py::init<>())
        .def("add_interaction", &RecommendationEngine::add_interaction, 
             "Add a single user-item interaction")
        .def("recommend", &RecommendationEngine::recommend, 
             "Get top K recommendations for a user")
        .def("rebuild", &RecommendationEngine::rebuild, 
             "Rebuild graph from a list of interactions")
        .def("get_user_count", &RecommendationEngine::get_user_count)
        .def("get_item_count", &RecommendationEngine::get_item_count)
        .def("get_edge_count", &RecommendationEngine::get_edge_count);
}