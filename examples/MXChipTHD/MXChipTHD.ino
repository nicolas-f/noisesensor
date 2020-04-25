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

// Audio buffer provided to QRTone. Samples are
static float scaled_input_buffer[MAX_WINDOW_SIZE];

/**
 * Called by AudioClass when the audio buffer is full
 */
void recordCallback(void)
{
  int length = Audio.readFromRecordBuffer(raw_audio_buffer, AUDIO_CHUNK_SIZE);
  // Convert Stereo short samples to mono float samples
  char* cur_reader = &raw_audio_buffer[0];
  char* end_reader = &raw_audio_buffer[length];
  const int offset = 4; // short samples size + skip right channel
  int sample_index = 0;
  while(cur_reader < end_reader)
  {
    int16_t sample = *((int16_t *)cur_reader);
    scaled_input_buffer[sample_index++] = (float)sample / 32768.0f;
    cur_reader += offset;
  }
  // Push remaining samples
  if(sample_index > 0) {
    // push_samples(scaled_input_buffer, sample_index)
  }
}

void setup(void)
{
  Screen.init();

  acoustic_indicators = ai_new_acoustic_indicators_data();
  
  int a_filter = 0;         // Usage of A weighting filter
  int compute_spectrum = 1; // Run FFT computation to have spectrum bands
  int use_tukey_window = 1; // Apply a tukey window in order to reduce frequency analysis leaks

  ai_init_acoustic_indicators_data(acoustic_indicators, a_filter, compute_spectrum, REF_SOUND_PRESSURE, use_tukey_window, AI_SAMPLE_RATE_32000, "S16_LE", 0);
  ai_SetTukeyAlpha(acoustic_indicators, 1.0); // Use Hann window instead of tukey
  Audio.format(SAMPLE_RATE, SAMPLE_SIZE);
  // disable automatic level control
  // Audio.setPGAGain(0x3F);
  
  // Start to record audio data
  Audio.startRecord(recordCallback);
  
  printIdleMessage();
}

void loop(void)
{
  delay(100);
}

void printIdleMessage()
{
  Screen.clean();
  Screen.print(0, "Awaiting message");
}
