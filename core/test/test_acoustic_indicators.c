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
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "minunit.h"
#include "string.h"

int tests_run = 0;

#ifndef ai_unit_test_print
#define ai_unit_test_print 0
#endif

//char *message = (char*)malloc(256 * sizeof(char));
char mu_message[256];

/**
 * Read raw audio signal file
 */
static char * test_leq_32khz() {
  // Compute the reference level.
  //double RMS_REFERENCE_90DB = 2500;
  //double DB_FS_REFERENCE = - (20 * log10(RMS_REFERENCE_90DB)) + 90;
  //double REF_SOUND_PRESSURE = 1 / pow(10, DB_FS_REFERENCE / 20);

	float_t REF_SOUND_PRESSURE = 1.;

	const char *filename = "speak_32000Hz_16bitsPCM_10s.raw";
	FILE *ptr;
	AcousticIndicatorsData acousticIndicatorsData;
    ai_init_acoustic_indicators_data(&acousticIndicatorsData, false, false,REF_SOUND_PRESSURE, false, AI_SAMPLE_RATE_32000, ai_formats[AI_FORMAT_S16_LE], true);

    int16_t shortBuffer[32000 / AI_WINDOWS_SIZE];

	// open file
	ptr = fopen(filename, "rb");
	if (ptr == NULL) {
		printf("Error opening audio file\n");
		exit(1);
	}

  int total_read = 0;
	int read = 0;

  float leqs[10];
  float expected_leqs[10] = {-26.21, -27.94, -29.12, -28.92, -40.4, -24.93, -31.55, -29.04, -31.08, -30.65};

  int leqId = 0;

	while(!feof(ptr)) {
		read = fread(shortBuffer, sizeof(int16_t), sizeof(shortBuffer) / sizeof(int16_t), ptr);
    total_read+=read;
		// File fragment is in read array
		// Process short sample
		int sampleCursor = 0;
		do {
			int maxLen = ai_get_maximal_sample_size(&acousticIndicatorsData) / sizeof(int16_t);
            int sampleLen = (read - sampleCursor) < maxLen ? (read - sampleCursor) : maxLen;
            if(ai_add_sample(&acousticIndicatorsData, sampleLen * sizeof(int16_t), shortBuffer + sampleCursor) == AI_FEED_COMPLETE) {
                mu_assert("Too much iteration, more than 10s in file or wrong sampling rate", leqId < 10);
                leqs[leqId++] = acousticIndicatorsData.last_leq_slow;
			}
			sampleCursor+=sampleLen;
		} while(sampleCursor < read);
	}
  mu_assert("Wrong number of parsed samples", total_read == 320000);
  ai_free_acoustic_indicators_data(&acousticIndicatorsData);
  // Check expected leq

  for(int second = 0; second < 10; second++) {
    sprintf(mu_message, "Wrong leq on %d second expected %f dB got %f dB", second, expected_leqs[second], leqs[second]);
    mu_assert(mu_message, fabs(expected_leqs[second] - leqs[second]) < 0.01);
  }
  return 0;
}


/**
 * Read raw audio signal file
 */
