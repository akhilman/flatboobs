cmake_minimum_required (VERSION 3.10)

set(CMAKE_CXX_STANDARD 17)
enable_testing()

find_package(Boost COMPONENTS unit_test_framework REQUIRED)
find_package(Flatbuffers REQUIRED)
find_package(FlatBoobs REQUIRED)

# schema
set(schema_files)
file(GLOB schema_files ../../schema/test/*.fbs)
flatboobs_add_schema(test_schema ${schema_files})

file(GLOB test_sources ./*.cpp)

link_libraries(libboost_unit_test_framework.a)
link_libraries(flatbuffers flatboobs test_schema)
foreach(test_src ${test_sources})
  get_filename_component(test_name ${test_src} NAME_WE)
  add_executable(${test_name} ${test_src})
  add_test(NAME ${test_name} COMMAND ${test_name})
endforeach(test_src)
