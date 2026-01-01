cmake_minimum_required(VERSION 3.10)
project(GraphRecommender)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Pybind11
find_package(pybind11 REQUIRED)

# Include directories
include_directories(include)

# Create the extension module
# "recommender" must match the name in PYBIND11_MODULE(recommender, m)
pybind11_add_module(recommender 
    src/RecommendationEngine.cpp 
    src/bindings.cpp
)

# Optimization flags
if(MSVC)
    target_compile_options(recommender PRIVATE /O2)
else()
    target_compile_options(recommender PRIVATE -O3 -march=native)
endif()