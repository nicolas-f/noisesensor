/*--------------------------------------------------------------------------

              j]_                   .___                                   
._________    ]0Mm                .=]MM]=                                  
M]MM]MM]M]1  jMM]P               d]-' NM]i                                 
-~-~   4MM1  d]M]1              d]'   jM]'                                 
       j]MT .]M]01       d],  .M]'    d]#                                  
       d]M1 jM4M]1  .,  d]MM  d]I    .]M'                                  
       ]0]  M/j]0(  d]L NM]f d]P     jM-                                   
       M]M .]I]0M  _]MMi -' .]M'                                           
       M]0 jM MM]  jM-M>   .]M/                                            
       ]0F MT ]M]  M>      d]M1        .,                                  
      j0MT.]' M]M j]1 .mm .]MM ._d]_,   J,                                 
      jM]1jM  ]01 =] .]M/ jM]Fd]M]MM]   .'                                 
      j]M1#T .M]1.]1 jM]' M]0M/^ "M]MT  j         .",    .__,  _,-_        
      jMM\]' J]01jM  M]M .]0]P    ]0]1  i         1 1   .'  j .'  "1       
      j]MJ]  jM]1]P .]M1 jMMP     MM]1  I        J  t   1   j J    '       
      =M]dT  jM]q0' dM]  M]MT     ]MM  j        j   j  j    J 1            
      ]M]M`  j]0j#  ]MF  ]M]'    .M]P  J       .'   j  J  .J  4_,          
      M]0M   =MM]1 .M]'  MM]     jM](  1       r    j  1  --,   "!         
      ]0MT   ]M]M  jM@   ]M]     M]P  j       J     j j     4     1        
      MM]'   M]0P  j]1  .M]M    j]M'  J      j'     ",?     j     1        
     _]M]    M]0`  jM1 .MNMM,  .]M'   1     .'       11     1    j'        
     jM]1   jM]@   j]L_]'?M]M__MP'    \     J        1G    J    .'         
     j]0(   jM]1   "M]P'  "N]M/-      "L__J L________'?L__- *__,'          
     "-'    "--                                                            
                                                                           
----------------------------------------------------------------------------

Copyright (c) <2016>, <Wi6labs>
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of the wi6labs nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL WI6LABS BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.*/


//---------------------------How to use it ------------------------------------

//Configure the RESOLUTION_OUTPUT, this is the RESOLUTION_OUTPUT for each
//     sample, if RESOLUTION_OUTPUT is more than 8 bits, you will consume
//     twice more memory.
//Call audio_init()

// debug #####################################################################
#define LOG_MODULE "AUDIO_AN"
#ifdef AUDIO_AN_TRACE
#define TRACE_LEVEL 3 //AUDIO_AN_TRACE
#else
#define TRACE_LEVEL 3
#endif

// include ###################################################################
#include <stdio.h>
#include <stdlib.h>
#include "common_debug.h"
#include "lib/list.h"
#include "lib/memb.h"
#include "uart2.h"
#include "i2s.h"
#include "audio_analyzer.h"
#include "arm_math.h"
#include "arm_const_structs.h"
#include "huffman_dict.h"
#include "third_octave_const.h"
#include <math.h>
#include <float.h>


// global #####################################################################
///@brief rx message list
LIST(g_buf_list);
#ifdef DMA_MODE
static uint8_t g_rx_buff[COMPLETE_NUMBER_OF_SAMPLE*SIZE_SAMPLE];      // Table for DMA Rx debug
static bool g_buff_cplt = FALSE;                             // first half of DMA buffer is full
#endif

//#define AUDIO_DEBUG

///@brief memb rx structure
#ifdef IT_MODE
MEMB(g_buf_memb, buf_of_buf, NB_BUF);
#endif
#ifdef DMA_MODE
MEMB(g_buf_memb, buf_of_buf, SIZE_SAMPLE*NB_BUF);    // working with half buffer
#endif

//set this flag to use the real FFT
#define USE_RFFT

///@brief the size of the FFT is the number of samples divided by 2
#define FFT_SIZE    ((NUMBER_OF_SAMPLE/2))

///@brief size of a buffer after the fft magnitude
#define TREATED_BUFFER_SIZE   32

///@brief size of the DB sample in the chain
#define DB_SCALE_SAMPLE_SIZE   29

///@brief size of the QUANTIZATION sample in the chain
#define QUANT_SAMPLE_SIZE      29

///@brief size of the DELTA compression sample in the chain
#define DELTA_SAMPLE_SIZE     29

///@brief size of the HUFFMAN input
#define HUFFMAN_SAMPLE_SIZE   (29*NB_WINDOW)

///@brief Quantized word size
#define QUANTIZED_WORD_SIZE         8

//debug flags
//#define PRINT_FFT_OUTPUT
//#define PRINT_MAGNITUDE_OUTPUT
#define PRINT_DB_SCALE
#define PRINT_QUANTIFICATION
//#define PRINT_THIRD_OCTAVE
#define PRINT_DELTA_ENCODING
#define PRINT_HUFFMAN
#define PRINT_OUTPUT


