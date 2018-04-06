#include "acoustic_indicators.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "minunit.h"

int tests_run = 0;
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

	float_t REF_SOUND_PRESSURE = 32767.;

	const char *filename = "speak_32000Hz_16bitsPCM_10s.raw";
	FILE *ptr;
	AcousticIndicatorsData acousticIndicatorsData;
    ai_InitAcousticIndicatorsData(&acousticIndicatorsData);

	int16_t shortBuffer[4096];

	// open file
	ptr = fopen(filename, "rb");
	if (ptr == NULL) {
		printf("Error opening audio file\n");
		exit(1);
	}

  int total_read = 0;
	int read = 0;

  float leqs[10];
  float expected_leqs[10] = {-26.21,-27.94,-29.12,-28.92,-40.39,-24.93,-31.55,-29.04,-31.08,-30.65};

  int leqId = 0;

	while(!feof(ptr)) {
		read = fread(shortBuffer, sizeof(int16_t), sizeof(shortBuffer) / sizeof(int16_t), ptr);
    total_read+=read;
		// File fragment is in read array
		// Process short sample
		int sampleCursor = 0;
		do {
			int maxLen = ai_GetMaximalSampleSize(&acousticIndicatorsData);
			int sampleLen = (read - sampleCursor) < maxLen ? (read - sampleCursor) : maxLen;
			float_t leq;
			if(ai_AddSample(&acousticIndicatorsData, sampleLen, shortBuffer + sampleCursor, &leq,REF_SOUND_PRESSURE, false)) {
        mu_assert("Too much iteration, more than 10s in file or wrong sampling rate", leqId < 10);
        leqs[leqId++] = leq;
			}
			sampleCursor+=sampleLen;
		} while(sampleCursor < read);
	}
  mu_assert("Wrong number of parsed samples", total_read == 320000);

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

	float_t REF_SOUND_PRESSURE = 32767.;

	const char *filename = "speak_32000Hz_16bitsPCM_10s.raw";
	FILE *ptr;
	AcousticIndicatorsData acousticIndicatorsData;
    ai_InitAcousticIndicatorsData(&acousticIndicatorsData);

	int16_t shortBuffer[4096];

	// open file
	ptr = fopen(filename, "rb");
	if (ptr == NULL) {
		printf("Error opening audio file\n");
		exit(1);
	}

  int total_read = 0;
	int read = 0;

  float leqs[10];
  float expected_laeqs[10] = {-31.36, -33.74, -33.06,-33.61,-43.66, -29.97, -35.53, -34.13, -37.07, -37.20};

  int leqId = 0;

	while(!feof(ptr)) {
		read = fread(shortBuffer, sizeof(int16_t), sizeof(shortBuffer) / sizeof(int16_t), ptr);
    total_read+=read;
		// File fragment is in read array
		// Process short sample
		int sampleCursor = 0;
		do {
			int maxLen = ai_GetMaximalSampleSize(&acousticIndicatorsData);
			int sampleLen = (read - sampleCursor) < maxLen ? (read - sampleCursor) : maxLen;
			float_t leq;
			if(ai_AddSample(&acousticIndicatorsData, sampleLen, shortBuffer + sampleCursor, &leq,REF_SOUND_PRESSURE, true)) {
        mu_assert("Too much iteration, more than 10s in file or wrong sampling rate", leqId < 10);
        leqs[leqId++] = leq;
			}
			sampleCursor+=sampleLen;
		} while(sampleCursor < read);
	}
  mu_assert("Wrong number of parsed samples", total_read == 320000);

  // Check expected leq

  for(int second = 0; second < 10; second++) {
    sprintf(mu_message, "Wrong lAeq on %d second expected %f dB got %f dB", second, expected_laeqs[second], leqs[second]);
    mu_assert(mu_message, fabs(expected_laeqs[second] - leqs[second]) < 0.1);
  }
  return 0;
}

static char * all_tests() {
   mu_run_test(test_leq_32khz);
   mu_run_test(test_laeq_32khz);
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
