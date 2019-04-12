function(flatboobs_add_schema target)

  # Requirements
  find_package(Python REQUIRED COMPONENTS Interpreter)
  find_package(Flatbuffers REQUIRED)

  # Parse args
  set(options HEADER_ONLY SHARED)
  cmake_parse_arguments(ARG "${options}" "" "" ${ARGN})
  set(schema_files ${ARG_UNPARSED_ARGUMENTS})

  # Get list of schema names
  execute_process(
    COMMAND
      ${Python_EXECUTABLE} -m flatboobs list ${schema_files}
    OUTPUT_VARIABLE
      schema_names
    )
  string(REPLACE "\n" ";" schema_names "${schema_names}")

  # make output directory
  set(output_dir ${CMAKE_CURRENT_BINARY_DIR}/generated/)
  add_custom_target("${target}_make_directory" ALL
    COMMAND ${CMAKE_COMMAND} -E make_directory ${output_dir}
    )

  ### C++ ###

  # Make list of C++ headers and sources
  set(header_files)
  set(source_files)

  foreach(schema ${schema_files})
    string(REGEX REPLACE "^.*/([^/]+)\.fbs$" "\\1" name ${schema})
    list(APPEND header_files ${output_dir}/include/${target}/${name}.hpp)
    if(NOT ARG_HEADER_ONLY)
      list(APPEND source_files ${output_dir}/src/${target}/${name}.cpp)
    endif()
  endforeach(schema)

  # Add command and target to generate C++ headers and sources
  if(ARG_HEADER_ONLY)
    set(boobs_args --header-only)
  else()
    set(boobs_args --no-header-only)
  endif()
  add_custom_command(
    OUTPUT
      ${header_files}
      ${source_files}
    DEPENDS
      ${schema_files}
      "${target}_make_directory"
    COMMAND
      ${Python_EXECUTABLE} -m flatboobs
        cpp ${boobs_args} -o ${output_dir} ${target} ${schema_files}
    WORKING_DIRECTORY
      ${output_dir}
    )
  add_custom_target(
    "${target}_generate"
    SOURCES
      ${header_files}
      ${source_files}
    )

  # Setup C++ library
  if(ARG_HEADER_ONLY)
    add_library(${target} INTERFACE)
    target_include_directories(${target} INTERFACE ${output_dir}/include)
  elseif(ARG_SHARED)
    add_library(${target} SHARED ${source_files})
    target_include_directories(${target} PUBLIC ${output_dir}/include)
  else()
    add_library(${target} STATIC ${source_files})
    target_include_directories(${target} PUBLIC ${output_dir}/include)
  endif()
  add_dependencies(${target} "${target}_generate")
  target_link_libraries(${target} INTERFACE flatbuffers)

endfunction(flatboobs_add_schema)