#define TEST_SIGNALS


///@brief coplement à 2 buffered data in 16bits mode
q15_t g_16bit_data[NUMBER_OF_SAMPLE];



#ifdef TEST_SIGNALS
#define SINUS
//test array
static q15_t g_sintest[NUMBER_OF_SAMPLE];
#endif

//event used when some data are ready to be sent to the modem
process_event_t g_audio_data_ready_ev;

//process called by the event g_audio_data_ready_ev
struct process *g_data_ready_process = NULL;

// Events
process_event_t PRINT_BUFF;                      // Buff full, ready to display


//used to know if the aduio has started sampling
static uint8_t g_audio_started = 0;

//normalization factors
static float g_fft_norm[NB_WINDOW][2];


///@brief declare the process with a string attribute
PROCESS(audio_analyzer_process, "Audio analyzer process");
PROCESS(display_process, "Display process");


// internal function ##########################################################

static int audio_process_data (uint8_t *recBuff, uint16_t size_buff);


////////////////////////////////////////////////////////////////////////////////
/// This function is used to print float
///
/// @return - a pointer on the buffer
////////////////////////////////////////////////////////////////////////////////
void printfloat(float v, int decimalDigits)
{
  int i = 1;
  int intPart, fractPart;
  for (;decimalDigits!=0; i*=10, decimalDigits--);
  intPart = (int)v;
  fractPart = (int)((v-(float)(int)v)*i);
  if(fractPart < 0) fractPart *= -1;
  printf("%i,%i", intPart, fractPart);
}

#define PRINTFLOAT(FLOAT, DIGITS) printfloat(FLOAT, DIGITS)


////////////////////////////////////////////////////////////////////////////////
/// This function find in the list a new buffer
///
/// @return - a pointer on the buffer
////////////////////////////////////////////////////////////////////////////////
static buf_of_buf * get_rx_buffer(void)
{
  buf_of_buf * rx_buff = list_tail(g_buf_list);

  if(rx_buff == NULL) {
    rx_buff = memb_alloc(&g_buf_memb);

    if(rx_buff == NULL) {
      #ifdef IT_MODE
      sai_it_stop();
      #endif
      PRINTD("no RX fifo \n\r");
      return NULL;
    }
    rx_buff->pending = 0;

    list_add(g_buf_list, rx_buff);

    //this means that the the previous buffer is not treated by the task.
    //Try to get another buffer
  } else if (rx_buff->pending == 1) {
    rx_buff = memb_alloc(&g_buf_memb);

    if(rx_buff == NULL) {
      //delay reception
      PRINTD("no more RX fifo \n\r");
      return NULL;
    }
    rx_buff->pending = 0;
    list_add(g_buf_list, rx_buff);
  }
  return rx_buff;
}


////////////////////////////////////////////////////////////////////////////////
/// Perform the "complement à 2" of the I2S received data
//@ output           : ouput ready buffer
//@ input         : i2s input buffer
////////////////////////////////////////////////////////////////////////////////
void data_16bits_proceed(q15_t *output, uint8_t *input)
{
  uint32_t i;
  uint32_t buff_length = 0;

  //1 : MSB, 0: Medium, 3 LSB
  for (i = 0; i < NUMBER_OF_SAMPLE; i++) {
    buff_length+=4;
    output[i]= (q15_t)(input[buff_length+1]<<8 | input[buff_length]);
  }
}


////////////////////////////////////////////////////////////////////////////////
/// Convert an array of bits to an array of bytes
//@ input_bit        : array of bits of length bitlen
//@ output_byte      : output array of bytes
//@ bitlen           : size in bits of the input
//
//@ return           : size in bytes of the output
////////////////////////////////////////////////////////////////////////////////
uint8_t toBytesarray(Bit * input_bit, uint8_t * output_byte, uint16_t bitlen)
{
  uint8_t byteIndex = 0, bitIndex = 0;
  uint8_t numBytes = bitlen / 8;
  if (bitlen % 8 != 0) numBytes++;


  for (int i = 0; i < bitlen; i++) {
    if (input_bit[i].bit) {
      output_byte[byteIndex] |= (uint8_t)(1 << (7 - bitIndex));
    }

    bitIndex++;
    if (bitIndex == 8) {
      bitIndex = 0;
      byteIndex++;
    }
  }

  return numBytes;
}


