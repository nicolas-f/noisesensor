/*
* BSD 3-Clause License
*
* Copyright (c) 2018, Ifsttar Wi6labs LS2N
* All rights reserved.
*
* Redistribution and use in source and binary forms, with or without
* modification, are permitted provided that the following conditions are met:
*
*  Redistributions of source code must retain the above copyright notice, this
*   list of conditions and the following disclaimer.
*
*  Redistributions in binary form must reproduce the above copyright notice,
*   this list of conditions and the following disclaimer in the documentation
*   and/or other materials provided with the distribution.
*
*  Neither the name of the copyright holder nor the names of its
*   contributors may be used to endorse or promote products derived from
*   this software without specific prior written permission.
*
* THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
* AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
* IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
* DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
* FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
* DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
* SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
* CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
* OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
* OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*
*/


#include <inttypes.h>
#include <math.h>
#include <stdbool.h>


#ifndef ACOUSTIC_INDICATORS_H_
#define ACOUSTIC_INDICATORS_H_

//number of third octave
#define AI_NB_BAND             29
// Note that only the sample rate 32khz is supported for (A) weigting.
#define AI_SAMPLING_RATE (32000)
// Analyse using Fast rate (125 ms)
#define AI_WINDOW_SIZE (4000)
#define AI_WINDOW_FFT_SIZE (4000)
#define AI_WINDOWS_SIZE (AI_SAMPLING_RATE / AI_WINDOW_SIZE)

#define AI_PI 3.141592653589793238462643383279502884197169399375105820974944

typedef struct  {
    int32_t window_cursor;
    float_t window_data[AI_WINDOW_SIZE];
    float_t* window_fft_data; // FFt rms
    int32_t windows_count;
    float_t windows[AI_WINDOWS_SIZE];
    float_t spectrum[AI_WINDOWS_SIZE][AI_NB_BAND];
    bool a_filter;
    bool has_spectrum;
    bool window;
    float_t ref_pressure;
    float_t tukey_alpha;
    float_t last_leq_slow;
    float_t last_leq_fast;
} AcousticIndicatorsData;

enum AI_FEED {AI_FEED_WINDOW_OVERFLOW = -1, //Exceed window array size
              AI_FEED_IDLE = 0,
              AI_FEED_COMPLETE = 1, //if a complete 1s LAeq has been computed, variable last_leq_slow and last_leq_fast can be read,
              AI_FEED_FAST = 2, //if a 125ms LAeq has been computed, variable last_leq_fast can be read
             };
/**
 * Init struct for acoustic indicators
 * @param data Acoustic indicators object
 * @param a_filter Compute A weighting
 * @param Compute leq for each third octaves
 */
void ai_InitAcousticIndicatorsData(AcousticIndicatorsData* data, bool a_filter, bool spectrum, float_t ref_pressure, bool window);

/**
 * Free struct for acoustic indicators
 */
void ai_FreeAcousticIndicatorsData(AcousticIndicatorsData* data);

/**
 * Change tukey alpha. Must be between 0 and 1
 */
void ai_SetTukeyAlpha(AcousticIndicatorsData* data, float_t tukey_alpha);

/**
 * Create a new instance of acoustic indicators
 */
AcousticIndicatorsData* ai_NewAcousticIndicatorsData(void);

/**
 * @param data instance of this struct, create an empty struct on first use
 */
int ai_GetMaximalSampleSize(const AcousticIndicatorsData* data);

/**
 * Add sample to the processing chain
 * @param[in,out] data instance of this struct, create an empty struct on first use
 * @param[in] sample_data sample content to add
 * @param[in] sample_len sample length of sample_data. Must be < than ai_get_maximal_sample_size
 * @param[out] laeq 1s laeq value if the return is true
 * @return Message code
 */
int ai_AddSample(AcousticIndicatorsData* data, int sample_len, const int16_t* sample_data);

/**
 * @brief ai_get_band_leq Compute band frequencies
 * @param data Acoustic indicators object
 * @param band_id Band identifier 0-AI_NB_BAND
 * @return Frequency value in dB, dB(A) if a_filter=true
 */
float ai_get_band_leq(AcousticIndicatorsData* data, int band_id);
/**
 * @brief ai_get_frequency Get frequency in hertz
 * @param band_id Band identifier 0-AI_NB_BAND
 * @return Frequency in hertz
 */
float ai_get_frequency(int band_id);

/**
 * @brief ai_get_leq_slow Used when ai_AddSample return AI_FEED_COMPLETE
 * @return value in dB, dB(A) if a_filter=true
 */
float ai_get_leq_slow(AcousticIndicatorsData* data);

/**
 * @brief ai_get_leq_slow Used when ai_AddSample return AI_FEED_COMPLETE or AI_FEED_FAST
 * @return value in dB, dB(A) if a_filter=true
 */
float ai_get_leq_fast(AcousticIndicatorsData* data);
/**
 * @brief ai_get_leq_band_fast Used when ai_AddSample return AI_FEED_COMPLETE or AI_FEED_FAST
 * @param band_id Band identifier 0-AI_NB_BAND
 * @return value in dB, dB(A) if a_filter=true
 */
float ai_get_leq_band_fast(AcousticIndicatorsData* data, int band_id);

#endif
