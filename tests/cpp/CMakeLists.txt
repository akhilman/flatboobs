cmake_minimum_required (VERSION 3.10)

if(NOT DEFINED PROJECT_NAME)
  project (FlatBoobs_tests)
  find_package(FlatBoobs REQUIRED)
else()
  include(${CMAKE_SOURCE_DIR}/CMake/FlatBoobsTools.cmake)
endif()

set(CMAKE_CXX_STANDARD 17)
enable_testing()

find_package(Boost REQUIRED COMPONENTS unit_test_framework)
find_package(Flatbuffers REQUIRED)

# schema
set(schema_files)
file(GLOB schema_files ../../schema/test/*.fbs)
flatboobs_add_schema(flatboobs_test_schema ${schema_files})

# tests
file(GLOB test_sources ./*.cpp)

set(test_exec)
foreach(test_src ${test_sources})
  get_filename_component(test_name ${test_src} NAME_WE)
  add_executable(${test_name} ${test_src})
  target_link_libraries(${test_name} Boost::unit_test_framework)
  target_link_libraries(${test_name} flatboobs_test_schema)
  target_compile_definitions(${test_name} PRIVATE BOOST_TEST_DYN_LINK)
  add_test(NAME ${test_name} COMMAND ${test_name})
  list(APPEND test_exec ${test_name})
endforeach(test_src)
add_custom_target(check COMMAND ${CMAKE_CTEST_COMMAND} DEPENDS ${test_exec})