////////////////////////////////////////////////////////////////////////////////
/// Perform the FFT and put the result in a buffer
//@ data           : buffer to convert (input/output)
//@ nb_bit         : resolution wanted
//@
////////////////////////////////////////////////////////////////////////////////
uint8_t fft_proceed(q15_t *data, q15_t *tmp_data, q15_t output[NB_WINDOW][FFT_SIZE], uint8_t nb_bit)
{
  //int buff_length;
  uint32_t i;

  ///@brief FFT instance used to configure FFT parameters in real case
  arm_rfft_instance_q15 rfft_instance;

  q15_t *origin_signal_ptr;

  uint8_t ind_frame;
  uint16_t offset = 0;

  if (nb_bit > 32)
  {
    return RESOLUTION_ERROR;
  }
    //1 : MSB, 0: Medium, 3 LSB

    
  if(nb_bit == 16) {

#ifdef TEST_SIGNALS
    float a = 0;
    float b = 0;
    float c = 0;
    float radian;
    q15_t res;
   // printf("g_sintest = ");
    for (i = 0; i < NUMBER_OF_SAMPLE; i++) {
      g_sintest [i] = 0;
  #ifdef SINUS

     /* radian = a/360;
      arm_float_to_q15(&radian, &res, 1);
      g_sintest [i] += arm_sin_q15(res)/10;*/

      radian = b/360;
      arm_float_to_q15(&radian, &res, 1);
      g_sintest [i] += arm_sin_q15(res)/10;
      /*radian = c/360;
      arm_float_to_q15(&radian, &res, 1);
      g_sintest [i] += arm_sin_q15(res)/10;*/
  #else
      radian = a/360;
      arm_float_to_q15(&radian, &res, 1);
      g_sintest [i] += arm_sin_q15(res)/10;

      if(g_sintest [i] > 100) {
        g_sintest [i] = 5000;
      } else {
        g_sintest [i] = -5000;
      }

    /* if((i > 100)&&(i < 500)) {
        g_sintest [i] = 5000;
      } else {
        g_sintest [i] = 0;
      }*/
  #endif // SINUS
    
      a+=360/(32000/400); //echantillonage à 32k; 2kHz equivaut à 16 échantillons par période
      if(a>=360) { a = 0;}

      b+=360/(32000/440); //echantillonage à 32k; 2kHz equivaut à 16 échantillons par période
      if(b>=360) { b = 0;}

      c+=360/(32000/1000); //echantillonage à 32k; 2kHz equivaut à 16 échantillons par période
      if(c>=360) { c = 0;}

      //printf("%d:%d,", i, g_sintest [i]);
    }
   // printf("\n\r");

    origin_signal_ptr = g_sintest;
#else

    origin_signal_ptr = data;

#endif //TEST_SIGNALS

    arm_rfft_init_q15(&rfft_instance, FFT_SIZE ,0 , 1);

    //apply windowing
    /*n_win = floor(1+(length(x)-l_frame)/l_hop); % Number of windows
    X_st = zeros(l_frame, n_win);
    for ind_frame = 1:n_win
        x_frame = x((ind_frame-1)*l_hop+1:(ind_frame-1)*l_hop+l_frame).*w; % Windowing
        X_st(:, ind_frame) = fft(x_frame); % FFT
    end*/


    for (ind_frame = 0; ind_frame < NB_WINDOW; ind_frame++) {
      offset = (ind_frame*FFT_SIZE);
      //NUMBER_OF_SAMPLE is a size in byte.... tmp_data has int16_t type.
      //NUMBER_OF_SAMPLE is half the size of the buffer in byte
      memcpy(tmp_data, (q15_t*)(origin_signal_ptr+offset), NUMBER_OF_SAMPLE);
      memset(tmp_data+FFT_SIZE, 0, NUMBER_OF_SAMPLE);


    /*  if(ind_frame == 1) {
      printf("ind_frame %d--%d FFT_SIZE = %d:", offset, ind_frame, FFT_SIZE);
      for (i = 0; i < NUMBER_OF_SAMPLE; i+=1) {
        //printf("%d vs %d - %d = %d,", i, i+(ind_frame*FFT_SIZE), tmp_data[i],g_sintest[i+(ind_frame*FFT_SIZE)]);
        printf("%d : %d ,", i, tmp_data[i]);
      }
      printf("\n\r");

      }*/
      //Push the receive sample and perform the FFT
      arm_rfft_q15(&rfft_instance, tmp_data, output[ind_frame]);
   }


  /*  for (ind_frame = 0; ind_frame < NB_WINDOW; ind_frame++) {
      for (i = 0; i < FFT_SIZE; i+=1)
      {
        PRINTFLOAT(output[ind_frame][i], 4);
        printf(";");
      }
      printf("\n\r");
    }*/

#ifdef PRINT_FFT_OUTPUT
    uint32_t id;
    printf("FFT output %d: \n\r",FFT_SIZE+1);
    for (ind_frame = 0; ind_frame < NB_WINDOW; ind_frame++) {
      printf("ind_frame %d :", ind_frame);
      for (id = 0; id <FFT_SIZE; id++) {
        printf("%d", output[ind_frame][id]); 
        printf(";");
      }
      printf("\n\r");
    }

#endif //PRINT_FFT_OUTPUT
  }

  return AUDIO_OK;
}

