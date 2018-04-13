/*
* BSD 3-Clause License
*
* Copyright (c) 2018, Ifsttar
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
#define AI_WINDOW_FFT_SIZE (4096)
#define AI_WINDOWS_SIZE (AI_SAMPLING_RATE / AI_WINDOW_SIZE)

typedef struct  {
    int32_t window_cursor;
    float_t window_data[AI_WINDOW_SIZE];
    float_t* window_fft_data; // FFt rms
    int32_t windows_count;
	float_t windows[AI_WINDOWS_SIZE];
    float_t spectrum[AI_WINDOWS_SIZE][AI_NB_BAND];
    bool a_filter;
    bool has_spectrum;
    float_t ref_pressure;
    float_t last_leq_slow;
    float_t last_leq_fast;
} AcousticIndicatorsData;

enum AI_FEED {AI_WINDOW_OVERFLOW = -1, //Exceed window array size
              AI_FEED_IDLE = 0,
              AI_FEED_COMPLETE = 1, //if a complete 1s LAeq has been computed, variable laeq can be read,
              AI_FEED_FAST = 2, //if a 125ms LAeq has been computed, variable laeq can be read
             };
/**
 * Init struct for acoustic indicators
 * @param data Acoustic indicators object
 * @param a_filter Compute A weighting
 * @param Compute leq for each third octaves
 */
void ai_InitAcousticIndicatorsData(AcousticIndicatorsData* data, bool a_filter, bool spectrum, float_t ref_pressure);

/**
 * Free struct for acoustic indicators
 */
void ai_FreeAcousticIndicatorsData(AcousticIndicatorsData* data);

/**
 * Create a new instance of acoustic indicators
 */
AcousticIndicatorsData* ai_NewAcousticIndicatorsData();

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
 * @brief ai_get_frequency Compute band frequencies
 * @param data Acoustic indicators object
 * @param band_id Band identifier 0-NB_BAND
 * @return Frequency value in Hz
 */
float ai_get_frequency(AcousticIndicatorsData* data, int band_id);

#endif
