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
#   ${FlatBuffers_SRC_Dir}/grpc/src/compiler/cpp_generator.cc
# )

# add_library(flatbuffers_compiler STATIC ${FlatBuffers_CPP_Compiler_SRCS})
# target_include_directories(
#   flatbuffers_compiler PUBLIC ${FlatBuffers_SRC_Dir}/grpc)
# target_link_libraries(flatbuffers_compiler PUBLIC flatbuffers)

# Link with releative path
# set(CMAKE_INSTALL_RPATH "$ORIGIN")
# set(CMAKE_BUILD_WITH_INSTALL_RPATH TRUE)

include_directories(include)

# Build modules
pybind11_add_module(idl src/idl.cc)
target_link_libraries(idl PRIVATE flatbuffers)

pybind11_add_module(flatboobs src/flatboobs.cc)
target_link_libraries(idl PRIVATE flatbuffers)

# Install
install(TARGETS idl LIBRARY DESTINATION flatboobs/)
install(TARGETS flatboobs LIBRARY DESTINATION flatboobs/)

install(DIRECTORY include DESTINATION flatboobs)

# Put compile_commands.json to package directory
install(
  FILES "${PROJECT_BINARY_DIR}/compile_commands.json"
  DESTINATION "${CMAKE_SOURCE_DIR}"
  )