////////////////////////////////////////////////////////////////////////////////
/// Perform the magnitude
//@ bufintput           : input buffer of size samples
//@ bufoutput           : output buffer of size samples
//@return status of the operation
////////////////////////////////////////////////////////////////////////////////
uint8_t magnitude_proceed(q15_t bufintput[NB_WINDOW][FFT_SIZE],
                          float output[NB_WINDOW][FFT_SIZE])
{

  uint8_t ind_frame;
  uint16_t i;
  /*       %% Magnitude spectrogram
  X = abs(X).^2; % Squared magnitude
  X = X/fft_norm; % Normalize to conserve the energy of x
  X = X(1:end/2+1); % Only keep the first half*/

  for (ind_frame = 0; ind_frame < NB_WINDOW; ind_frame++) {
    for (i = 0; i < FFT_SIZE; i++) {
      output[ind_frame][i] = abs(bufintput[ind_frame][i]*bufintput[ind_frame][i]);
    }
  }


#ifdef PRINT_MAGNITUDE_OUTPUT
    uint32_t id;
    printf("MAGNITUDE output %d: \n\r",FFT_SIZE+1);
    for (ind_frame = 0; ind_frame < NB_WINDOW; ind_frame++) {
      printf("ind_frame %d :", ind_frame);
      for (id = 0; id <FFT_SIZE; id++) {
        PRINTFLOAT( output[ind_frame][id], 4); 
        printf(";");
      }
      printf("\n\r");
    }

#endif //PRINT_MAGNITUDE_OUTPUT
  return AUDIO_OK;
}

////////////////////////////////////////////////////////////////////////////////
/// Perform the third octave analysis of the frame
//@ bufintput           : input buffer of size samples
//@ bufoutput           : output buffer of size samples
//@ size                : number of input samples
//@return status of the operation
////////////////////////////////////////////////////////////////////////////////
uint8_t third_octave_analysis_proceed(
                              float bufintput[NB_WINDOW][FFT_SIZE],
                              float bufoutput[NB_WINDOW][TREATED_BUFFER_SIZE],
                              uint16_t size)
{

  uint16_t band, id, sample, ind_frame;

  /* MATLAB code
    X_st is the input --> bufintput
    X_tob is the output

    %% Third-octave bands analysis
    for ind_band = 1:length(H_band) % Filtering band by band
        X_tob(ind_band, :) = H_band{ind_band}*X_st(f_band{ind_band}(1):f_band{ind_band}(2), :);
    end
  */

  for (ind_frame = 0; ind_frame < NB_WINDOW; ind_frame++) {

    //Do the job band by band
    for(band = 0; band < NB_BAND; band++) {
      bufoutput[ind_frame][band] = 0;
      
     // printf("f_band[band][1] - f_band[band][0] = %d \n\r", f_band[band][1] - f_band[band][0]);
     // printf(" H_band_sizes[band] = %d \n\r",  H_band_sizes[band]);


      //lets take all the samples of the band to analysis
      for(id = 0, sample = f_band[band][0]-1; id < H_band_sizes[band]; id++, sample++) {

        //take the sample of the audio input to consider. These sample are the
        //samples defined between f_band[band][0] and f_band[band][1]

        //for example,  f_band_22[2] = {257, 403}; --> 147 elements
        //we have to multiply the H_band_22[147] by the 147 samples of bufintput[257--> 403]

          bufoutput[ind_frame][band] += H_band[band][id]*bufintput[ind_frame][sample];

       /*  if((band == 12)||(band == 13)){
            printf("id= %d, band= %d, ind_frame = %d, f_band[band][0] = %d, f_band[band][1] = %d bufintput[%d][%d] = ", id, band, ind_frame, f_band[band][0], f_band[band][1], ind_frame, sample);
            
            PRINTFLOAT( bufintput[ind_frame][sample], 4); 
            printf("\n\r");
          }*/
      }
      if(bufoutput[ind_frame][band] == 0) {
       bufoutput[ind_frame][band] = 2.2204e-16;
      }
    }

  }

#ifdef PRINT_THIRD_OCTAVE
  uint32_t a;
  printf("third_octave_analysis output : ");
  printf("\n\r");

  for (ind_frame = 0; ind_frame < NB_WINDOW; ind_frame++) {
    printf("ind_frame %d :", ind_frame);
    for (a = 0; a < NB_BAND; a++) {
      PRINTFLOAT( bufoutput[ind_frame][a], 4); 
      printf(";");
    }
    printf("\n\r");
  }
#endif //PRINT_THIRD_OCTAVE

  return AUDIO_OK;
}

////////////////////////////////////////////////////////////////////////////////
/// Perform the db scale of the third octave analysis
//@ bufintput           : input buffer of size samples
//@ bufoutput           : output buffer of size samples
//@ size                : number of samples
//@return status of the operation
////////////////////////////////////////////////////////////////////////////////
uint8_t db_scale_proceed(float bufintput[NB_WINDOW][TREATED_BUFFER_SIZE],
                         float bufoutput[NB_WINDOW][TREATED_BUFFER_SIZE],
                         uint8_t size)
{
  uint16_t id, ind_frame;

  /* MATLAB code
    X_tob = 10*log10(X_tob); % dB scale
  */
  for (ind_frame = 0; ind_frame < NB_WINDOW; ind_frame++) {
    for(id = 0; id < size; id++) {
      bufoutput[ind_frame][id] = 10*log10f(bufintput[ind_frame][id]);
    }
  }

#ifdef PRINT_DB_SCALE
  uint8_t i;
  printf("DB scale output : \n\r");
  for (ind_frame = 0; ind_frame < NB_WINDOW; ind_frame++) {
    printf("ind_frame %d :", ind_frame);
    for (i = 0; i < size; i++) {
      PRINTFLOAT( bufoutput[ind_frame][i], 4);
      printf(";");
    }
    printf("\n\r");
  }
#endif //PRINT_DB_SCALE


  return AUDIO_OK;
}


