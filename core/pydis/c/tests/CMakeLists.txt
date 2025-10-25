cmake_minimum_required(VERSION 3.14)

# Force conda Python paths if in conda environment
if(DEFINED ENV{CONDA_PREFIX})
    set(PYTHON_INCLUDE_DIRS $ENV{CONDA_PREFIX}/include/python3.6m)
    set(PYTHON_LIBRARIES $ENV{CONDA_PREFIX}/lib/libpython3.6m.so)
    set(PYTHONLIBS_FOUND TRUE)
else()
    find_package(PythonLibs)
endif()
if(PYTHONLIBS_FOUND)
    add_executable(test_calforce)
    include_directories(${PYTHON_INCLUDE_DIRS})

    target_sources(test_calforce PRIVATE test_calforce.c)

    add_compile_definitions("SOURCE_ROOT=${CMAKE_SOURCE_DIR}")

    target_link_libraries(test_calforce ${PYTHON_LIBRARIES})
else()
    message("skips building core/pydis/c/tests/")
endif(PYTHONLIBS_FOUND)


