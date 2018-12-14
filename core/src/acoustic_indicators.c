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
#include "kiss_fftr.h"
#include <limits.h>

#ifndef MIN
#define MIN(a,b) (((a)<(b))?(a):(b))
#endif

#ifndef MAX
#define MAX(a,b) (((a)>(b))?(a):(b))
#endif

// int order = max(denominator.length, numerator.length);
#define ORDER (7)

// #define AI_APPLY_FREQUENCY_BINS_FILTER


/**
 * Numerator coefficients of the A-weighting filter determined by means of a bilinear transform that converts
 * second-order section analog weights to second-order section digital weights.
 */
const float_t a_filter_numerator[AI_NB_SUPPORTED_SAMPLES_RATES][ORDER] = {{0.34345834, -0.68691668, -0.34345834, 1.37383335, -0.34345834, -0.68691668, 0.34345834},
{ 1.        , -4.11304341,  6.55312175, -4.99084929,  1.7857373 , -0.2461906 ,  0.01122425 }};
/**
 * Denominator coefficients of the A-weighting filter determined by means of a bilinear transform that converts
 * second-order section analog weights to second-order section digital weights.
 */
const float_t a_filter_denominator[AI_NB_SUPPORTED_SAMPLES_RATES][ORDER] = {{1. , -3.65644604, 4.83146845, -2.5575975, 0.25336804, 0.12244303, 0.00676407},
{ 0.23430179, -0.46860358, -0.23430179,  0.93720717, -0.23430179, -0.46860358,  0.23430179 }};

int ai_get_maximal_sample_size(const AcousticIndicatorsData* data) {
	return (data->window_data_size - data->window_cursor) * ai_formats_bytes[data->format] * (data->mono ? 1 : 2);
}

