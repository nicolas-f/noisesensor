import os.path
import time
import unittest
import numpy
from noisesensor.filterdesign import FilterDesign
from noisesensor.spectrumchannel import SpectrumChannel, compute_leq
import acoustics
import math

UNIT_TEST_PATH = os.path.dirname(os.path.abspath(__file__))

def generate_signal(sample_rate, duration, signal_frequency):
    samples_time = numpy.arange(
        int(sample_rate * duration)) / sample_rate
    samples = numpy.sin(2.0 * numpy.pi * signal_frequency * samples_time)
    return samples


def to_w(spl):
    return 10**(spl/20)


class TestBiQuadFilter(unittest.TestCase):
    def test_sinus_third_octave_g10(self):
        f = FilterDesign(sample_rate=48000, first_frequency_band=50,
                         last_frequency_band=16000)
        f.down_sampling = f.G10
        f.band_division = 3
        configuration = f.generate_configuration()

        # generate signal
        samples = generate_signal(f.sample_rate, duration=5,
                                  signal_frequency=1000.0)

        expected_leq = compute_leq(samples)

        sc = SpectrumChannel(configuration, use_scipy=False, use_cascade=True)

        spectrum = sc.process_samples(samples)

        fields = [bp["nominal_frequency"] for bp in configuration["bandpass"]]

        self.assertAlmostEqual(to_w(expected_leq), to_w(spectrum[fields.index(1000.0)]), delta=0.01)
    def test_sinus_third_octave_g2(self):
        f = FilterDesign(sample_rate=48000, first_frequency_band=50,
                         last_frequency_band=16000)
        f.down_sampling = f.G2
        f.band_division = 3
        configuration = f.generate_configuration()

        # generate signal
        samples = generate_signal(f.sample_rate, duration=5,
                                  signal_frequency=1000.0)

        expected_leq = compute_leq(samples)

        sc = SpectrumChannel(configuration, use_scipy=False, use_cascade=True)

        spectrum = sc.process_samples(samples)

        fields = [bp["nominal_frequency"] for bp in configuration["bandpass"]]

        self.assertAlmostEqual(to_w(expected_leq), to_w(spectrum[fields.index(1000.0)]), delta=0.01)

    def test_sinus_third_octave_g2_32000(self):
        f = FilterDesign(sample_rate=32000, first_frequency_band=50,
                         last_frequency_band=12500)
        f.down_sampling = f.G2
        f.band_division = 3
        configuration = f.generate_configuration()

        # generate signal
        samples = generate_signal(f.sample_rate, duration=5,
                                  signal_frequency=1000.0)

        expected_leq = compute_leq(samples)

        sc = SpectrumChannel(configuration, use_scipy=False, use_cascade=True)

        spectrum = sc.process_samples(samples)

        fields = [bp["nominal_frequency"] for bp in configuration["bandpass"]]

        self.assertAlmostEqual(to_w(expected_leq), to_w(spectrum[fields.index(1000.0)]), delta=0.01)

    def test_sinus_octave_g10(self):
        f = FilterDesign(sample_rate=48000, first_frequency_band=50,
                         last_frequency_band=16000)
        f.down_sampling = f.G10
        f.band_division = 1
        configuration = f.generate_configuration()

        # generate signal
        samples = generate_signal(f.sample_rate, duration=5,
                                  signal_frequency=1000.0)

        expected_leq = compute_leq(samples)

        sc = SpectrumChannel(configuration, use_scipy=False, use_cascade=True)

        spectrum = sc.process_samples(samples)

        fields = [bp["nominal_frequency"] for bp in configuration["bandpass"]]

        self.assertAlmostEqual(to_w(expected_leq), to_w(spectrum[fields.index(1000.0)]), delta=0.01)

    def test_sinus_octave_g2(self):
        f = FilterDesign(sample_rate=48000, first_frequency_band=50,
                         last_frequency_band=16000)
        f.down_sampling = f.G2
        f.band_division = 1
        configuration = f.generate_configuration()

        # generate signal
        samples = generate_signal(f.sample_rate, duration=5,
                                  signal_frequency=1000.0)

        expected_leq = compute_leq(samples)

        sc = SpectrumChannel(configuration, use_scipy=False, use_cascade=True)

        spectrum = sc.process_samples(samples)

        fields = [bp["nominal_frequency"] for bp in configuration["bandpass"]]

        self.assertAlmostEqual(to_w(expected_leq), to_w(spectrum[fields.index(1000.0)]), delta=0.01)

    def test_leq_speak(self):
        fd = FilterDesign(sample_rate=32000,
                          first_frequency_band=20,
                          last_frequency_band=12500)
        expected_leqs = []
        fd.down_sampling = fd.G10
        fd.band_division = 3
        configuration = fd.generate_configuration()
        center_frequency = [bp["center_frequency"] for bp in
                       configuration["bandpass"]]
        sc = SpectrumChannel(configuration)
        try:
            with open(os.path.join(UNIT_TEST_PATH,
                                   "speak_32000Hz_16bitsPCM_10s.raw"),
                      "rb") as f:
                if f is not None:
                    samples = numpy.frombuffer(f.read(), numpy.short)
                    samples = samples / 2**15
                    # process with acoustics library
                    s = acoustics.Signal(samples, 32000)
                    frequencies, filtered_signals = s.third_octaves(
                        frequencies=center_frequency)
                    for freq, filtered_signal in list(
                            zip(frequencies, filtered_signals)):
                        expected_leqs.append(
                                            acoustics.standards.
                                            iec_61672_1_2013.
                                            time_averaged_sound_level(
                                             filtered_signal.values,
                                             filtered_signal.fs,
                                             len(samples) / filtered_signal.fs,
                                             1)[1])
                    # process with this library
                    spectrum = sc.process_samples(samples)
                    self.assertEqual(len(expected_leqs), len(spectrum))
                    err = 0
                    for freq, expected, got in zip(frequencies.nominal, expected_leqs, spectrum):
                        err += (expected[0] - got)**2
                    mean_squared_error = math.sqrt(err / len(expected_leqs))
                    self.assertLess(mean_squared_error, 0.32)
        except FileNotFoundError as e:
            print("Working directory: "+os.path.abspath("./"))
            raise e

    def test_leq_speak_g2(self):
        fd = FilterDesign(sample_rate=32000,
                          first_frequency_band=20,
                          last_frequency_band=12500)
        expected_leqs = []
        fd.down_sampling = fd.G2
        fd.band_division = 3
        configuration = fd.generate_configuration()
        center_frequency = [bp["center_frequency"] for bp in
                       configuration["bandpass"]]
        sc = SpectrumChannel(configuration)
        try:
            with open(os.path.join(UNIT_TEST_PATH,
                                   "speak_32000Hz_16bitsPCM_10s.raw"),
                      "rb") as f:
                if f is not None:
                    samples = numpy.frombuffer(f.read(), numpy.short)
                    samples = samples / 2**15
                    # process with acoustics library
                    s = acoustics.Signal(samples, 32000)
                    frequencies, filtered_signals = s.third_octaves(
                        frequencies=center_frequency)
                    for freq, filtered_signal in list(
                            zip(frequencies, filtered_signals)):
                        expected_leqs.append(
                                            acoustics.standards.
                                            iec_61672_1_2013.
                                            time_averaged_sound_level(
                                             filtered_signal.values,
                                             filtered_signal.fs,
                                             len(samples) / filtered_signal.fs,
                                             1)[1])
                    # process with this library
                    spectrum = sc.process_samples(samples)
                    self.assertEqual(len(expected_leqs), len(spectrum))
                    err = 0
                    for expected, got in zip(expected_leqs, spectrum):
                        err += (expected[0] - got)**2
                    mean_squared_error = math.sqrt(err / len(expected_leqs))
                    self.assertLess(mean_squared_error, 0.6)

        except FileNotFoundError as e:
            print("Working directory: "+os.path.abspath("./"))
            raise e


if __name__ == '__main__':
    unittest.main()