////////////////////////////////////////////////////////////////////////////////
/// Perform the quantization of the signal
//@ bufintput           : input buffer of size samples (16bits)
//@ bufoutput           : output buffer of size samples (8bits)
//@ size                : number of samples
//@return status of the operation
////////////////////////////////////////////////////////////////////////////////
uint8_t quantization_proceed(float bufintput[NB_WINDOW][TREATED_BUFFER_SIZE],
                              uint8_t bufoutput[NB_WINDOW][TREATED_BUFFER_SIZE],
                              uint8_t size)
{
  uint16_t ind_frame;
  uint8_t id;
  float norm_buffer[NB_WINDOW][QUANT_SAMPLE_SIZE];


  if(size > QUANT_SAMPLE_SIZE) {
    return AUDIO_ERROR;
  }


  for (ind_frame = 0; ind_frame < NB_WINDOW; ind_frame++) {

    /* MATLAB code
      bufintput: X_tob
      bufoutput: X_tob

      q_norm(1) = min(min(X_tob));
      X_tob = X_tob-q_norm(1); % Everything has to be positive
      q_norm(2) = max(max(X_tob));
      X_tob = round((2^(q-1)-1)*X_tob./q_norm(2)); % Normalisation + Quantization
    */

    //get the minimum value of the input buffer
    g_fft_norm[ind_frame][0] = FLT_MAX;
    for(id = 0; id < size; id++) {
      if(g_fft_norm[ind_frame][0] > bufintput[ind_frame][id]) {
        g_fft_norm[ind_frame][0] = bufintput[ind_frame][id];
      }
    }

    //remove the min offset to the input
    for(id = 0; id < size; id++) {
      bufoutput[ind_frame][id] = bufintput[ind_frame][id] - g_fft_norm[ind_frame][0];
    }

    //get the max value of the sample
    g_fft_norm[ind_frame][1] = 0;
    for(id = 0; id < size; id++) {
      if(g_fft_norm[ind_frame][1] < bufoutput[ind_frame][id]) {
        g_fft_norm[ind_frame][1] = bufoutput[ind_frame][id];
      }
    }

    //perform the normalization
    for(id = 0; id < size; id++) {
      //switch to float
      norm_buffer[ind_frame][id] = (bufoutput[ind_frame][id] * 127);
      //((2^(QUANTIZED_WORD_SIZE-1))-1));
      norm_buffer[ind_frame][id] /= g_fft_norm[ind_frame][1];
      bufoutput[ind_frame][id] = (uint8_t)norm_buffer[ind_frame][id];
    }


    //convert float to q7
   // arm_float_to_q7(norm_buffer[ind_frame], bufoutput[ind_frame], size);

  }

#ifdef PRINT_QUANTIFICATION
    uint8_t i;
    printf("QUANTIZED output ");
    for (ind_frame = 0; ind_frame < NB_WINDOW; ind_frame++) {
      printf("ind_frame %d :", ind_frame);
      printf(" norm[0] = ");
      PRINTFLOAT( g_fft_norm[ind_frame][0], 4);
      printf(" norm[1] = ");
      PRINTFLOAT( g_fft_norm[ind_frame][1], 4);
      printf("\n\r");

      for (i = 0; i < size; i++) {

        //PRINTFLOAT( norm_buffer[ind_frame][i], 4);

        printf("%d;", bufoutput[ind_frame][i]);
      }
      printf("\n\r");
    }
#endif //PRINT_QUANTIFICATION


  return AUDIO_OK;
}

