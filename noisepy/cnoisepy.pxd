
from libc.stdint cimport int16_t, int32_t, int8_t
from libcpp cimport bool

cdef extern from "acoustic_indicators.h":
    ctypedef struct AcousticIndicatorsData:
      pass
    cdef int AI_WINDOW_FFT_SIZE
    # Imports definitions from a c header file
    void ai_init_acoustic_indicators_data(AcousticIndicatorsData* data, bool a_filter, bool spectrum, float ref_pressure, bool window,int8_t sample_rate_index, const char* format, bool mono)
    void ai_free_acoustic_indicators_data(AcousticIndicatorsData* data)
    AcousticIndicatorsData* ai_NewAcousticIndicatorsData()
    int ai_GetMaximalSampleSize(const AcousticIndicatorsData* data)
    int ai_AddSample(AcousticIndicatorsData* data, int sample_len, const int8_t* sample_data)
    float ai_get_leq_slow(AcousticIndicatorsData* data)
    float ai_get_leq_fast(AcousticIndicatorsData* data)
    float ai_get_band_leq(AcousticIndicatorsData* data, int band_id)
    float ai_get_leq_band_fast(AcousticIndicatorsData* data, int32_t band_id)
    void ai_SetTukeyAlpha(AcousticIndicatorsData* data, float tukey_alpha)
    float ai_GetThinBandRMS(AcousticIndicatorsData* data, int32_t band)
