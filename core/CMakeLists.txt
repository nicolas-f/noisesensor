cmake_minimum_required(VERSION 2.8)

# Definitions
set(PROJECT_NAME coresensor)

#project(cense_coder)
project(${PROJECT_NAME})

include_directories (include)

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=c99")

set(SOURCE_FILES src/acoustic_indicators.c
   )

add_library(coresensor ${SOURCE_FILES})


#------------#
#    TEST 1
#------------#

# Data files
set(TEST_DATA_DIR "${PROJECT_BINARY_DIR}/Testing")
file(COPY test/speak_32000Hz_16bitsPCM_10s.raw test/speak_44100Hz_16bitsPCM_10s.raw
    DESTINATION ${TEST_DATA_DIR})

# Test executable and folder
set(CORESENSOR_TESTS
     test/test_acoustic_indicators.c)


add_executable(TEST_coresensor ${CORESENSOR_TESTS})

if(UNIX AND NOT APPLE)
    target_link_libraries (TEST_coresensor
    coresensor m)
else()
    target_link_libraries (TEST_coresensor
    coresensor)
endif()

set_property(TARGET TEST_coresensor PROPERTY FOLDER "tests")


# Add to test suite
enable_testing()
add_test( NAME coresensor
    WORKING_DIRECTORY ${TEST_DATA_DIR}
    COMMAND TEST_coresensor )