////////////////////////////////////////////////////////////////////////////////
/// Perform the delat encoding of the signal
//@ bufin           : input buffer of size samples (8bits)
//@ bufout           : ouput buffer of size samples (8bits)
//@ size                : number of samples
//@return status of the operation
////////////////////////////////////////////////////////////////////////////////
uint8_t delta_encoding_proceed(uint8_t bufin[NB_WINDOW][TREATED_BUFFER_SIZE],
                               q7_t bufout[NB_WINDOW][TREATED_BUFFER_SIZE],
                                uint8_t size)
{
  uint8_t i;
  uint16_t ind_frame;

  if(size > DELTA_SAMPLE_SIZE) {
    return AUDIO_ERROR;
  }

  /* MATLAB code
    bufintput = X_tob
    bufoutput = X_delta

    X_delta = zeros(size(X_tob));
    prev = zeros(size(X_tob, 1), 1);
    for ind_frame = 1:size(X_tob, 2);
        X_delta(:, ind_frame) = X_tob(:, ind_frame) - prev;
        prev = X_tob(:, ind_frame);
    end
  */



  memcpy(bufout[0], bufin[0], TREATED_BUFFER_SIZE);

  for (ind_frame = 1; ind_frame < NB_WINDOW; ind_frame++) {
    memcpy(bufout[ind_frame], bufin[ind_frame], TREATED_BUFFER_SIZE);
    for(i = 0; i < size; i++)
    {
      bufout[ind_frame][i] = bufout[ind_frame][i] - bufout[ind_frame-1][i];
    }
  }
#ifdef PRINT_DELTA_ENCODING
  printf("DELTA_ENCODING output %d: \n\r", size);
  for (ind_frame = 0; ind_frame < NB_WINDOW; ind_frame++) {
    printf("ind_frame %d :", ind_frame);
    for (i = 0; i < size; i++) {
      printf("%d;", bufout[ind_frame][i]);
    }
    printf("\n\r");
  }
#endif //PRINT_DELTA_ENCODING

  return AUDIO_OK;
}

////////////////////////////////////////////////////////////////////////////////
/// Perform all the operation to perform the audio encoding
//@ data           : buffer to convert
//@ nb_bit         : resolution wanted
// return the size in bits of the output
////////////////////////////////////////////////////////////////////////////////
uint16_t Huffman_proceed(q7_t bufinout[NB_WINDOW][TREATED_BUFFER_SIZE],
                        Bit * output_buf, uint8_t size)
{
  q7_t buf[NB_WINDOW*DELTA_SAMPLE_SIZE];
  uint16_t window, d_i, a, offset;
  q7_t i;

  //start by serializing the data
  for(window = 0; window < NB_WINDOW; window++) {
    memcpy(&buf[window*DELTA_SAMPLE_SIZE], bufinout[window],
            DELTA_SAMPLE_SIZE);
  }



  /*
  for ind_sym_data in range(0,X_delta.shape[0]):
    for ind_sym_dict in range(0,len(d_sym)): # Terrible method
      if X_delta[ind_sym_data] == d_sym[ind_sym_dict]:
        X_huff = np.append(X_huff, d_code[ind_sym_dict])
        X_huff_l = X_huff_l+len(d_code[ind_sym_dict])*/



  offset = 0;
  //parse all the ements of the data
  for(d_i = 0; d_i < NB_WINDOW*DELTA_SAMPLE_SIZE; d_i++) {
    //try to find the symbol
    for(i = -127; i < 128; i++) {
      if(buf[d_i] == i) {
        //replace the symbol by the bit stream
        for (a = 0; a < huffman_dict_size[i+128]; a++) {
          output_buf[offset] = huffman_dict[i+128][a];
          offset++;
        }
        break;
      }
    }
  }

#ifdef PRINT_HUFFMAN
  printf("huffman output (%d) : ", offset);
  for(a = 0; a < offset; a++) {
    printf("%d",output_buf[a]);
  }
  printf("\n\r");
#endif //PRINT_HUFFMAN

  return offset;


//  return Huffman_Compress((uint8_t*)buf, output_buf, HUFFMAN_SAMPLE_SIZE);
}