static char * test_laeq_32khz() {
  // Compute the reference level.
  //double RMS_REFERENCE_90DB = 2500;
  //double DB_FS_REFERENCE = - (20 * log10(RMS_REFERENCE_90DB)) + 90;
  //double REF_SOUND_PRESSURE = 1 / pow(10, DB_FS_REFERENCE / 20);

	float_t REF_SOUND_PRESSURE = 1.;

	const char *filename = "speak_32000Hz_16bitsPCM_10s.raw";
	FILE *ptr;
	AcousticIndicatorsData acousticIndicatorsData;
    ai_init_acoustic_indicators_data(&acousticIndicatorsData, true, false,REF_SOUND_PRESSURE, false, AI_SAMPLE_RATE_32000, ai_formats[AI_FORMAT_S16_LE], true);

    int16_t shortBuffer[32000 / AI_WINDOWS_SIZE];

	// open file
	ptr = fopen(filename, "rb");
	if (ptr == NULL) {
		printf("Error opening audio file\n");
		exit(1);
	}

  int total_read = 0;
	int read = 0;

  float leqs[10];
  float expected_laeqs[10] = {-31.37, -33.74, -33.05, -33.61, -43.68, -29.96, -35.53, -34.12, -37.06, -37.19};

  int leqId = 0;

	while(!feof(ptr)) {
		read = fread(shortBuffer, sizeof(int16_t), sizeof(shortBuffer) / sizeof(int16_t), ptr);
    total_read+=read;
		// File fragment is in read array
		// Process short sample
		int sampleCursor = 0;
		do {
			int maxLen = ai_get_maximal_sample_size(&acousticIndicatorsData) / sizeof(int16_t);
            int sampleLen = (read - sampleCursor) < maxLen ? (read - sampleCursor) : maxLen;
            if(ai_add_sample(&acousticIndicatorsData, sampleLen * sizeof(int16_t), shortBuffer + sampleCursor) == AI_FEED_COMPLETE) {
                mu_assert("Too much iteration, more than 10s in file or wrong sampling rate", leqId < 10);
                leqs[leqId++] = ai_get_leq_slow(&acousticIndicatorsData);
			}
			sampleCursor+=sampleLen;
		} while(sampleCursor < read);
	}
  mu_assert("Wrong number of parsed samples", total_read == 320000);

  ai_free_acoustic_indicators_data(&acousticIndicatorsData);
  // Check expected leq

  for(int second = 0; second < 10; second++) {
    sprintf(mu_message, "Wrong lAeq on %d second expected %f dB got %f dB", second, expected_laeqs[second], leqs[second]);
    mu_assert(mu_message, fabs(expected_laeqs[second] - leqs[second]) < 0.1);
  }
  return 0;
}


/**
 * Read raw audio signal file
 */
static char * test_leq_spectrum_32khz() {
  // Compute the reference level.
  //double RMS_REFERENCE_90DB = 2500;
  //double DB_FS_REFERENCE = - (20 * log10(RMS_REFERENCE_90DB)) + 90;
  //double REF_SOUND_PRESSURE = 1 / pow(10, DB_FS_REFERENCE / 20);

    float_t REF_SOUND_PRESSURE = 1.;

    const char *filename = "speak_32000Hz_16bitsPCM_10s.raw";
    FILE *ptr;
    AcousticIndicatorsData acousticIndicatorsData;
    ai_init_acoustic_indicators_data(&acousticIndicatorsData, false, true,REF_SOUND_PRESSURE, false, AI_SAMPLE_RATE_32000, ai_formats[AI_FORMAT_S16_LE], true);
    int16_t shortBuffer[32000 / AI_WINDOWS_SIZE];

    // open file
    ptr = fopen(filename, "rb");
    if (ptr == NULL) {
        printf("Error opening audio file\n");
        exit(1);
    }

  int total_read = 0;
    int read = 0;

  float leqs[AI_NB_BAND];
  memset(leqs, 0, sizeof(float) * AI_NB_BAND);
  float expected_leqs[AI_NB_BAND] = {-64.59,-62.82,-63.14,-64.93,-65.03,-66.43,-65.56,-66.  ,-68.06,-66.28,-43.34,
                             -31.93,-37.28,-47.33,-35.33,-42.68,-42.91,-48.51,-49.1 ,-52.9 ,-52.15,-52.8 ,
                             -52.35,-52.31,-53.39,-52.53,-53.73,-53.56,-57.9};

	if(ai_unit_test_print) {
		printf("Frequency");
		int iband;
		for(iband=0;iband<AI_NB_BAND;iband++) {
			printf(",%.1f", ai_get_frequency(iband));
		}
		printf("\nRef");
		for(iband=0;iband<AI_NB_BAND;iband++) {
			printf(",%.1f", expected_leqs[iband]);
		}
		printf("\n");
	}
  int leqId = 0;
    int i;
    while(!feof(ptr)) {
        read = fread(shortBuffer, sizeof(int16_t), sizeof(shortBuffer) / sizeof(int16_t), ptr);
    total_read+=read;
        // File fragment is in read array
        // Process short sample
        int sampleCursor = 0;
        do {
            int maxLen = ai_get_maximal_sample_size(&acousticIndicatorsData) / sizeof(int16_t);
            int sampleLen = (read - sampleCursor) < maxLen ? (read - sampleCursor) : maxLen;
            if(ai_add_sample(&acousticIndicatorsData, sampleLen * sizeof(int16_t), shortBuffer + sampleCursor) == AI_FEED_COMPLETE) {
                mu_assert("Too much iteration, more than 10s in file or wrong sampling rate", leqId < 10);
                for(i = 0; i < AI_NB_BAND; i++) {
                    double db_1s = ai_get_band_leq(&acousticIndicatorsData, i);
                    leqs[i] += pow(10, db_1s / 10.);
                }
            }
            sampleCursor+=sampleLen;
        } while(sampleCursor < read);
    }
  mu_assert("Wrong number of parsed samples", total_read == 320000);
  ai_free_acoustic_indicators_data(&acousticIndicatorsData);
  // Check expected leq
  int idfreq;
  double sumval =  0;
	if(ai_unit_test_print) {
		printf("STFFT");
	}
  for(idfreq = 0; idfreq < AI_NB_BAND; idfreq++) {
		float leqstfft = 10 * log10(leqs[idfreq] / 10);
    float leqdiff = leqstfft - expected_leqs[idfreq];
		if(ai_unit_test_print) {
			printf(",%.1f", leqstfft);
		}
    sumval+=leqdiff*leqdiff;
  }
	if(ai_unit_test_print) {
		printf("\n");
	}
  double expected_mean_error = 2.64;
  double mean_error = sqrt(sumval / AI_NB_BAND);
  sprintf(mu_message, "Wrong mean error expected %f got %f\n", expected_mean_error, mean_error);
  mu_assert(mu_message, mean_error < expected_mean_error);
  return 0;
}

