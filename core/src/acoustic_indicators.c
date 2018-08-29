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

#include "acoustic_indicators.h"
#include "third_octave_const.h"
#include <stdio.h>
#include <inttypes.h>
#include <math.h>
#include <string.h>
#include <stdlib.h>
#include "kiss_fft.h"

#ifndef MIN
#define MIN(a,b) (((a)<(b))?(a):(b))
#endif

#ifndef MAX
#define MAX(a,b) (((a)>(b))?(a):(b))
#endif

// int order = max(denominator.length, numerator.length);
#define ORDER (7)

#define AI_APPLY_FREQUENCY_BINS_FILTER
/**
 * Numerator coefficients of the A-weighting filter determined by means of a bilinear transform that converts
 * second-order section analog weights to second-order section digital weights.
 */
const float_t numerator_32khz[ORDER] = {0.34345834, -0.68691668, -0.34345834, 1.37383335, -0.34345834, -0.68691668, 0.34345834};
/**
 * Denominator coefficients of the A-weighting filter determined by means of a bilinear transform that converts
 * second-order section analog weights to second-order section digital weights.
 */
const float_t denominator_32khz[ORDER] = {1. , -3.65644604, 4.83146845, -2.5575975, 0.25336804, 0.12244303, 0.00676407};

int ai_GetMaximalSampleSize(const AcousticIndicatorsData* data) {
    if(!data->hann_window) {
        return AI_WINDOW_SIZE - (data->sample_index + AI_WINDOW_SIZE) % AI_WINDOW_SIZE;
    } else {
        return AI_WINDOW_OVERLAPING_SIZE - (data->sample_index + AI_WINDOW_OVERLAPING_SIZE) % AI_WINDOW_OVERLAPING_SIZE;
    }
}