////////////////////////////////////////////////////////////////////////////////
/// Perform all the operation to perform the audio encoding
//@ data           : buffer to convert
//@ nb_bit         : resolution wanted
////////////////////////////////////////////////////////////////////////////////
uint8_t audio_proceed(q15_t *data, uint8_t nb_bit,  audio_data_t *audio_data)
{
  uint8_t ret;
  uint16_t bitlen;

 /* uint32_t main_buffer[NB_WINDOW*NUMBER_OF_SAMPLE];
  float * f_bufb = (float *)main_buffer;
  q15_t * q15_bufa = (q15_t *)main_buffer;*/

  q15_t q15_bufa[NB_WINDOW][FFT_SIZE];
  float f_bufb[NB_WINDOW][NUMBER_OF_SAMPLE];
  float f_bufa[NB_WINDOW][TREATED_BUFFER_SIZE];
  uint8_t u8_bufa[NB_WINDOW][TREATED_BUFFER_SIZE];
  q7_t q7_bufa[NB_WINDOW][TREATED_BUFFER_SIZE];
  Bit output_buf[MAX_NB_BIT_FOR_HUFFMAN];


  //use this huge buffer for temp treatments in the fft
  q15_t * tmp_data = (q15_t *)f_bufb;
  //start by calculating the fft and the magnitude of the sample
  ret = fft_proceed(data, tmp_data, q15_bufa, nb_bit);
  if(ret != AUDIO_OK) {
    return ret;
  }

  //start by calculating the fft and the magnitude of the sample
  ret = magnitude_proceed(q15_bufa, f_bufb);
  if(ret != AUDIO_OK) {
    return ret;
  }


  //Third octave analysis (bufa as output)
  ret = third_octave_analysis_proceed(f_bufb, f_bufa, FFT_SIZE);
  if(ret != AUDIO_OK) {
    return ret;
  }

  //push it in db scale (bufa as input, bufb as output)
  ret = db_scale_proceed(f_bufa, f_bufb, DB_SCALE_SAMPLE_SIZE);
  if(ret != AUDIO_OK) {
    return ret;
  }

  //Quantization (bufb as input, bufa as output)
  ret = quantization_proceed(f_bufb, u8_bufa, QUANT_SAMPLE_SIZE);
  if(ret != AUDIO_OK) {
    return ret;
  }

  //Delta encoding along time dimension
  ret = delta_encoding_proceed(u8_bufa, q7_bufa, DELTA_SAMPLE_SIZE);
  if(ret != AUDIO_OK) {
    return ret;
  }

  //Huffman encoding
  bitlen = Huffman_proceed(q7_bufa, output_buf, HUFFMAN_SAMPLE_SIZE);
  if(bitlen == 0) {
    return AUDIO_ERROR;
  }

  audio_data->len = toBytesarray(output_buf, audio_data->data, bitlen);


  audio_data->norm_factor[0][0] = (uint8_t)g_fft_norm[0][0];
  audio_data->norm_factor[0][1] = (uint8_t)g_fft_norm[0][1];
  audio_data->norm_factor[1][0] = (uint8_t)g_fft_norm[1][0];
  audio_data->norm_factor[1][1] = (uint8_t)g_fft_norm[1][1];


#ifdef PRINT_OUTPUT
  uint16_t i;

  printf("final output (%d bytes): ", audio_data->len);
  for (i = 0; i < audio_data->len; i++) {
    printf("%02x", audio_data->data[i]);
  }

  printf("norm[0] : %d-%d / norm[1]%d-%d",
              audio_data->norm_factor[0][0], audio_data->norm_factor[0][1],
                audio_data->norm_factor[1][0], audio_data->norm_factor[1][1]); 

  printf("\n\r");
#endif //PRINT_OUTPUT

  return AUDIO_OK;
}



////////////////////////////////////////////////////////////////////////////////
/// Convert data and display then on uart interface
//@ data           : buffer to convert and display
//@ nb_bit         : resolution wanted
////////////////////////////////////////////////////////////////////////////////
uint8_t convert_and_display(uint8_t *data, uint8_t nb_bit)
{
  
  if (nb_bit > 32)
  {
    return RESOLUTION_ERROR;
  }
  

  //1 : MSB, 0: Medium, 3 LSB

  // CPL2 and display, data on I2S transit with CPL2
  for (int buff_length = 0; buff_length < LITTLE_BUFFER_SIZE; buff_length+=SIZE_SAMPLE)
  {
    if (RESOLUTION_OUTPUT <= 8)
    {
      if(data[buff_length+1] == 0xFF) {
        data[buff_length+1] = 0;
      }
      // 8 bits sample
      uart2_putc(data[buff_length+1]);
    }
    else if (RESOLUTION_OUTPUT <= 16)
    {
      // 16 bits sample
      uart2_putc(data[buff_length+1]);
      uart2_putc(data[buff_length]);
    }
    else
    {
      // 24 bits sample
      uart2_putc(data[buff_length+1]);
      uart2_putc(data[buff_length]);
      uart2_putc(data[buff_length+3]);
    }
  }
  return AUDIO_OK;
}


////////////////////////////////////////////////////////////////////////////////
/// Display process
/// Only for display data on terminal
///////////////////////////////////////////////////////////////////////////////
PROCESS_THREAD(display_process, ev, data)
{
  PROCESS_BEGIN();
  buf_of_buf *rx_buff;
  static audio_data_t audio_data;
  PRINTD("Hello process display\n\r");
  
  while(1)
  {
    PROCESS_WAIT_EVENT();
    if (ev == PRINT_BUFF)
    {
      // read through the whole list, can be more than one buff to display
      for(rx_buff = list_head(g_buf_list); rx_buff != NULL; rx_buff = list_item_next(rx_buff))
      {
        if (rx_buff->pending == 1)
        {

#ifdef AUDIO_DEBUG
          convert_and_display(rx_buff->data, RESOLUTION_OUTPUT);
#endif
          data_16bits_proceed(g_16bit_data, rx_buff->data);

          if(audio_proceed(g_16bit_data, RESOLUTION_OUTPUT, &audio_data)
                         == AUDIO_OK) {
            process_post(g_data_ready_process,
                         g_audio_data_ready_ev,
                         &audio_data);
          }
          rx_buff->pending = 0;             // free the buffer for futher use
          list_pop(g_buf_list);
          memb_free(&g_buf_memb, rx_buff);
        }
      }
    }
  }
  PROCESS_END();
}

////////////////////////////////////////////////////////////////////////////////
///This function is called to be notified when the audio treatment has been done
///////////////////////////////////////////////////////////////////////////////
void audio_analyser_register_process(struct process * p)
{
  g_data_ready_process = p;
}

////////////////////////////////////////////////////////////////////////////////
/// Main process for audio_analyzer
///////////////////////////////////////////////////////////////////////////////

