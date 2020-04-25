/**------------------------------------------------------------------------------
 *
 *  Compute and display the Total Harmonic Distortion on the Microsoft MXChip IoT DevKit.
 *
 *  @file MXChipTHD.ino
 *
 *  @brief Compute and display the Total Harmonic Distortion on the Microsoft MXChip IoT DevKit.
 * 
 * BSD 3-Clause License 
 *
 * Copyright (c) Unité Mixte de Recherche en Acoustique Environnementale (univ-gustave-eiffel)
 * All rights reserved.
 *
 *----------------------------------------------------------------------------*/

/*
 * MXChip and Arduino native headers.
 */
#include "OledDisplay.h"
#include "AudioClassV2.h"

/*
 * noisesensor header
 */
#include "acoustic_indicators.h"

/*
 * The audio sample rate used by the microphone. 
 * Only 32000 and 48000 Hz are supported
 */
#define SAMPLE_RATE 32000

#define SAMPLE_SIZE 16

#define SAMPLE_BYTE_SIZE 2

// AUDIO_CHUNK_SIZE is 512 bytes
// A sample is 2 bytes (16 bits)
// raw_audio_buffer contains 128 short left samples and 128 short right samples
// We keep only left samples
#define MAX_WINDOW_SIZE 128

// Ref sound pressure for -26 dBFS @ 94 dB
// pow(10,((-26-94)/20.0) / sqrt(2))
#define REF_SOUND_PRESSURE 0.00005719516442989919116721836411799

// audio sensor lib instance
AcousticIndicatorsData* acoustic_indicators = NULL;

// MXChip audio controler
AudioClass& Audio = AudioClass::getInstance();

// Audio buffer used by MXChip audio controler
static char raw_audio_buffer[AUDIO_CHUNK_SIZE];

static float last_leq_fast = 0.f;

static float last_printed = 0.f;
/**
 * Called by AudioClass when the audio buffer is full
 */
void recordCallback(void)
{
  int length = Audio.readFromRecordBuffer(raw_audio_buffer, AUDIO_CHUNK_SIZE);
  int sample_index = 0;
  int maxLen = ai_get_maximal_sample_size(acoustic_indicators);
  while(sample_index < length)
  {
    int window_length = min(length - sample_index, maxLen);
    int res = ai_add_sample(acoustic_indicators, window_length, (int8_t*)(raw_audio_buffer + sample_index));
    if (res == AI_FEED_FAST || res == AI_FEED_COMPLETE) {
        // If 125ms or 1s analysis is complete
        last_leq_fast = acoustic_indicators->last_leq_fast;
        maxLen = ai_get_maximal_sample_size(acoustic_indicators);
    }
    sample_index += window_length;
  }
}

void setup(void)
{
  Screen.init();

  acoustic_indicators = ai_new_acoustic_indicators_data();
  
  int a_filter = 0;         // Usage of A weighting filter
  int compute_spectrum = 1; // Run FFT computation to have spectrum bands
  int use_tukey_window = 1; // Apply a tukey window in order to reduce frequency analysis leaks
  int mono = 0;  // is audio stream is mono or stereo

  ai_init_acoustic_indicators_data(acoustic_indicators, a_filter, compute_spectrum, REF_SOUND_PRESSURE, use_tukey_window, AI_SAMPLE_RATE_32000, "S16_LE", 0);
  ai_SetTukeyAlpha(acoustic_indicators, 1.0); // Use Hann window instead of tukey
  Audio.format(SAMPLE_RATE, SAMPLE_SIZE);
  // disable automatic level control
  Audio.setPGAGain(0x3F);
  
  // Start to record audio data
  Audio.startRecord(recordCallback);
  
  printIdleMessage();
}

void loop(void)
{
  if(last_leq_fast != last_printed) {
    last_printed = last_leq_fast;
    char buf[100];
    sprintf(buf, "%.2f dB", last_leq_fast);
    Screen.print(0, buf);
  }
}

void printIdleMessage()
{
  Screen.clean();
  Screen.print(0, "Awaiting audio");
}