int ai_AddSample(AcousticIndicatorsData* data, int sample_len, const int16_t* sample_data) {
    int i;
    if(sample_len > ai_GetMaximalSampleSize(data)) {
        return AI_FEED_WINDOW_OVERFLOW;
    }
    if(sample_len == 0) {
      return AI_FEED_IDLE;
    }
    // Copy data to buffer
    int window_cursor = data->sample_index % AI_WINDOW_SIZE;
    int window_copy_to = (data->sample_index + sample_len) % AI_WINDOW_SIZE;

    if(window_cursor < window_copy_to || window_copy_to == 0) {
        memcpy(&data->window_data[window_cursor], sample_data, sample_len * sizeof(int16_t));
    } else {
        // Copy begining part of data
        memcpy(&data->window_data[window_cursor], sample_data, (AI_WINDOW_SIZE - window_cursor) * sizeof(int16_t));
        // Copy end part of data
        //memcpy(&data->window_data, &sample_data[window_cursor], window_copy_to * sizeof(int16_t));
        memcpy(&data->window_data, &sample_data[AI_WINDOW_SIZE - window_cursor], window_copy_to * sizeof(int16_t));
    }
    //printf("cursor_global:%d cursor_window:%d copy_to:%d \n", data->sample_index, window_cursor, window_copy_to);
    data->sample_index += sample_len;
    if((data->hann_window && data->sample_index % AI_WINDOW_OVERLAPING_SIZE == 0) || (!data->hann_window && data->sample_index % AI_WINDOW_SIZE == 0)) {
        // Window is filled
        // Store a time contiuous window
        float_t continuous_window[AI_WINDOW_SIZE];
        // Copy begining part of data
        for(i = window_copy_to; i < AI_WINDOW_SIZE; i++) {
            continuous_window[i - window_copy_to] = data->window_data[i];
        }
        int last_part = AI_WINDOW_SIZE - window_copy_to;
        // Copy end part of data (most recent)
        for(i = 0; i < window_copy_to; i++) {
            continuous_window[i + last_part] = data->window_data[i];
        }
        if(data->hann_window) {
          // Apply hann window Filter to signal
          for(i=0; i<AI_WINDOW_SIZE; i++) {
            continuous_window[i] *= (float_t)((1.0-cos(2.0*AI_PI*(i+1)/(AI_WINDOW_SIZE+1)))*0.5);
          }
        }
		    // Compute A weighting
        if(data->a_filter) {
  				float_t weightedSignal[AI_WINDOW_SIZE];
  				// Filter delays
  				float_t z[ORDER-1][AI_WINDOW_SIZE];
          int idT;
    			for (idT = 0; idT < AI_WINDOW_SIZE; idT++) {
            // Avoid iteration idT=0 exception (z[0][idT-1]=0)
            weightedSignal[idT] = (numerator_32khz[0]*continuous_window[idT] + (idT == 0 ? 0 : z[0][idT-1]));
            // Avoid iteration idT=0 exception (z[1][idT-1]=0)
            z[0][idT] = (numerator_32khz[1]*continuous_window[idT] + (idT == 0 ? 0 : z[1][idT-1]) - denominator_32khz[1]*continuous_window[idT]);
            int k;
            for (k = 0; k<ORDER-2; k++){
              // Avoid iteration idT=0 exception (z[k+1][idT-1]=0)
              z[k][idT] = (numerator_32khz[k+1]*continuous_window[idT] + (idT ==0 ? 0 : z[k+1][idT-1]) - denominator_32khz[k+1]*weightedSignal[idT]);
            }
            z[ORDER-2][idT] = (numerator_32khz[ORDER-1]*continuous_window[idT] - denominator_32khz[ORDER-1] * weightedSignal[idT]);
          }
          for (idT = 0; idT < AI_WINDOW_SIZE; idT++){
            continuous_window[idT] = weightedSignal[idT];
          }
    		}
        // Compute spectrum
        if(data->has_spectrum) {

            kiss_fft_cfg cfg = kiss_fft_alloc(AI_WINDOW_FFT_SIZE, 0, NULL, NULL);

            kiss_fft_cpx buffer[AI_WINDOW_FFT_SIZE];

            // Append padding of 0
            memset(buffer, 0 , sizeof(kiss_fft_cpx) * AI_WINDOW_FFT_SIZE);

            // Convert short to kiss_fft_scalar type
            for(i=0; i < AI_WINDOW_SIZE; i++) {
                buffer[i].r = (kiss_fft_scalar) continuous_window[i];
            }

            kiss_fft_cpx fft_out[AI_WINDOW_FFT_SIZE];

            kiss_fft(cfg, buffer, fft_out);

            kiss_fft_free(cfg);

            // Compute RMS for each thin frequency bands
            const int band_limit = ai_f_band[AI_NB_BAND - 1][1];
            for(i=0; i< band_limit; i++) {
                data->window_fft_data[i] = fft_out[i].r * fft_out[i].r + fft_out[i].i * fft_out[i].i;
            }
            // Compute RMS for each third octave frequency bands by applying filters
            // Reset accumulator
            int id_third_octave;
            if(!data->hann_window || data->do_reset_fft_accumulator) {
              data->do_reset_fft_accumulator = false;
              //printf("Reset at %d data->spectrum[%d][*]\n",data->sample_index - sample_len, data->windows_count);
              for(id_third_octave = 0; id_third_octave < AI_NB_BAND; id_third_octave++) {
                data->spectrum[data->windows_count][id_third_octave] = 0;
              }
            }
            //printf("Accum at %d data->spectrum[%d][*]\n",data->sample_index - sample_len, data->windows_count);
            #ifdef AI_APPLY_FREQUENCY_BINS_FILTER
            for(id_third_octave = 0; id_third_octave < AI_NB_BAND; id_third_octave++) {
                double sumRms = 0;
                const int startSampleIndex = ai_f_band[id_third_octave][0];
                const int endSampleIndex = ai_f_band[id_third_octave][1];
                for(i=startSampleIndex; i <= endSampleIndex; i++) {
                    sumRms += ai_H_band[id_third_octave][i - startSampleIndex] * data->window_fft_data[i];
                }
                const double rms = (2. / AI_WINDOW_SIZE * sqrt(sumRms / 2));
                data->spectrum[data->windows_count][id_third_octave] += rms / data->ref_pressure;
            }
            #else
                double freqByCell = AI_SAMPLING_RATE / (double)AI_WINDOW_SIZE;
                int refFreq = 17; // 1000 hz
                for(id_third_octave = 0; id_third_octave < AI_NB_BAND; id_third_octave++) {
                    // Compute lower and upper value of third-octave
                    // NF-EN 61260
                    // base 10
                    double fCenter = pow(10, (id_third_octave - refFreq)/10.) * 1000;
                    double fLower = fCenter * pow(10, -1. / 20.);
                    double fUpper = fCenter * pow(10, 1. / 20.);
                    double sumRms = 0;
                    int cellFloor = (int)(ceil(fLower / freqByCell));
                    int cellCeil = MIN(AI_WINDOW_FFT_SIZE - 1, (int) (floor(fUpper / freqByCell)));
                    int cellLower = MIN(cellFloor, cellCeil);
                    int cellUpper = MAX(cellFloor, cellCeil);
                    for(int idCell = cellLower; idCell <= cellUpper; idCell++) {
                        sumRms += data->window_fft_data[idCell];
                    }
                    const float_t rms = sqrt(sumRms / 2) / (AI_WINDOW_SIZE / 2.);
                    data->spectrum[data->windows_count][id_third_octave] += rms / data->ref_pressure;
                }
            #endif
        }
    		// Compute RMS
    		float_t sampleSum = 0;
    		for(i=0; i < AI_WINDOW_SIZE; i++) {
                sampleSum += continuous_window[i] * continuous_window[i];
    		}
        if(data->hann_window) {
            data->hann_results[data->hann_results_cursor++] = sampleSum;
            if(data->hann_results_cursor >= AI_WINDOW_SUM_HANN_COUNT) {
              data->hann_results_cursor = 0;
            }
        }
        if(!data->hann_window || data->sample_index % (AI_WINDOW_OVERLAPING_SIZE * AI_WINDOW_SUM_HANN_COUNT) == 0) {
            if(data->hann_window) {
                // Compute sum of hann RMS
                sampleSum = 0;
                for(int i=0; i< AI_WINDOW_SUM_HANN_COUNT; i++) {
                    sampleSum += data->hann_results[i];
                }
                data->do_reset_fft_accumulator = true;
            }
            // Return a result to the user
            // Push window sum in windows struct data
            data->windows[data->windows_count++] = sampleSum;
            // Convert into dB(A)
            data->last_leq_fast = 10 * log10((double)data->windows[data->windows_count - 1] / (AI_WINDOW_SIZE) / (data->ref_pressure * data->ref_pressure));
            if(data->windows_count == AI_WINDOWS_SIZE) { // 1s computation complete
                // compute energetic average
                float_t sumWindows = 0;
                for(i=0; i<AI_WINDOWS_SIZE;i++) {
                    sumWindows+=data->windows[i];
                }
                // Convert into dB(A)
                data->last_leq_slow = 10 * log10((double)sumWindows / (AI_WINDOWS_SIZE * AI_WINDOW_SIZE) / (data->ref_pressure * data->ref_pressure));
                data->windows_count = 0;
                return AI_FEED_COMPLETE;
            } else { // 125ms complete
                return AI_FEED_FAST;
            }
        }
  	}
    return AI_FEED_IDLE;
}

