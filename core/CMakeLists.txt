cmake_minimum_required(VERSION 2.8)

# Definitions
set(PROJECT_NAME coresensor)

#project(cense_coder)
project(${PROJECT_NAME})

include_directories (include)
#-DFIXED_POINT=16 -Dkiss_fft_scalar=double
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -std=c99 -Dkiss_fft_scalar=float")

set(SOURCE_FILES src/acoustic_indicators.c
                 src/kiss_fft.c
				 src/kiss_fftr.c
   )

add_library(coresensor ${SOURCE_FILES})


#------------#
#    TEST 1
#------------#

# Data files
set(TEST_DATA_DIR "${PROJECT_BINARY_DIR}/Testing")
file(COPY test/speak_32000Hz_16bitsPCM_10s.raw test/ref38dB_48000Hz_32bitsPCM.raw test/ref94dB_48000Hz_32bitsPCM.raw test/sinus1khz_32000Hz_24bitsPCM_2s.raw
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


#------------#
#    TEST 2
#------------#

# Test executable and folder
set(CORESENSOR_TESTS2
test/test_fft.c)


add_executable(TEST_coresensor2 ${CORESENSOR_TESTS2})

if(UNIX AND NOT APPLE)
    target_link_libraries (TEST_coresensor2
    coresensor m)
else()
    target_link_libraries (TEST_coresensor2
    coresensor)
endif()

set_property(TARGET TEST_coresensor2 PROPERTY FOLDER "tests")

# Add to test suite
enable_testing()
add_test( NAME coresensor
    WORKING_DIRECTORY ${TEST_DATA_DIR}
    COMMAND TEST_coresensor )
add_test( NAME coresensor2
    WORKING_DIRECTORY ${TEST_DATA_DIR}
  COMMAND TEST_coresensor2 )
