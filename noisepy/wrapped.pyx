cimport cython
from libcpp cimport bool
from libc.stdint cimport int16_t, int32_t

DEF AI_SAMPLING_RATE = 32000
DEF AI_WINDOW_SIZE = 1000
DEF AI_WINDOWS_SIZE = AI_SAMPLING_RATE / AI_WINDOW_SIZE

cdef struct AcousticIndicatorsData:
    int window_cursor
    float window_data[AI_WINDOW_SIZE]
    int windows_count
    float windows[AI_WINDOWS_SIZE]

cdef extern from "acoustic_indicators.h":
    # Imports definitions from a c header file
    void ai_NewAcousticIndicatorsData(AcousticIndicatorsData* data)
    int ai_GetMaximalSampleSize(const AcousticIndicatorsData* data)
    bool ai_AddSample(AcousticIndicatorsData* data, int32_t sample_len, const int16_t* sample_data, float* laeq, float ref_pressure, bool a_filter)


