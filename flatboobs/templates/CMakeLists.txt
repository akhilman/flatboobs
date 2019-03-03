cmake_minimum_required (VERSION 3.10)

project ({{ project_name }})

set(PROJECT_NAME {{ project_name }})

set(CMAKE_CXX_STANDARD 17)
list(APPEND CMAKE_CXX_FLAGS -Wall)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find dependencies
find_package(pybind11 CONFIG REQUIRED)
find_package(Flatbuffers REQUIRED)
find_package(FlatBoobs REQUIRED)

set(FLATBOOBS_EXEC "python" -m flatboobs)
set(FLATC_EXEC "flatc")

set(SCHEMA_PATHS
    "{{ schema_paths|map("relative_path", output_dir)|join(";") }}")
set(SCHEMA_INCLUDE_PATHS
    "{{ include_paths|map("relative_path", output_dir)|join(";") }}")

# Define functions
function(make_serializer schema_files)
    set(base_names)
    set(gen_headers)
    set(gen_py_headers)
    set(gen_py_sources)
    set(gen_py_modsources)
    foreach(name ${schema_files})
        string(REGEX REPLACE "^.*/([^/]+)\.fbs$" "\\1" name ${name})
        list(APPEND base_names ${name})
        list(APPEND gen_headers "${PROJECT_BINARY_DIR}/${name}_generated.h")
        list(APPEND gen_py_headers "${PROJECT_BINARY_DIR}/${name}_generated_py.h")
        list(APPEND gen_py_sources "${PROJECT_BINARY_DIR}/${name}_generated_py.cc")
        list(APPEND gen_py_modsources "${PROJECT_BINARY_DIR}/${name}.cc")
    endforeach(name)

    add_custom_command(
        OUTPUT ${gen_headers}
        DEPENDS ${schema_files}
        COMMAND ${FLATC_EXEC} --cpp -o ${PROJECT_BINARY_DIR} ${schema_files}
        WORKING_DIRECTORY ${PROJECT_BINARY_DIR}
        )
    add_custom_command(
        OUTPUT ${gen_py_headers} ${gen_py_sources} ${gen_py_modsources}
        DEPENDS ${source_files} ${gen_headers}
        COMMAND ${FLATBOOBS_EXEC} serializer -o ${PROJECT_BINARY_DIR}
            ${schema_files}
        WORKING_DIRECTORY ${PROJECT_BINARY_DIR}
        )

    add_library(${PROJECT_NAME} STATIC ${gen_py_sources})
    target_link_libraries(${PROJECT_NAME} PRIVATE flatbuffers flatboobs)
    target_include_directories(${PROJECT_NAME} PRIVATE ${PYTHON_INCLUDE_DIRS})
    target_include_directories(${PROJECT_NAME} PUBLIC
        $<BUILD_INTERFACE:${PROJECT_BINARY_DIR}>
        $<INSTALL_INTERFACE:include>)

    foreach(name ${base_names})
        pybind11_add_module(${name} MODULE "${name}.cc")
        target_link_libraries(
            ${name} PRIVATE flatbuffers flatboobs ${PROJECT_NAME})
    endforeach(name)

endfunction(make_serializer)

set(schema_files)
foreach(schema_path ${SCHEMA_PATHS})
    file(GLOB new_schema_files ${schema_path}/*.fbs)
    list(APPEND schema_files ${new_schema_files})
endforeach(schema_path)
make_serializer("${schema_files}")

message("It works" ${SCHEMA_FILES})