PROCESS_THREAD(audio_analyzer_process, ev, data)
{
  PROCESS_BEGIN();
  
  uint32_t back_value = 0;     // back value of init function
  buf_of_buf * rx_buff;        // buffer of buffers
  clock_time_t time_start = 0; // timout for starting microphone
  
  PRINT_BUFF = process_alloc_event();
  g_audio_data_ready_ev = process_alloc_event();
   
  back_value = i2s_init(AUDIO_FREQUENCY_32K); // 32K is enough, no need 44K1
  
  //free all buffers
  for(rx_buff = list_head(g_buf_list); rx_buff != NULL; rx_buff = list_item_next(rx_buff))
  {
    list_pop(g_buf_list);
    memb_free(&g_buf_memb, rx_buff);
  }
  
  // wait for the microphone be ready (20ms max)
  time_start = clock_time();
  // delay on number of ticks, 1 tick = 10 ms
  while (clock_time() - time_start < 100);
  
  #ifdef IT_MODE
  sai_set_cplt(audio_process_data);            // register callback function
  #endif
  
  #ifdef DMA_MODE
  sai_set_cplt(audio_process_data);            // register callback complete buffer
  sai_set_half(audio_process_data);            // register callback half buffer
  PRINTD("first call receive DMA\n\r");
  #endif
  
  PRINTD("Bonjour thread audio analyzer, back value vaut %d\n\r", back_value);
  
  while (1)
  {
    PROCESS_WAIT_EVENT();
    if (ev == PROCESS_EVENT_POLL)
    {
      #ifdef IT_MODE
      rx_buff = get_rx_buffer();           // get another free buffer
      if (rx_buff == NULL)
      {
        PRINTD("No more FIFO\n\r");
      }
      else
      {
        i2s_receive_polling_IT(rx_buff, COMPLETE_NUMBER_OF_SAMPLE);
      }
      #endif
      
      #ifdef DMA_MODE
      // Copy local buffer to memb, this is only a half buffer
      rx_buff = get_rx_buffer();           // get another free buffer
      if (rx_buff == NULL)
      {
        PRINTD("No more FIFO\n\r");
      }
      else
      {
        // copy g_rx_buff in the new buffer
        if (g_buff_cplt == TRUE) // second half buffer of the circular buffer
        {
          for(int i=0; i<LITTLE_BUFFER_SIZE; i+=1)
          {
            rx_buff->data[i] = g_rx_buff[i+LITTLE_BUFFER_SIZE];
          }
          g_buff_cplt = FALSE;
        }
        else // first half buffer of the circular buffer
        {
          for(int i=0; i<LITTLE_BUFFER_SIZE; i+=1)
          {
            rx_buff->data[i] = g_rx_buff[i];
          }
          g_buff_cplt = TRUE;
        }
      }
      rx_buff->pending = 1;
      #endif
      
      process_post(&display_process, PRINT_BUFF, rx_buff->data);  // buf to display
    }
  }
  PROCESS_END();
}

////////////////////////////////////////////////////////////////////////////////
/// audio_analyzer process initilialization
///////////////////////////////////////////////////////////////////////////////
void
audio_analyzer_init(void)
{
  process_start(&audio_analyzer_process, NULL);
  process_start(&display_process, NULL);
}

////////////////////////////////////////////////////////////////////////////////
/// Function process receive data. To register in callback function SAI
//@ RecBuff : buffer to write receive data (must be at least size*4 if sampling 32 bits)
//@ size    : number of data to receive (number of sample)
///////////////////////////////////////////////////////////////////////////////
int audio_process_data (uint8_t *recBuff, uint16_t size_buf)
{
  // just poll the process, data already in the buffer of reception
  process_poll(&audio_analyzer_process);
  return 1;
}

////////////////////////////////////////////////////////////////////////////////
/// Start sampling
///////////////////////////////////////////////////////////////////////////////
void audio_start()
{

  #ifdef IT_MODE
  buf_of_buf * rx_buff;     // buffer of buffers
  #endif

  if(g_audio_started == 0) {


    printf("audio_start\n\r");

    #ifdef DMA_MODE
    i2s_receive_DMA(g_rx_buff, COMPLETE_NUMBER_OF_SAMPLE);
    #endif
    
    #ifdef IT_MODE
    rx_buff = get_rx_buffer();           // get another free buffer
    if (rx_buff == NULL)
    {
      PRINTD("No more FIFO\n\r");
    }
    else
    {
      i2s_receive_polling_IT(rx_buff, COMPLETE_NUMBER_OF_SAMPLE);
    }
    #endif

    g_audio_started = 1;

  }
}

////////////////////////////////////////////////////////////////////////////////
/// Stop sampling
///////////////////////////////////////////////////////////////////////////////
#ifdef DMA_MODE
void audio_stop()
{
  if(g_audio_started == 1) {
    printf("audio_stop\n\r");
    g_audio_started = 0;
    sai_dma_stop();
  }
}
#endif