int ai_add_sample(AcousticIndicatorsData* data, int sample_len, const int8_t* sample_data) {
    int i;
	if(sample_len > ai_get_maximal_sample_size(data)) {
        return AI_FEED_WINDOW_OVERFLOW;
    }
    if(AI_FORMAT_S16_LE == data->format) {
	    for(i=data->window_cursor; i < sample_len / ai_formats_bytes[data->format] + data->window_cursor; i++) {
		    data->window_data[i] = (int16_t)(sample_data[(i-data->window_cursor) * ai_formats_bytes[data->format] * (data->mono ? 1 : 2)]) / (float_t)SHRT_MAX;
	    }
    } else {
        for (i = data->window_cursor; i < sample_len / ai_formats_bytes[data->format] + data->window_cursor; i++) {
            data->window_data[i] = (int32_t)(sample_data[(i - data->window_cursor) * ai_formats_bytes[data->format] * (data->mono ? 1 : 2)]) / (float_t)INT_MAX;
        }    
    }
	data->window_cursor+=sample_len;
	if(data->window_cursor >= data->window_data_size) {
		data->window_cursor = 0;
		// Compute A weighting
        if(data->a_filter) {
				float_t* weightedSignal = malloc(sizeof(float_t) * data->window_data_size);
				// Filter delays
				//float_t z[ORDER-1][data->window_data_size];
                float_t* z = malloc(sizeof(float_t) * data->window_data_size * (ORDER - 1));
                int idT;
				for (idT = 0; idT < data->window_data_size; idT++){
                    // Avoid iteration idT=0 exception (z[0][idT-1]=0)
                    weightedSignal[idT] = (a_filter_denominator[data->sample_rate_index][0]*data->window_data[idT] + (idT == 0 ? 0 : z[idT-1]));
                    // Avoid iteration idT=0 exception (z[1][idT-1]=0)
                    z[idT] = (a_filter_numerator[data->sample_rate_index][1]*data->window_data[idT] +
                        (idT == 0 ? 0 : z[data->window_data_size + idT - 1]) - a_filter_denominator[data->sample_rate_index][1]*data->window_data[idT]);
                    int k;
                    for (k = 0; k<ORDER-2; k++){
                        // Avoid iteration idT=0 exception (z[k+1][idT-1]=0)
                        z[k*data->window_data_size+idT] = (a_filter_numerator[data->sample_rate_index][k+1]*data->window_data[idT] +
                            (idT ==0 ? 0 : z[(k+1)*data->window_data_size+idT-1]) - a_filter_denominator[data->sample_rate_index][k+1]*weightedSignal[idT]);
                    }
                    z[data->window_data_size * (ORDER-2) + idT] = (a_filter_numerator[data->sample_rate_index][ORDER-1]*data->window_data[idT]
                        - a_filter_denominator[data->sample_rate_index][ORDER-1] * weightedSignal[idT]);
                }
                free(z);
				for (idT = 0; idT < data->window_data_size; idT++){
					data->window_data[idT] = weightedSignal[idT];
				}
                free(weightedSignal);
		}
        // Compute spectrum
        if(data->has_spectrum) {

            kiss_fft_cfg cfg = kiss_fft_alloc(data->window_fft_data_size, 0, NULL, NULL);
            
            // Convert short to kiss_fft_scalar type and apply windowing
			data->energy_correction = 0;
            if(!data->window) {
			  data->energy_correction = data->window_data_size;
              memcpy(data->window_fft_data, data->window_data, sizeof(kiss_fft_scalar) * data->window_data_size);
              if(data->window_fft_data_size > data->window_data_size) {
                  memset(&data->window_fft_data[data->window_data_size], 0, sizeof(kiss_fft_scalar) * (data->window_fft_data_size - data->window_data_size));
              }
            } else {
              int index_begin_flat = (data->tukey_alpha / 2) * data->window_data_size;
              int index_end_flat = data->window_data_size - index_begin_flat;
							double window_value = 0;
              for(i=0; i < index_begin_flat; i++) {
								window_value = (0.5 * (1 + cos(2 * AI_PI / data->tukey_alpha * ((i / (float)data->window_data_size) - data->tukey_alpha / 2))));
								data->energy_correction += window_value * window_value;
                                data->window_fft_data[i] = (kiss_fft_scalar) data->window_data[i] * window_value;
              }
              // Flat part
							data->energy_correction += index_end_flat - index_begin_flat;
              for(i=index_begin_flat; i < index_end_flat; i++) {
                  data->window_fft_data[i] = (kiss_fft_scalar) data->window_data[i];
              }
              // End Hann part
              for(i=index_end_flat; i < data->window_data_size; i++) {
				window_value = (0.5 * (1 + cos(2 * AI_PI / data->tukey_alpha * ((i / (float)data->window_data_size) - 1 + data->tukey_alpha / 2))));
				data->energy_correction += window_value * window_value;
                data->window_fft_data[i] = (kiss_fft_scalar) data->window_data[i] * window_value;
              }
            }
			data->energy_correction = 1.0 / sqrt(data->energy_correction / data->window_data_size);
            kiss_fft_cpx* fft_out = malloc(sizeof(kiss_fft_cpx) * data->window_fft_data_size);

            kiss_fftr(cfg, data->window_fft_data, fft_out);

            kiss_fft_free(cfg);

            // Compute RMS for each thin frequency bands
            int fft_offset = data->window_fft_data_size - data->window_data_size;
            for(i=fft_offset; i < data->window_fft_data_size; i++) {
                data->window_fft_data[i-fft_offset] = fft_out[i].r * fft_out[i].r + fft_out[i].i * fft_out[i].i;
            }
            free(fft_out);
            // Compute RMS for each third octave frequency bands by applying filters
            int id_third_octave;
            double freqByCell = ai_supported_samples_rates[data->sample_rate_index] / data->window_data_size;
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
                int cellCeil = MIN(data->window_data_size - 1, (int) (floor(fUpper / freqByCell)));
                int cellLower = MIN(cellFloor, cellCeil);
                int cellUpper = MAX(cellFloor, cellCeil);
									int idCell;
                for(idCell = cellLower; idCell <= cellUpper; idCell++) {
                    sumRms += data->window_fft_data[idCell];
                }
                const float_t rms = (sqrt(sumRms / 2) / (data->window_data_size / 2.)) * data->energy_correction;
                data->spectrum[data->windows_count][id_third_octave] = 20 * log10(rms / data->ref_pressure);
            }
        }
		// Compute RMS
		float_t sampleSum = 0;
		for(i=0; i < data->window_data_size; i++) {
			sampleSum += (float_t)data->window_data[i] * (float_t)data->window_data[i];
		}
		// Push window sum in windows struct data
		data->windows[data->windows_count++] = sampleSum;
        // Convert into dB(A)
        data->last_leq_fast = 10 * log10((double)data->windows[data->windows_count - 1] / (data->window_data_size) / (data->ref_pressure * data->ref_pressure));
        if(data->windows_count == AI_WINDOWS_SIZE) { // 1s computation complete
            // compute energetic average
            float_t sumWindows = 0;
            for(i=0; i<AI_WINDOWS_SIZE;i++) {
                sumWindows+=data->windows[i];
            }
            // Convert into dB(A)
            data->last_leq_slow = 10 * log10((double)sumWindows / (AI_WINDOWS_SIZE * data->window_data_size) / (data->ref_pressure * data->ref_pressure));
            data->windows_count = 0;
            return AI_FEED_COMPLETE;
        } else { // 125ms complete
            return AI_FEED_FAST;
        }
	}
    return AI_FEED_IDLE;
}

