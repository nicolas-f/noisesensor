
from libc.stdint cimport int16_t, int32_t
from libcpp cimport bool

cdef extern from "acoustic_indicators.h":
    ctypedef struct AcousticIndicatorsData:
      pass
    # Imports definitions from a c header file
    void ai_InitAcousticIndicatorsData(AcousticIndicatorsData* data, bool a_filter, bool spectrum, float ref_pressure)
    void ai_FreeAcousticIndicatorsData(AcousticIndicatorsData* data)
    AcousticIndicatorsData* ai_NewAcousticIndicatorsData()
    int ai_GetMaximalSampleSize(const AcousticIndicatorsData* data)
    int ai_AddSample(AcousticIndicatorsData* data, int sample_len, const int16_t* sample_data)
    float ai_get_leq_slow(AcousticIndicatorsData* data)
    float ai_get_leq_fast(AcousticIndicatorsData* data)
    float ai_get_leq_band_fast(AcousticIndicatorsData* data, int32_t band_id)