static char * test_32khz_32bits() {
    double RMS_REFERENCE_94DB = 163840000.0;
    double DB_FS_REFERENCE = -(20 * log10(RMS_REFERENCE_94DB)) + 94;
    double REF_SOUND_PRESSURE = 1 / pow(10, DB_FS_REFERENCE / 20);

    const int sampleRate = 32000;
    const int signal_samples = 32000;
    double powerRMS = RMS_REFERENCE_94DB;
    float signalFrequency = 1000;
    double powerPeak = powerRMS * sqrt(2);

    int32_t buffer[32000 / AI_WINDOWS_SIZE];

    AcousticIndicatorsData acousticIndicatorsData;

    ai_init_acoustic_indicators_data(&acousticIndicatorsData, false, true, REF_SOUND_PRESSURE / INT_MAX, false, AI_SAMPLE_RATE_32000, ai_formats[AI_FORMAT_S32_LE], true);

    int s;
    for (s = 0; s < signal_samples;) {
        int start_s = s;
        int maxLen = ai_get_maximal_sample_size(&acousticIndicatorsData) / sizeof(int32_t);
        for (; s < signal_samples && s - start_s < maxLen; s++) {
            double t = s * (1 / (double)sampleRate);
            double pwr = (sin(2 * AI_PI * signalFrequency * t) * (powerPeak));
            buffer[s - start_s] = (int32_t)pwr;
        }
        if (ai_add_sample(&acousticIndicatorsData, maxLen * sizeof(int32_t), buffer) == AI_FEED_COMPLETE) {
            // Average spectrum levels
            int iband;
            float_t level = ai_get_band_leq(&acousticIndicatorsData, 17);
            sprintf(mu_message, "Wrong mean error expected %f got %f\n", 94.f, level);
            mu_assert(mu_message, abs(94 - level) < 0.1);
        }
    }
    return 0;
}


