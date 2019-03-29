function(flatboobs_add_schema target)

  find_package(Python REQUIRED COMPONENTS Interpreter)
  find_package(Flatbuffers REQUIRED)

  set(options HEADER_ONLY SHARED)
  cmake_parse_arguments(ARG "${options}" "" "" ${ARGN})
  set(schema_files ${ARG_UNPARSED_ARGUMENTS})

  set(output_dir ${CMAKE_BINARY_DIR}/${target})
  set(header_files)
  set(source_files)
  foreach(schema ${schema_files})
    string(REGEX REPLACE "^.*/([^/]+)\.fbs$" "\\1" name ${schema})
    list(APPEND header_files ${output_dir}/${name}_flatboobs.hpp)
    if(NOT ARG_HEADER_ONLY)
      list(APPEND source_files ${output_dir}/${name}_flatboobs.cpp)
    endif()
  endforeach(schema)

  add_custom_target("${target}_make_directory" ALL
    COMMAND ${CMAKE_COMMAND} -E make_directory ${output_dir}
    )

  add_custom_command(
    OUTPUT
      ${header_files}
      ${source_files}
    COMMAND
      ${Python_EXECUTABLE} -m flatboobs -o ${output_dir} ${schema_files}
    WORKING_DIRECTORY
      ${output_dir}
    )
  add_custom_target(
    "${target}_generate"
    DEPENDS
      "${target}_make_directory"
    SOURCES
      ${header_files}
      ${source_files}
    )

  if(ARG_HEADER_ONLY)
    add_library(${target} INTERFACE)
    add_dependencies(${target} "${target}_generate")
  elseif(ARG_SHARED)
    add_library(${target} SHARED ${source_files})
  else()
    add_library(${target} STATIC ${source_files})
  endif()
  target_link_libraries(${target} INTERFACE flatbuffers)
  target_include_directories(${target} INTERFACE ${output_dir})

endfunction(flatboobs_add_schema)
