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
#include "RGB_LED.h"

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

#define RGB_LED_BRIGHTNESS 32

static int cellLower; // 1000 Hz frequency band start on FFT array
static int cellUpper; // 1000 Hz frequency band end on FFT array

Thread thread;

RGB_LED rgbLed;

// audio sensor lib instance
AcousticIndicatorsData* acoustic_indicators = NULL;

// MXChip audio controler
AudioClass& Audio = AudioClass::getInstance();

// Audio buffer used by MXChip audio controler
static char raw_audio_buffer[AUDIO_CHUNK_SIZE];

static int64_t sample_index = 0;

static int data_to_process = 0;

static boolean do_print = false;

/**
 * Called by AudioClass when the audio buffer is full
 */
void recordCallback(void)
{
  sample_index += AUDIO_CHUNK_SIZE / SAMPLE_BYTE_SIZE;
  if(data_to_process > 0) {
    rgbLed.setColor(RGB_LED_BRIGHTNESS, 0, 0);
  } else {
    rgbLed.setColor(0, RGB_LED_BRIGHTNESS, 0);
  }
  if(sample_index > 2.0 * SAMPLE_RATE) {
    data_to_process = Audio.readFromRecordBuffer(raw_audio_buffer, AUDIO_CHUNK_SIZE);
  }
}

void setup(void)
{
  Screen.init();

  // Compute target frequency range  
  int SAMPLING = (int)(0.125 * SAMPLE_RATE);
  double target_frequency = 1000.0;
  double freq_by_cell = SAMPLE_RATE / SAMPLING;
  double f_lower = target_frequency * pow(10, -1. / 20.);
  double f_upper = target_frequency * pow(10, 1. / 20.);
  int cell_floor = int(ceil(f_lower / freq_by_cell));
  int cell_ceil = min(SAMPLING - 1, int(floor(f_upper / freq_by_cell)));
  cellLower = min(cell_floor, cell_ceil);
  cellUpper = max(cell_floor, cell_ceil);

  acoustic_indicators = ai_new_acoustic_indicators_data();
  
  int a_filter = 0;         // Usage of A weighting filter
  int compute_spectrum = 0; // Run FFT computation to have spectrum bands
  int use_tukey_window = 0; // Apply a tukey window in order to reduce frequency analysis leaks
  int mono = 0;  // is audio stream is mono or stereo

  ai_init_acoustic_indicators_data(acoustic_indicators, a_filter, compute_spectrum, REF_SOUND_PRESSURE, use_tukey_window, AI_SAMPLE_RATE_32000, "S16_LE", 0);

  Audio.format(SAMPLE_RATE, SAMPLE_SIZE);

  // disable automatic level control
  Audio.setPGAGain(0x3E);
  
  // Start to record audio data
  Audio.startRecord(recordCallback);
  
  Screen.clean();
  Screen.print(0, "Awaiting audio");

  thread.start(display_leq_thread);
}

void display_leq_thread() {
  while(true) {
    if(do_print) {
      do_print = false;
      char buf[100];
      sprintf(buf, "%.2f dB(A)", acoustic_indicators->last_leq_fast);
      Screen.print(0, buf);
    } else {
      delay(250.0);
    }
  }
}

void loop(void)
{
  if(data_to_process > 0) {
    int length = data_to_process;
    int sample_index = 0;
    while(sample_index < length)
    {
      const int maxLen = ai_get_maximal_sample_size(acoustic_indicators);
      const int window_length = min(length - sample_index, maxLen);
      const int res = ai_add_sample(acoustic_indicators, window_length, (int8_t*)(raw_audio_buffer + sample_index));
      if (res == AI_FEED_COMPLETE) {
          // analysis is complete
          do_print = true;
      }
      sample_index += window_length;
    }
    data_to_process = 0;
  }
}

