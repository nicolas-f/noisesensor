from sonomkr.filterdesign import FilterDesign
from sonomkr.spectrumchannel import SpectrumChannel
import numpy
import time


def generate_signal(sample_rate, duration, signal_frequency):
    samples_time = numpy.arange(
        int(sample_rate * duration)) / sample_rate
    samples = numpy.sin(2.0 * numpy.pi * signal_frequency * samples_time)
    return samples


def test_sinus():
    f = FilterDesign(sample_rate=48000, first_frequency_band=50,
                     last_frequency_band=16000)
    f.down_sampling = f.G2
    f.band_division = 3
    configuration = f.generate_configuration()
    import json
    print(json.dumps(configuration, sort_keys=False, indent=4))

    # generate signal
    samples = generate_signal(f.sample_rate, duration=10,
                              signal_frequency=1000.0)

    sc = SpectrumChannel(configuration, use_scipy=False, use_cascade=True)

    # heat up process (numba compilation time)
    sc.process_samples(samples)

    deb = time.time()
    # find appropriate sampling
    stride = int(f.sample_rate)
    stride = round(stride / sc.minimum_samples_length) *\
        sc.minimum_samples_length
    spectrogram = []
    for sample_index in range(0, len(samples), stride):
        sub_samples = samples[sample_index:sample_index+stride]
        spectrum_dictionary = sc.process_samples(sub_samples)
        spectrogram.append(("%g" % ((sample_index + stride) / f.sample_rate)
                          , ",".join(["%g" % spl for spl in spectrum_dictionary])))
    fields = ["%g Hz" % bp["nominal_frequency"]
              for bp in configuration["bandpass"]]
    print("t, "+", ".join(fields))
    for t, spectrum in spectrogram:
        print(t+", "+spectrum)
    print("Done in %.3f" % (time.time() - deb))


test_sinus()



