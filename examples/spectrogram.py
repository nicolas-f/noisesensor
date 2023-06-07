from noisesensor.spectrumchannel import SpectrumChannel
import numpy
import time
import json


def generate_signal(sample_rate, duration, signal_frequency):
    samples_time = numpy.arange(
        int(sample_rate * duration)) / sample_rate
    samples = numpy.sin(2.0 * numpy.pi * signal_frequency * samples_time)
    return samples


def test_sinus(configuration):

    sample_rate = configuration["configuration"]["sample_rate"]
    # generate signal
    samples = generate_signal(sample_rate, duration=10,
                              signal_frequency=1000.0)

    sc = SpectrumChannel(configuration, use_scipy=False, use_cascade=True)

    # find appropriate sampling
    stride = int(sample_rate)
    stride = round(stride / sc.minimum_samples_length) *\
        sc.minimum_samples_length
    spectrogram = []
    for sample_index in range(0, len(samples), stride):
        sub_samples = samples[sample_index:sample_index+stride]
        spectrum_dictionary = sc.process_samples(sub_samples)
        spectrogram.append(("%g" % ((sample_index + stride) / sample_rate)
                            , ",".join(
            ["%g" % spl for spl in spectrum_dictionary])))
    fields = ["%g Hz" % bp["nominal_frequency"]
              for bp in configuration["bandpass"]]
    print("t, "+", ".join(fields))
    for t, spectrum in spectrogram:
        print(t+", "+spectrum)

    # timings

    deb = time.time()
    sc.process_samples(samples)
    end_process = time.time()
    process_time_per_second = (end_process - deb) / (len(samples) / sample_rate)
    print("Process time per second of audio %.3f ms" %
          (process_time_per_second * 1000.0))

config = json.load(open("config_48000_third_octave.json", "r"))
test_sinus(config)



