
from libc.stdint cimport int16_t, int32_t
from libcpp cimport bool

cdef extern from "acoustic_indicators.h":
    ctypedef struct AcousticIndicatorsData:
      pass
    # Imports definitions from a c header file
    void ai_InitAcousticIndicatorsData(AcousticIndicatorsData* data)
    void ai_FreeAcousticIndicatorsData(AcousticIndicatorsData* data)
    AcousticIndicatorsData* ai_NewAcousticIndicatorsData()
    int ai_GetMaximalSampleSize(const AcousticIndicatorsData* data)
    bool ai_AddSample(AcousticIndicatorsData* data, int32_t sample_len, const int16_t* sample_data, float* laeq, float ref_pressure, bool a_filter)
