cmake_minimum_required(VERSION 3.16.0)

execute_process(
  COMMAND git rev-parse --short HEAD
  WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
  OUTPUT_VARIABLE GIT_COMMIT_ID
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
add_definitions("-DGIT_COMMIT_ID=\"${GIT_COMMIT_ID}\"")

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(SpiraBot_main)

