#define _USE_MATH_DEFINES
#undef __STRICT_ANSI__
#include "kiss_fft.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "minunit.h"

#define SAMPLES 22050

#define MIN(a,b) (((a)<(b))?(a):(b))
#define MAX(a,b) (((a)>(b))?(a):(b))

int tests_run = 0;
char mu_message[256];

static char* test1khz() {
	const int sampleRate = 33000;
	const int window = 3300;
	double powerRMS = 2500; // 90 dBspl
	float signalFrequency = 1000;
	double powerPeak = powerRMS * sqrt(2);

	kiss_fft_cpx audio[SAMPLES];

	for (int s = 0; s < SAMPLES; s++) {
		double t = s * (1 / (double)sampleRate);
        kiss_fft_scalar pwr = (sin(2 * M_PI * signalFrequency * t) * (powerPeak));
		audio[s].r = pwr;
		audio[s].i = 0;
	}

	kiss_fft_cfg cfg = kiss_fft_alloc(window, 0, NULL, NULL);

	kiss_fft_cpx fft_out[SAMPLES];

	kiss_fft(cfg, audio, fft_out);

	int freqBand = (int)round(signalFrequency / (sampleRate / (double)window));

	double rms = (2. / window * sqrt(((double)fft_out[freqBand].r * (double)fft_out[freqBand].r + (double)fft_out[freqBand].i * (double)fft_out[freqBand].i))) / sqrt(2);

	kiss_fft_free(cfg);

  sprintf(mu_message, "FFT result is wrong expected %.2f got %.2f ", powerRMS, (double)(fft_out[freqBand].r));
	mu_assert(mu_message, abs(rms - powerRMS) < 0.1);
}


static char * all_tests() {
   mu_run_test(test1khz);
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