static char * test_32khz_32bits_stereo() {
    double RMS_REFERENCE_94DB = 163840000.0;
    double DB_FS_REFERENCE = -(20 * log10(RMS_REFERENCE_94DB)) + 94;
    double REF_SOUND_PRESSURE = 1 / pow(10, DB_FS_REFERENCE / 20);

    const int sampleRate = 32000;
    const int signal_samples = 32000 * 2;
    double powerRMS = RMS_REFERENCE_94DB;
    float signalFrequency = 1000;
    double powerPeak = powerRMS * sqrt(2);

    size_t buffer_len = 32000 / AI_WINDOWS_SIZE * 2;
    int32_t buffer[32000 / AI_WINDOWS_SIZE * 2];

    AcousticIndicatorsData acousticIndicatorsData;

    ai_init_acoustic_indicators_data(&acousticIndicatorsData, false, true, REF_SOUND_PRESSURE / INT_MAX, false, AI_SAMPLE_RATE_32000, ai_formats[AI_FORMAT_S32_LE], false);

    int s;
    for (s = 0; s < signal_samples;) {
        int start_s = s;
        int maxLen = ai_get_maximal_sample_size(&acousticIndicatorsData) / sizeof(int32_t);
        for (; s < signal_samples && s - start_s < maxLen / 2; s++) {
            double t = s * (1 / (double)sampleRate);
            double pwr = (sin(2 * AI_PI * signalFrequency * t) * (powerPeak));
            buffer[(s - start_s) * 2] = (int32_t)pwr;
            buffer[(s - start_s) * 2 + 1] = (int32_t)0;
        }
        if (ai_add_sample(&acousticIndicatorsData, maxLen * sizeof(int32_t), buffer) == AI_FEED_COMPLETE) {
            // Average spectrum levels
            int iband;
            float_t level = ai_get_band_leq(&acousticIndicatorsData, 17);
            sprintf(mu_message, "Wrong mean error expected %f got %f\n", 94.f, level);
            mu_assert(mu_message, abs(94 - level) < 0.1);
        }
    }
    return 0;
}




static char * test_48khz_32bits_stereo() {
    double RMS_REFERENCE_94DB = 163840000.0;
    double DB_FS_REFERENCE = -(20 * log10(RMS_REFERENCE_94DB)) + 94;
    double REF_SOUND_PRESSURE = 1 / pow(10, DB_FS_REFERENCE / 20);

    const int sampleRate = 48000;
    const int signal_samples = 48000 * 2;
    double powerRMS = RMS_REFERENCE_94DB;
    float signalFrequency = 1000;
    double powerPeak = powerRMS * sqrt(2);

    size_t buffer_len = 48000 / AI_WINDOWS_SIZE * 2;
    int32_t buffer[48000 / AI_WINDOWS_SIZE * 2];

    AcousticIndicatorsData acousticIndicatorsData;

    ai_init_acoustic_indicators_data(&acousticIndicatorsData, false, true, REF_SOUND_PRESSURE / INT_MAX, false, AI_SAMPLE_RATE_48000, ai_formats[AI_FORMAT_S32_LE], false);

    int s;
    for (s = 0; s < signal_samples;) {
        int start_s = s;
        int maxLen = ai_get_maximal_sample_size(&acousticIndicatorsData) / sizeof(int32_t);
        for (; s < signal_samples && s - start_s < maxLen / 2; s++) {
            double t = s * (1 / (double)sampleRate);
            double pwr = (sin(2 * AI_PI * signalFrequency * t) * (powerPeak));
            buffer[(s - start_s) * 2] = (int32_t)pwr;
            buffer[(s - start_s) * 2 + 1] = (int32_t)0;
        }
        if (ai_add_sample(&acousticIndicatorsData, maxLen * sizeof(int32_t), buffer) == AI_FEED_COMPLETE) {
            // Average spectrum levels
            int iband;
            float_t level = ai_get_band_leq(&acousticIndicatorsData, 17);
            sprintf(mu_message, "Wrong mean error expected %f got %f\n", 94.f, level);
            mu_assert(mu_message, abs(94 - level) < 0.1);
        }
    }
    return 0;
}