AcousticIndicatorsData* ai_NewAcousticIndicatorsData(void) {
		AcousticIndicatorsData* p = malloc(sizeof(AcousticIndicatorsData));
		return p;
}

void ai_SetTukeyAlpha(AcousticIndicatorsData* data, float_t tukey_alpha) {
	data->tukey_alpha = tukey_alpha;
}

void ai_free_acoustic_indicators_data(AcousticIndicatorsData* data) {
    free(data->window_data);
    if(data->has_spectrum) {
        free(data->window_fft_data);
    }
}

float_t ai_GetThinBandRMS(AcousticIndicatorsData* data, int32_t band) {
	if(data->has_spectrum) {
		return data->window_fft_data[band];
	} else {
		return 0;
	}
}

int ai_init_acoustic_indicators_data(AcousticIndicatorsData* data, bool a_filter, bool spectrum, float_t ref_pressure, bool window, int8_t sample_rate_index, const char* format, bool mono)
{
    if(sample_rate_index >= AI_NB_SUPPORTED_SAMPLES_RATES) {
        return AI_INIT_WRONG_SAMPLE_RATE;
    }
    int i;
    data->format = -1;
    for(i = 0; i < AI_FORMATS_SIZE; i++) {
        if(strcmp(format, ai_formats[i]) == 0) {
            data->format = i;
            break;
        }
    }
    if(data->format == -1) {
        return AI_INIT_WRONG_FORMAT;
    }
    data->mono = mono;
    data->window_data_size = (size_t)(ai_supported_samples_rates[sample_rate_index] / AI_WINDOWS_SIZE);
    data->window_data = malloc(data->window_data_size * sizeof(float_t));
	data->windows_count = 0;
	data->window_cursor = 0;
    data->window = window;
    data->a_filter = a_filter;
    data->has_spectrum = spectrum;
    data->ref_pressure = ref_pressure;
    data->last_leq_fast = 0;
    data->last_leq_slow = 0;
    data->tukey_alpha = 0.5;
    data->window_fft_data_size = kiss_fft_next_fast_size(data->window_data_size);
    if(spectrum) {
        data->window_fft_data = malloc(data->window_fft_data_size * sizeof(float_t));
        memset(data->window_fft_data, 0, data->window_fft_data_size * sizeof(float_t));
    } else {
        data->window_fft_data = NULL;
    }
    return AI_INIT_NO_ERRORS;
}


float ai_get_band_leq(AcousticIndicatorsData* data, int band_id) {
    if(data->has_spectrum && band_id >= 0 && band_id < AI_NB_BAND) {
        int i;
        double sum = 0;
        int window_count = data->windows_count == 0 ? AI_WINDOWS_SIZE : data->windows_count;
        for(i=0; i < window_count; i++) {
            sum += pow(10, data->spectrum[i][band_id] / 10.0);
        }
        return (float_t)(10 * log10(sum / AI_WINDOWS_SIZE));
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
        return data->spectrum[window_count][band_id];
    } else {
        return 0.;
    }
}
