cmake_minimum_required (VERSION 3.10)

project (FlatBoobs)

set(CMAKE_CXX_STANDARD 17)

# Find dependencies
find_package(pybind11 CONFIG REQUIRED)
find_package(Flatbuffers REQUIRED)

# Build modules
pybind11_add_module(idl src/idl.cc)
target_link_libraries(idl PRIVATE flatbuffers::flatbuffers_shared)