AcousticIndicatorsData* ai_NewAcousticIndicatorsData(void) {
		AcousticIndicatorsData* p = malloc(sizeof(AcousticIndicatorsData));
		return p;
}

void ai_FreeAcousticIndicatorsData(AcousticIndicatorsData* data) {
    if(data->has_spectrum) {
        free(data->window_fft_data);
    }
}

void ai_InitAcousticIndicatorsData(AcousticIndicatorsData* data, bool a_filter, bool spectrum, float_t ref_pressure, bool hann_window)
{
	data->windows_count = 0;
    data->sample_index = 0;
    data->a_filter = a_filter;
    data->has_spectrum = spectrum;
    data->ref_pressure = ref_pressure;
    data->last_leq_fast = 0;
    data->last_leq_slow = 0;
    data->do_reset_fft_accumulator = true;
    data->hann_window = hann_window;
    memset(data->window_data, 0, AI_WINDOW_SIZE * sizeof(int16_t));
    if(spectrum) {
        data->window_fft_data = malloc(AI_WINDOW_FFT_SIZE * sizeof(float_t));
        memset(data->window_fft_data, 0, AI_WINDOW_FFT_SIZE * sizeof(float_t));
    } else {
        data->window_fft_data = NULL;
    }
}


float ai_get_band_leq(AcousticIndicatorsData* data, int band_id) {
    if(data->has_spectrum && band_id >= 0 && band_id < AI_NB_BAND) {
        int i;
        double sum = 0;
        int window_count = data->windows_count == 0 ? AI_WINDOWS_SIZE : data->windows_count;
        for(i=0; i < window_count; i++) {
          sum += data->spectrum[i][band_id];
        }
        return 20 * log10(sum / AI_WINDOWS_SIZE);
    } else {
        return 0.f;
    }
}


float ai_get_frequency(int band_id) {
    return ai_frequencies[band_id];
}

float ai_get_leq_slow(AcousticIndicatorsData* data) {
    return data->last_leq_slow;
}

float ai_get_leq_fast(AcousticIndicatorsData* data) {
    return data->last_leq_fast;
}

float ai_get_leq_band_fast(AcousticIndicatorsData* data, int band_id) {
    if(data->has_spectrum && band_id >= 0 && band_id < AI_NB_BAND) {
        int window_count = data->windows_count == 0 ? AI_WINDOWS_SIZE - 1 : data->windows_count - 1;
        return 20 * log10(data->spectrum[window_count][band_id]);
    } else {
        return 0.;
    }
}
