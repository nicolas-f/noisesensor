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
#include <limits.h>

int tests_run = 0;

#ifndef ai_unit_test_print
#define ai_unit_test_print 1
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
            if(ai_add_sample(&acousticIndicatorsData, sampleLen * sizeof(int16_t), (int8_t *)shortBuffer + sampleCursor) == AI_FEED_COMPLETE) {
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
            if(ai_add_sample(&acousticIndicatorsData, sampleLen * sizeof(int16_t), (int8_t *)shortBuffer + sampleCursor) == AI_FEED_COMPLETE) {
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
            if(ai_add_sample(&acousticIndicatorsData, sampleLen * sizeof(int16_t), (int8_t *)shortBuffer + sampleCursor) == AI_FEED_COMPLETE) {
                mu_assert("Too much iteration, more than 10s in file or wrong sampling rate", leqId < 10);
                for(i = 0; i < AI_NB_BAND; i++) {
                    double db_1s = ai_get_band_leq(&acousticIndicatorsData, i);
                    leqs[i] += pow(10, db_1s / 10.);
                }
                leqId++;
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
		float leqstfft = 10 * log10(leqs[idfreq] / leqId);
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
        if (ai_add_sample(&acousticIndicatorsData, maxLen * sizeof(int32_t), (int8_t *)buffer) == AI_FEED_COMPLETE) {
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
        if (ai_add_sample(&acousticIndicatorsData, maxLen * sizeof(int32_t), (int8_t *)buffer) == AI_FEED_COMPLETE) {
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
        if (ai_add_sample(&acousticIndicatorsData, maxLen * sizeof(int32_t), (int8_t *)buffer) == AI_FEED_COMPLETE) {
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
 static char * test_1khz_hann_lobs(double alpha) {
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
			if(ai_add_sample(&acousticIndicatorsData, maxLen * sizeof(int16_t), (int8_t *)buffer) == AI_FEED_COMPLETE) {
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
    return test_1khz_hann_lobs(1.);
}

static char * test_1khz_hann_lobs_075() {
    return test_1khz_hann_lobs(0.75);
}

static char * test_1khz_hann_lobs_05() {
    return test_1khz_hann_lobs(0.5);
}
static char * test_1khz_hann_lobs_025() {
    return test_1khz_hann_lobs(0.25);
}
static char * test_1khz_hann_lobs_015() {
    return test_1khz_hann_lobs(0.15);
}
static char * test_1khz_hann_lobs_01() {
	return test_1khz_hann_lobs(0.1);
}

static char * test_1khz_hann_lobs_0() {
    return test_1khz_hann_lobs(0);
}


/**
* Read raw audio signal file
*/
static char * test_stereo_leq_38db_48khz() {
    float_t REF_SOUND_PRESSURE = 1.;

    const char *filename = "ref38dB_48000Hz_32bitsPCM.raw";
    FILE *ptr;
    AcousticIndicatorsData acousticIndicatorsData;
    ai_init_acoustic_indicators_data(&acousticIndicatorsData, false, true, REF_SOUND_PRESSURE, true, AI_SAMPLE_RATE_48000, ai_formats[AI_FORMAT_S32_LE], false);

    int8_t buffer[48000 / AI_WINDOWS_SIZE * sizeof(int32_t)];

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
    float expected_leqs[AI_NB_BAND] = { -98.5526106508941, -100.08310461956117, -101.39702355324788,
     -99.78748251303432, -102.82087254268916, -100.12116830605451, -102.66192546679406, -98.88108459596202,
      -104.95385497497156, -106.03069451647563, -104.97137742862505, -105.52732839258753, -106.43284370908978,
       -106.97648277016575, -107.10026993077449, -107.50380055381696, -108.0872366006321, -108.52118804018241,
        -109.12049558053083, -109.13943526568177, -109.19021532505474, -109.35368116045458, -108.9564386285079,
         -108.48942369424529, -108.1625057801655, -107.58874054478314, -106.93409550080841, -105.90455046987447,
          -104.77799354205305 };

    if (ai_unit_test_print) {
        printf("Frequency");
        int iband;
        for (iband = 0; iband<AI_NB_BAND; iband++) {
            printf(",%.1f", ai_get_frequency(iband));
        }
        printf("\nRef");
        for (iband = 0; iband<AI_NB_BAND; iband++) {
            printf(",%.1f", expected_leqs[iband]);
        }
        printf("\n");
    }
    int leqId = 0;
    int i;
    while (!feof(ptr)) {
        read = fread(buffer, 1, sizeof(buffer), ptr);
        total_read += read;
        // File fragment is in read array
        // Process short sample
        int sampleCursor = 0;
        do {
            int maxLen = ai_get_maximal_sample_size(&acousticIndicatorsData);
            int sampleLen = (read - sampleCursor) < maxLen ? (read - sampleCursor) : maxLen;
            if (ai_add_sample(&acousticIndicatorsData, sampleLen, buffer + sampleCursor) == AI_FEED_COMPLETE) {
                if (ai_unit_test_print) {
                    printf("leq: %.1f\n", ai_get_leq_slow(&acousticIndicatorsData));
                }
                mu_assert("Too much iteration, more than 10s in file or wrong sampling rate", leqId < 2);
                for (i = 0; i < AI_NB_BAND; i++) {
                    double db_1s = ai_get_band_leq(&acousticIndicatorsData, i);
                    leqs[i] += pow(10, db_1s / 10.);
                }
                leqId++;
            }
            sampleCursor += sampleLen;
        } while (sampleCursor < read);
    }
    mu_assert("Wrong number of parsed samples", total_read == 48000 * 2 * sizeof(int32_t) * 2);
    ai_free_acoustic_indicators_data(&acousticIndicatorsData);
    // Check expected leq
    int idfreq;
    double sumval = 0;
    if (ai_unit_test_print) {
        printf("STFFT");
    }
    for (idfreq = 0; idfreq < AI_NB_BAND; idfreq++) {
        float leqstfft = 10 * log10(leqs[idfreq] / leqId);
        float leqdiff = leqstfft - expected_leqs[idfreq];
        if (ai_unit_test_print) {
            printf(",%.1f", leqstfft);
        }
        sumval += leqdiff*leqdiff;
    }
    if (ai_unit_test_print) {
        printf("\n");
    }
    double expected_mean_error = 7;
    double mean_error = sqrt(sumval / AI_NB_BAND);
    sprintf(mu_message, "Wrong mean error expected %f got %f\n", expected_mean_error, mean_error);
    mu_assert(mu_message, mean_error < expected_mean_error);
    return 0;
}


/**
* Read raw audio signal file
*/
static char * test_stereo_leq_94db_48khz() {
    float_t REF_SOUND_PRESSURE = 1.;

    const char *filename = "ref94dB_48000Hz_32bitsPCM.raw";
    FILE *ptr;
    AcousticIndicatorsData acousticIndicatorsData;
    ai_init_acoustic_indicators_data(&acousticIndicatorsData, false, true, REF_SOUND_PRESSURE, true, AI_SAMPLE_RATE_48000, ai_formats[AI_FORMAT_S32_LE], false);

    int8_t buffer[48000 / AI_WINDOWS_SIZE * sizeof(int32_t)];

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
    float expected_leqs[AI_NB_BAND] = { -99.48116721400389, -97.48893965813018, -96.81184203949795,
     -95.84214992764502, -98.10607934318902, -96.58995912512071, -96.67682704617175, -96.34552399897245,
      -95.5364517170513, -94.79901758561999, -93.9314365185785, -92.65730679563312, -91.44326986828703,
       -89.84820640786023, -87.72436124413997, -82.85361930914539, -62.31561092644313, -38.101112720252885,
        -62.30610806101392, -83.69825044599386, -87.38405791324978, -94.78531345604127, -87.15480116933949,
        -100.05667263141724, -101.78695388790811, -102.64481450593492, -103.30209829076762, -103.33360212552641,
         -102.90378652372958 };

    if (ai_unit_test_print) {
        printf("Frequency");
        int iband;
        for (iband = 0; iband<AI_NB_BAND; iband++) {
            printf(",%.1f", ai_get_frequency(iband));
        }
        printf("\nRef");
        for (iband = 0; iband<AI_NB_BAND; iband++) {
            printf(",%.1f", expected_leqs[iband]);
        }
        printf("\n");
    }
    int leqId = 0;
    int i;
    while (!feof(ptr)) {
        read = fread(buffer, 1, sizeof(buffer), ptr);
        total_read += read;
        // File fragment is in read array
        // Process short sample
        int sampleCursor = 0;
        do {
            int maxLen = ai_get_maximal_sample_size(&acousticIndicatorsData);
            int sampleLen = (read - sampleCursor) < maxLen ? (read - sampleCursor) : maxLen;
            if (ai_add_sample(&acousticIndicatorsData, sampleLen, buffer + sampleCursor) == AI_FEED_COMPLETE) {
                if (ai_unit_test_print) {
                    printf("leq: %.1f\n", ai_get_leq_slow(&acousticIndicatorsData));
                }
                mu_assert("Too much iteration, more than 10s in file or wrong sampling rate", leqId < 2);
                for (i = 0; i < AI_NB_BAND; i++) {
                    double db_1s = ai_get_band_leq(&acousticIndicatorsData, i);
                    leqs[i] += pow(10, db_1s / 10.);
                }
                leqId++;
            }
            sampleCursor += sampleLen;
        } while (sampleCursor < read);
    }
    mu_assert("Wrong number of parsed samples", total_read == 48000 * 2 * sizeof(int32_t) * 2);
    ai_free_acoustic_indicators_data(&acousticIndicatorsData);
    // Check expected leq
    int idfreq;
    double sumval = 0;
    if (ai_unit_test_print) {
        printf("STFFT");
    }
    for (idfreq = 0; idfreq < AI_NB_BAND; idfreq++) {
        float leqstfft = 10 * log10(leqs[idfreq] / leqId);
        float leqdiff = leqstfft - expected_leqs[idfreq];
        if (ai_unit_test_print) {
            printf(",%.1f", leqstfft);
        }
        sumval += leqdiff*leqdiff;
    }
    if (ai_unit_test_print) {
        printf("\n");
    }
    double expected_mean_error = 18;
    double mean_error = sqrt(sumval / AI_NB_BAND);
    sprintf(mu_message, "Wrong mean error expected %f got %f\n", expected_mean_error, mean_error);
    mu_assert(mu_message, mean_error < expected_mean_error);
    return 0;
}


/**
* Read raw audio signal file
*/
static char * test_stereo_laeq_38db_48khz() {
    float_t REF_SOUND_PRESSURE = 1.;

    const char *filename = "ref38dB_48000Hz_32bitsPCM.raw";
    FILE *ptr;
    AcousticIndicatorsData acousticIndicatorsData;
    ai_init_acoustic_indicators_data(&acousticIndicatorsData, true, true, REF_SOUND_PRESSURE, true, AI_SAMPLE_RATE_48000, ai_formats[AI_FORMAT_S32_LE], false);

    int8_t buffer[48000 / AI_WINDOWS_SIZE * sizeof(int32_t)];

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
    float expected_leqs[AI_NB_BAND] = { -148.52242848597487, -145.0410709965136, -140.71736260195368, -133.77491215895515, -132.97004136003804, -126.08837867645909, -125.45670565322497, -118.04299740430042, -121.00479362630595, -119.27408987814134, -115.81459671703703, -114.11695398489775, -113.00720031492013, -111.8250303439453, -110.3497762939496, -109.3999326249805, -108.93797150858033, -108.52991543085524, -108.53702595982811, -108.16139817739926, -107.9932619644383, -108.0909781628753, -107.77572060675288, -107.56906253981106, -107.71989936014863, -107.9462763576687, -108.6076615044825, -109.6471064868118, -111.85562726954451};

    if (ai_unit_test_print) {
        printf("Frequency");
        int iband;
        for (iband = 0; iband<AI_NB_BAND; iband++) {
            printf(",%.1f", ai_get_frequency(iband));
        }
        printf("\nRef");
        for (iband = 0; iband<AI_NB_BAND; iband++) {
            printf(",%.1f", expected_leqs[iband]);
        }
        printf("\n");
    }
    int leqId = 0;
    int i;
    while (!feof(ptr)) {
        read = fread(buffer, 1, sizeof(buffer), ptr);
        total_read += read;
        // File fragment is in read array
        // Process short sample
        int sampleCursor = 0;
        do {
            int maxLen = ai_get_maximal_sample_size(&acousticIndicatorsData);
            int sampleLen = (read - sampleCursor) < maxLen ? (read - sampleCursor) : maxLen;
            if (ai_add_sample(&acousticIndicatorsData, sampleLen, buffer + sampleCursor) == AI_FEED_COMPLETE) {
                if (ai_unit_test_print) {
                    printf("laeq: %.1f\n", ai_get_leq_slow(&acousticIndicatorsData));
                }
                mu_assert("Too much iteration, more than 10s in file or wrong sampling rate", leqId < 2);
                for (i = 0; i < AI_NB_BAND; i++) {
                    double db_1s = ai_get_band_leq(&acousticIndicatorsData, i);
                    leqs[i] += pow(10, db_1s / 10.);
                }
                leqId++;
            }
            sampleCursor += sampleLen;
        } while (sampleCursor < read);
    }
    mu_assert("Wrong number of parsed samples", total_read == 48000 * 2 * sizeof(int32_t) * 2);
    ai_free_acoustic_indicators_data(&acousticIndicatorsData);
    // Check expected leq
    int idfreq;
    double sumval = 0;
    if (ai_unit_test_print) {
        printf("STFFT");
    }
    for (idfreq = 0; idfreq < AI_NB_BAND; idfreq++) {
        float leqstfft = 10 * log10(leqs[idfreq] / leqId);
        float leqdiff = leqstfft - expected_leqs[idfreq];
        if (ai_unit_test_print) {
            printf(",%.1f", leqstfft);
        }
        sumval += leqdiff*leqdiff;
    }
    if (ai_unit_test_print) {
        printf("\n");
    }
    double expected_mean_error = 7;
    double mean_error = sqrt(sumval / AI_NB_BAND);
    sprintf(mu_message, "Wrong mean error expected %f got %f\n", expected_mean_error, mean_error);
    mu_assert(mu_message, mean_error < expected_mean_error);
    return 0;
}


/**
* Read raw audio signal file
*/
static char * test_mono_24bits() {
    float_t REF_SOUND_PRESSURE = 1.;

    const char *filename = "sinus1khz_32000Hz_24bitsPCM_2s.raw";
    FILE *ptr;
    AcousticIndicatorsData acousticIndicatorsData;
    bool mono = true;
    ai_init_acoustic_indicators_data(&acousticIndicatorsData, true, true, REF_SOUND_PRESSURE, true, AI_SAMPLE_RATE_32000, ai_formats[AI_FORMAT_S24_3LE], mono);

    int8_t buffer[32000 / AI_WINDOWS_SIZE * 3];

    // open file
    ptr = fopen(filename, "rb");
    if (ptr == NULL) {
        printf("test_mono_24bits - Error opening audio file\n");
        exit(1);
    }

    int total_read = 0;
    int read = 0;

    float leqs[AI_NB_BAND];
    memset(leqs, 0, sizeof(float) * AI_NB_BAND);
    // single tone at 1000 hz
    float expected_leqs[AI_NB_BAND] = { -78.7,-84.2,-88.7,-93.7,-96.7,-103.2,-102.0,-105.7,-109.1,-109.1,-112.3,-112.0,-111.7,-108.0,-101.1,-92.0,-73.4,-5.2,-75.7,-95.1,-104.7,-111.6,-117.8,-123.3,-128.6,-133.8,-139.3,-144.9,-150.2};

    if (ai_unit_test_print) {
        printf("test_mono_24bits - Frequency");
        int iband;
        for (iband = 0; iband<AI_NB_BAND; iband++) {
            printf(",%.1f", ai_get_frequency(iband));
        }
        printf("\ntest_mono_24bits - Ref");
        for (iband = 0; iband<AI_NB_BAND; iband++) {
            printf(",%.1f", expected_leqs[iband]);
        }
        printf("\n");
    }
    int leqId = 0;
    int i;
    while (!feof(ptr)) {
        read = fread(buffer, 1, sizeof(buffer), ptr);
        total_read += read;
        // File fragment is in read array
        // Process short sample
        int sampleCursor = 0;
        do {
            int maxLen = ai_get_maximal_sample_size(&acousticIndicatorsData);
            int sampleLen = (read - sampleCursor) < maxLen ? (read - sampleCursor) : maxLen;
            if (ai_add_sample(&acousticIndicatorsData, sampleLen, buffer + sampleCursor) == AI_FEED_COMPLETE) {
                if (ai_unit_test_print) {
                    printf("test_mono_24bits - laeq: %.1f\n", ai_get_leq_slow(&acousticIndicatorsData));
                }
                mu_assert("test_mono_24bits - Too much iteration, more than 2s in file or wrong sampling rate", leqId < 2);
                for (i = 0; i < AI_NB_BAND; i++) {
                    double db_1s = ai_get_band_leq(&acousticIndicatorsData, i);
                    leqs[i] += pow(10, db_1s / 10.);
                }
                leqId++;
            }
            sampleCursor += sampleLen;
        } while (sampleCursor < read);
    }
    mu_assert("Wrong number of parsed samples", total_read == 32000 * 3 * 2);
    ai_free_acoustic_indicators_data(&acousticIndicatorsData);
    // Check expected leq
    int idfreq;
    double sumval = 0;
    if (ai_unit_test_print) {
        printf("test_mono_24bits - STFFT");
    }
    for (idfreq = 0; idfreq < AI_NB_BAND; idfreq++) {
        float leqstfft = 10 * log10(leqs[idfreq] / leqId);
        float leqdiff = leqstfft - expected_leqs[idfreq];
        if (ai_unit_test_print) {
            printf(",%.1f", leqstfft);
        }
        sumval += leqdiff*leqdiff;
    }
    if (ai_unit_test_print) {
        printf("\n");
    }
    double expected_mean_error = 7;
    double mean_error = sqrt(sumval / AI_NB_BAND);
    sprintf(mu_message, "Wrong mean error expected %f got %f\n", expected_mean_error, mean_error);
    mu_assert(mu_message, mean_error < expected_mean_error);
    return 0;
}

/**
* Read raw audio signal file
*/
static char * test_stereo_laeq_94db_48khz() {
    float_t REF_SOUND_PRESSURE = 1.;

    const char *filename = "ref94dB_48000Hz_32bitsPCM.raw";
    FILE *ptr;
    AcousticIndicatorsData acousticIndicatorsData;
    ai_init_acoustic_indicators_data(&acousticIndicatorsData, true, true, REF_SOUND_PRESSURE, true, AI_SAMPLE_RATE_48000, ai_formats[AI_FORMAT_S32_LE], false);

    int8_t buffer[48000 / AI_WINDOWS_SIZE * sizeof(int32_t)];

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
    float expected_leqs[AI_NB_BAND] = { -148.76145336415823, -142.02290606955137, -135.65709345177677, -130.422748051288, -128.1276494727666, -122.62484339462289, -118.90994693495598, -115.37918899082335, -111.44171024630242, -108.073387664057, -104.6711640242838, -101.18230226703105, -97.95702809120776, -94.5361302510598, -90.72356776518873, -83.92602123522417, -62.32667772302924, -38.09714129602734, -62.290738596789375, -83.14102940809882, -86.21859435781707, -93.54032539035302, -85.93661501638371, -99.10603501674265, -101.32188368799432, -102.97556440177885, -104.93361391803438, -107.01548021858707, -109.90552292237994 };

    if (ai_unit_test_print) {
        printf("Frequency");
        int iband;
        for (iband = 0; iband<AI_NB_BAND; iband++) {
            printf(",%.1f", ai_get_frequency(iband));
        }
        printf("\nRef");
        for (iband = 0; iband<AI_NB_BAND; iband++) {
            printf(",%.1f", expected_leqs[iband]);
        }
        printf("\n");
    }
    int leqId = 0;
    int i;
    while (!feof(ptr)) {
        read = fread(buffer, 1, sizeof(buffer), ptr);
        total_read += read;
        // File fragment is in read array
        // Process short sample
        int sampleCursor = 0;
        do {
            int maxLen = ai_get_maximal_sample_size(&acousticIndicatorsData);
            int sampleLen = (read - sampleCursor) < maxLen ? (read - sampleCursor) : maxLen;
            if (ai_add_sample(&acousticIndicatorsData, sampleLen, buffer + sampleCursor) == AI_FEED_COMPLETE) {
                if (ai_unit_test_print) {
                    printf("laeq: %.1f\n", ai_get_leq_slow(&acousticIndicatorsData));
                }
                mu_assert("Too much iteration, more than 10s in file or wrong sampling rate", leqId < 2);
                for (i = 0; i < AI_NB_BAND; i++) {
                    double db_1s = ai_get_band_leq(&acousticIndicatorsData, i);
                    leqs[i] += pow(10, db_1s / 10.);
                }
                leqId++;
            }
            sampleCursor += sampleLen;
        } while (sampleCursor < read);
    }
    mu_assert("Wrong number of parsed samples", total_read == 48000 * 2 * sizeof(int32_t) * 2);
    ai_free_acoustic_indicators_data(&acousticIndicatorsData);
    // Check expected leq
    int idfreq;
    double sumval = 0;
    if (ai_unit_test_print) {
        printf("STFFT");
    }
    for (idfreq = 0; idfreq < AI_NB_BAND; idfreq++) {
        float leqstfft = 10 * log10(leqs[idfreq] / leqId);
        float leqdiff = leqstfft - expected_leqs[idfreq];
        if (ai_unit_test_print) {
            printf(",%.1f", leqstfft);
        }
        sumval += leqdiff*leqdiff;
    }
    if (ai_unit_test_print) {
        printf("\n");
    }
    double expected_mean_error = 12.5;
    double mean_error = sqrt(sumval / AI_NB_BAND);
    sprintf(mu_message, "Wrong mean error expected %f got %f\n", expected_mean_error, mean_error);
    mu_assert(mu_message, mean_error < expected_mean_error);
    return 0;
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
   mu_run_test(test_stereo_leq_38db_48khz);
   mu_run_test(test_stereo_leq_94db_48khz);
   mu_run_test(test_stereo_laeq_38db_48khz);
   mu_run_test(test_stereo_laeq_94db_48khz);
   mu_run_test(test_mono_24bits);

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
