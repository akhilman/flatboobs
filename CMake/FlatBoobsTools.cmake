function(flatboobs_add_schema target)

  find_package(Python REQUIRED COMPONENTS Interpreter)
  find_package(Flatbuffers REQUIRED)

  set(options)
  cmake_parse_arguments(ARG "${options}" "" "" ${ARGN})
  set(schema_files ${ARG_UNPARSED_ARGUMENTS})

  set(output_dir ${CMAKE_BINARY_DIR}/${target})
  set(header_files)
  foreach(schema ${schema_files})
    string(REGEX REPLACE "^.*/([^/]+)\.fbs$" "\\1" name ${schema})
    list(APPEND header_files ${output_dir}/${name}_flatboobs.hpp)
  endforeach(schema)

  add_custom_target("${target}_make_directory" ALL
    COMMAND ${CMAKE_COMMAND} -E make_directory ${output_dir}
    )

  add_custom_command(
    OUTPUT ${header_files}
    COMMAND ${Python_EXECUTABLE} -m flatboobs lazy --header-only -o ${output_dir} ${schema_files}
    WORKING_DIRECTORY ${output_dir}
    )
  add_custom_target("${target}_generate"
    DEPENDS "${target}_make_directory" SOURCES ${header_files})

  add_library(${target} INTERFACE)
  add_dependencies(${target} "${target}_generate")
  target_include_directories(${target} INTERFACE ${output_dir})
  target_link_libraries(${target} INTERFACE flatbuffers)

endfunction(flatboobs_add_schema)
