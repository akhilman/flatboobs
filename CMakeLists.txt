cmake_minimum_required (VERSION 3.10)

project (FlatBoobs)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_CXX_STANDARD 17)
list(APPEND CMAKE_CXX_FLAGS -Wall)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find dependencies
find_package(pybind11 CONFIG REQUIRED)
find_package(Flatbuffers REQUIRED)

# add_subdirectory(third_party/pybind11)

# set(FLATBUFFERS_BUILD_TESTS OFF CACHE BOOL "Disable Flatbuffers tests")
# set(FLATBUFFERS_BUILD_FLATC OFF CACHE BOOL "Disable Flatbuffers flatc")
# set(FLATBUFFERS_BUILD_FLATHASH OFF CACHE BOOL "Disable Flatbuffers flathash")
# add_subdirectory(third_party/flatbuffers)

# Link with releative path
# set(CMAKE_INSTALL_RPATH "$ORIGIN")
# set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)

# Build modules
pybind11_add_module(idl src/idl.cc)
target_link_libraries(idl PUBLIC flatbuffers)

install(TARGETS idl DESTINATION ./flatboobs/)
install(FILES "${PROJECT_BINARY_DIR}/compile_commands.json" DESTINATION "${CMAKE_SOURCE_DIR}")
