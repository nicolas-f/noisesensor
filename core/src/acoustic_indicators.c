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

#include "acoustic_indicators.h"
#include <stdio.h>
#include <inttypes.h>
#include <math.h>
#include <string.h>



// int order = max(denominator.length, numerator.length);
#define ORDER (7)

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
	return AI_WINDOW_SIZE - data->window_cursor;
}

bool ai_AddSample(AcousticIndicatorsData* data, int sample_len, const int16_t* sample_data, float_t* laeq, float_t ref_pressure, bool a_filter) {
	if(data->window_cursor + sample_len > AI_WINDOW_SIZE) {
		fprintf( stderr, "Exceed window array size (%d on %d)\n", data->window_cursor + sample_len, AI_WINDOW_SIZE);
		return false;
	}
	for(int i=data->window_cursor; i < sample_len + data->window_cursor; i++) {
		data->window_data[i] = sample_data[i-data->window_cursor];
	}
	data->window_cursor+=sample_len;
	if(data->window_cursor >= AI_WINDOW_SIZE) {
		data->window_cursor = 0;
		// Compute A weighting
		if(a_filter) {
				float_t weightedSignal[AI_WINDOW_SIZE];
				// Filter delays
				float_t z[ORDER-1][AI_WINDOW_SIZE];
				for (int idT = 0; idT < AI_WINDOW_SIZE; idT++){
            // Avoid iteration idT=0 exception (z[0][idT-1]=0)
            weightedSignal[idT] = (numerator_32khz[0]*data->window_data[idT] + (idT == 0 ? 0 : z[0][idT-1]));
            // Avoid iteration idT=0 exception (z[1][idT-1]=0)
            z[0][idT] = (numerator_32khz[1]*data->window_data[idT] + (idT == 0 ? 0 : z[1][idT-1]) - denominator_32khz[1]*data->window_data[idT]);
            for (int k = 0; k<ORDER-2; k++){
                // Avoid iteration idT=0 exception (z[k+1][idT-1]=0)
                z[k][idT] = (numerator_32khz[k+1]*data->window_data[idT] + (idT ==0 ? 0 : z[k+1][idT-1]) - denominator_32khz[k+1]*weightedSignal[idT]);
            }
            z[ORDER-2][idT] = (numerator_32khz[ORDER-1]*data->window_data[idT] - denominator_32khz[ORDER-1] * weightedSignal[idT]);
        }
				for (int idT = 0; idT < AI_WINDOW_SIZE; idT++){
					data->window_data[idT] = weightedSignal[idT];
				}
		}
		// Compute RMS
		float_t sampleSum = 0;
		for(int i=0; i < AI_WINDOW_SIZE; i++) {
			sampleSum += (float_t)data->window_data[i] * (float_t)data->window_data[i];
		}
		// Push window sum in windows struct data
		data->windows[data->windows_count++] = sampleSum;
		if(data->windows_count == AI_WINDOWS_SIZE) {
				// compute energetic average
				float_t sumWindows = 0;
				for(int i=0; i<AI_WINDOWS_SIZE;i++) {
					sumWindows+=data->windows[i];
				}
				// Convert into dB(A)
				*laeq = 10 * log10((double)sumWindows / (AI_WINDOWS_SIZE * AI_WINDOW_SIZE) / (ref_pressure * ref_pressure));
				data->windows_count = 0;
				return true;
		}
	}
	return false;
}

void ai_NewAcousticIndicatorsData(AcousticIndicatorsData* data)
{
	data->windows_count = 0;
	data->window_cursor = 0;
}
