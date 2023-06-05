# Copyright 2019 The TensorFlow Authors All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Inference demo for YAMNet."""
from __future__ import division, print_function

import sys
import time
import numpy as np
import resampy
import soundfile as sf
import tensorflow as tf

import yamnet.params as yamnet_params
from yamnet import yamnet as yamnet_model
import math

def main(argv):
  assert argv, 'Usage: inference.py <wav file> <wav file> ...'

  params = yamnet_params.Params()
  yamnet = yamnet_model.yamnet_frames_model(params)
  yamnet.load_weights('yamnet.h5')
  yamnet_classes = yamnet_model.class_names('yamnet_class_map.csv')

  for file_name in argv:
    # Decode the WAV file.
    wav_data, sr = sf.read(file_name, dtype=np.int16)
    assert wav_data.dtype == np.int16, 'Bad sample type: %r' % wav_data.dtype
    waveform = wav_data / 32768.0  # Convert to [-1.0, +1.0]
    waveform = waveform.astype('float32')

    # Convert to mono and the sample rate expected by YAMNet.
    if len(waveform.shape) > 1:
      waveform = np.mean(waveform, axis=1)
    if sr != params.sample_rate:
      waveform = resampy.resample(waveform, sr, params.sample_rate)
    # apply gain
    max_value = max(1e-12, float(np.max(np.abs(waveform))))
    gain = 10 * math.log10(1 / max_value)
    max_gain = 20
    print("Max gain %.2f signal max value gain %.2f " % (max_gain, gain))
    gain = min(max_gain, gain)
    waveform *= 10 ** (gain / 10.0)

    # Predict YAMNet classes.
    deb = time.time()
    scores, embeddings, spectrogram = yamnet(waveform)
    print("Computed in %.3f seconds" % (time.time() - deb))
    # Scores is a matrix of (time_frames, num_classes) classifier scores.
    # Average them along time to get an overall classifier output for the clip.
    prediction = np.max(scores, axis=0)
    # Report the highest-scoring classes and their scores.
    top5_i = np.argsort(prediction)[::-1][:5]
    print(file_name, ':\n' +
          '\n'.join('  {:12s}: {:.3f}'.format(yamnet_classes[i], prediction[i])
                    for i in top5_i))


if __name__ == '__main__':
  main(sys.argv[1:])
