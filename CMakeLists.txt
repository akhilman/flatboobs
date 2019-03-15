cmake_minimum_required (VERSION 3.10)

project (FlatBoobs)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_CXX_STANDARD 17)
list(APPEND CMAKE_CXX_FLAGS -Wall)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find dependencies
find_package(pybind11 CONFIG REQUIRED)
find_package(Flatbuffers REQUIRED)

# set(PyBind11_SRC_Dir third_party/pybind11)
# add_subdirectory(${PyBind11_SRC_Dir})
#
# set(FlatBuffers_SRC_Dir third_party/flatbuffers)
# set(FLATBUFFERS_BUILD_TESTS OFF CACHE BOOL "Disable Flatbuffers tests")
# set(FLATBUFFERS_BUILD_FLATC OFF CACHE BOOL "Disable Flatbuffers flatc")
# set(FLATBUFFERS_BUILD_FLATHASH OFF CACHE BOOL "Disable Flatbuffers flathash")
# add_subdirectory(${FlatBuffers_SRC_Dir})
#
# set(FlatBuffers_CPP_Compiler_SRCS
#   ${FlatBuffers_SRC_Dir}/src/idl_gen_cpp.cpp
#   ${FlatBuffers_SRC_Dir}/src/idl_gen_general.cpp
#   ${FlatBuffers_SRC_Dir}/src/idl_gen_grpc.cpp
#   ${FlatBuffers_SRC_Dir}/grpc/src/compiler/schema_interface.h
#   ${FlatBuffers_SRC_Dir}/grpc/src/compiler/cpp_generator.h
#   ${FlatBuffers_SRC_Dir}/grpc/src/compiler/cpp_generator.cpp
# )

# add_library(flatbuffers_compiler STATIC ${FlatBuffers_CPP_Compiler_SRCS})
# target_include_directories(
#   flatbuffers_compiler PUBLIC ${FlatBuffers_SRC_Dir}/grpc)
# target_link_libraries(flatbuffers_compiler PUBLIC flatbuffers)

# Link with releative path
# set(CMAKE_INSTALL_RPATH "$ORIGIN")
# set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)

# Build modules

add_library(flatboobs STATIC src/container.cpp)
target_link_libraries(flatboobs PRIVATE flatbuffers)
target_include_directories(flatboobs PRIVATE ${PYTHON_INCLUDE_DIRS})
target_include_directories(flatboobs PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>)

pybind11_add_module(idl MODULE src/idl.cpp)
target_link_libraries(idl PRIVATE flatbuffers)
include_directories(idl PRIVATE include)

pybind11_add_module(flatboobs-mod MODULE src/flatboobs.cpp)
set_target_properties(flatboobs-mod PROPERTIES OUTPUT_NAME flatboobs)
target_link_libraries(flatboobs-mod PRIVATE flatbuffers flatboobs)
include_directories(flatboobs-mod PRIVATE include)

# Install
install(TARGETS idl LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX})
install(TARGETS flatboobs-mod LIBRARY DESTINATION ${CMAKE_INSTALL_PREFIX})
install(TARGETS flatboobs
    EXPORT FlatBoobsConfig
    ARCHIVE DESTINATION ${CMAKE_INSTALL_PREFIX}
    PUBLIC_HEADER DESTINATION ${CMAKE_INSTALL_PREFIX}/include)
install(DIRECTORY include DESTINATION ${CMAKE_INSTALL_PREFIX})

install(EXPORT FlatBoobsConfig
    DESTINATION cmake
    EXPORT_LINK_INTERFACE_LIBRARIES
    )

# Put compile_commands.json to package directory
install(
  FILES "${PROJECT_BINARY_DIR}/compile_commands.json"
  DESTINATION "${CMAKE_SOURCE_DIR}"
  )

# Sample
# pybind11_add_module(
#   monster_generated_py MODULE flatboobs/sample/monster/monster_generated_py.cpp)
# target_link_libraries(monster_generated_py PRIVATE flatbuffers flatboobs)
# install(TARGETS monster_generated_py DESTINATION sample/monster)
