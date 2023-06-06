import time

import tensorflow as tf
import numpy as np
import io
import csv
import soundfile as sf
import sys
import math
import resampy


# Find the name of the class with the top score when mean-aggregated across frames.
def class_names_from_csv(class_map_csv_text):
  """Returns list of class names corresponding to score vector."""
  class_names = []
  with tf.io.gfile.GFile(class_map_csv_text) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      class_names.append(row['display_name'])

  return class_names



def main(argv):
  assert argv, 'Usage: inference.py <wav file> <wav file> ...'

  # Download the model to yamnet.tflite
  interpreter = tf.lite.Interpreter('yamnet.tflite')

  input_details = interpreter.get_input_details()
  waveform_input_index = input_details[0]['index']
  output_details = interpreter.get_output_details()
  scores_output_index = output_details[0]['index']
  embeddings_output_index = output_details[1]['index']
  spectrogram_output_index = output_details[2]['index']

  for file_name in argv:
    # Decode the WAV file.
    wav_data, sr = sf.read(file_name, dtype=np.int16)
    assert wav_data.dtype == np.int16, 'Bad sample type: %r' % wav_data.dtype
    waveform = wav_data / 32768.0  # Convert to [-1.0, +1.0]
    waveform = waveform.astype('float32')

    # Convert to mono and the sample rate expected by YAMNet.
    if len(waveform.shape) > 1:
      waveform = np.mean(waveform, axis=1)

    sample_rate = 16000
    if sr != sample_rate:
      waveform = resampy.resample(waveform, sr, sample_rate)
    # apply gain
    max_value = max(1e-12, float(np.max(np.abs(waveform))))
    gain = 10 * math.log10(1 / max_value)
    max_gain = 20
    print("Max gain %.2f signal max value gain %.2f " % (max_gain, gain))
    gain = min(max_gain, gain)
    waveform *= 10 ** (gain / 10.0)

    deb = time.time()
    interpreter.resize_tensor_input(waveform_input_index, [len(waveform)],
                                    strict=True)
    interpreter.allocate_tensors()
    interpreter.set_tensor(waveform_input_index, waveform)
    interpreter.invoke()
    scores, embeddings, spectrogram = (
        interpreter.get_tensor(scores_output_index),
        interpreter.get_tensor(embeddings_output_index),
        interpreter.get_tensor(spectrogram_output_index))
    print(scores.shape, embeddings.shape, spectrogram.shape)
    print("Computed in %.3f seconds" % (time.time() - deb))
    # Scores is a matrix of (time_frames, num_classes) classifier scores.
    # Average them along time to get an overall classifier output for the clip.
    prediction = np.max(scores, axis=0)
    # Report the highest-scoring classes and their scores.
    class_names = class_names_from_csv('yamnet_class_threshold_map.csv')
    top5_i = np.argsort(prediction)[::-1][:5]
    print(file_name, '(%.2f s)' % (len(waveform) / sample_rate), ':\n' +
          '\n'.join('  {:12s}: {:.3f}'.format(class_names[i], prediction[i])
                    for i in top5_i))


if __name__ == '__main__':
  main(sys.argv[1:])