/**
 * Test 1khz overlapped Hann FFT
 */
 static char * test_1khz_hann_lobs(float alpha) {
		double RMS_REFERENCE_94DB = 2500.0;
		double DB_FS_REFERENCE = - (20 * log10(RMS_REFERENCE_94DB)) + 94;
		double REF_SOUND_PRESSURE = 1 / pow(10, DB_FS_REFERENCE / 20);

		const int sampleRate = 32000;
		const int signal_samples = 32000;
		double powerRMS = RMS_REFERENCE_94DB;
		float signalFrequency = 1000;
		double powerPeak = powerRMS * sqrt(2);

		int16_t buffer[32000 / AI_WINDOWS_SIZE];

		AcousticIndicatorsData acousticIndicatorsData;
		ai_init_acoustic_indicators_data(&acousticIndicatorsData, false, true,REF_SOUND_PRESSURE / SHRT_MAX, alpha > 0, AI_SAMPLE_RATE_32000, ai_formats[AI_FORMAT_S16_LE], true);
		if(alpha > 0) {
			acousticIndicatorsData.tukey_alpha = alpha;
		}
		int s;
		int processed_bands = 0;
		for (s = 0; s < signal_samples;) {
			int start_s = s;
			int maxLen = ai_get_maximal_sample_size(&acousticIndicatorsData) / sizeof(int16_t);
			for(; s < signal_samples && s-start_s < maxLen;s++) {
				double t = s * (1 / (double)sampleRate);
	      double pwr = (sin(2 * AI_PI * signalFrequency * t) * (powerPeak));
				buffer[s-start_s] = (int16_t)pwr;
			}
			if(ai_add_sample(&acousticIndicatorsData, maxLen * sizeof(int16_t), buffer) == AI_FEED_COMPLETE) {
					// Average spectrum levels
					int iband;
					if(ai_unit_test_print) {
						printf("Tukey_%.2f", acousticIndicatorsData.tukey_alpha);
					}
					int band_id;
					for(iband=0;iband<AI_NB_BAND;iband++) {
						processed_bands++;
						float_t level = ai_get_band_leq(&acousticIndicatorsData, iband);
						if(ai_get_frequency(iband) == signalFrequency) {
						  sprintf(mu_message, "Wrong mean error expected %f got %f\n", 94.f, level);
						  mu_assert(mu_message, abs(94-level) < 0.1);
						}
						if(ai_unit_test_print) {
							printf(",%.1f", level);
						}
					}
					if(ai_unit_test_print) {
						printf(",%.1f", ai_get_leq_slow(&acousticIndicatorsData));
						printf("\n");
					}
			}
		}
		mu_assert("Spectrum not obtained" ,processed_bands == AI_NB_BAND);
	  ai_free_acoustic_indicators_data(&acousticIndicatorsData);
		return 0;
}

static char * test_1khz_hann_lobs_1() {
	test_1khz_hann_lobs(1.);
}

static char * test_1khz_hann_lobs_075() {
	test_1khz_hann_lobs(0.75);
}

static char * test_1khz_hann_lobs_05() {
	test_1khz_hann_lobs(0.5);
}
static char * test_1khz_hann_lobs_025() {
	test_1khz_hann_lobs(0.25);
}
static char * test_1khz_hann_lobs_015() {
	test_1khz_hann_lobs(0.15);
}
static char * test_1khz_hann_lobs_01() {
	test_1khz_hann_lobs(0.1);
}

static char * test_1khz_hann_lobs_0() {
	test_1khz_hann_lobs(0);
}
static char * all_tests() {
   mu_run_test(test_leq_32khz);
   mu_run_test(test_laeq_32khz);
   mu_run_test(test_leq_spectrum_32khz);
   mu_run_test(test_1khz_hann_lobs_1);
   mu_run_test(test_1khz_hann_lobs_075);
   mu_run_test(test_1khz_hann_lobs_05);
   mu_run_test(test_1khz_hann_lobs_025);
   mu_run_test(test_1khz_hann_lobs_015);
   mu_run_test(test_1khz_hann_lobs_01);
   mu_run_test(test_1khz_hann_lobs_0);
   mu_run_test(test_32khz_32bits);
   mu_run_test(test_32khz_32bits_stereo);
   mu_run_test(test_48khz_32bits_stereo);
   return 0;
}

int main(int argc, char **argv) {
     char *result = all_tests();
     if (result != 0) {
         printf("%s\n", result);
     }
     else {
         printf("ALL TESTS PASSED\n");
     }
     printf("Tests run: %d\n", tests_run);

     return result != 0;
}
