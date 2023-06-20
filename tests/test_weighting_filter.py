import os.path
import unittest
import numpy
from noisesensor.filterdesign import FilterDesign
from noisesensor.digitalfilter import DigitalFilter
import acoustics
import scipy

UNIT_TEST_PATH = os.path.dirname(os.path.abspath(__file__))


class TestWeightingFilter(unittest.TestCase):
    def test_weighting_a(self):
        f = FilterDesign(sample_rate=48000, first_frequency_band=50,
                         last_frequency_band=16000)
        f.down_sampling = f.G10
        f.band_division = 3
        configuration = f.generate_configuration()
        numerator = numpy.array(
            configuration["a_weighting"]["filter_numerator"])
        denominator = numpy.array(
            configuration["a_weighting"]["filter_denominator"])
        df = DigitalFilter(numerator, denominator)
        rng = numpy.random.default_rng(seed=7355608)
        signal = rng.normal(0, 0.7, size=20)
        expected = scipy.signal.lfilter(numerator, denominator, signal)
        got = numpy.zeros(signal.shape)
        df.filter(signal, got)
        for expected, got in zip(expected, got):
            # Use error delta in linear scale
            self.assertAlmostEqual(expected, got,
                                   delta=1e-12,
                                   msg="%f != %f" %
                                       (expected, got))

    def test_weighting_a_acoustics(self):
        sample_rate = 48000
        f = FilterDesign(sample_rate=sample_rate, first_frequency_band=50,
                         last_frequency_band=16000)
        f.down_sampling = f.G10
        f.band_division = 3
        configuration = f.generate_configuration()
        numerator = numpy.array(
            configuration["a_weighting"]["filter_numerator"])
        denominator = numpy.array(
            configuration["a_weighting"]["filter_denominator"])
        df = DigitalFilter(numerator, denominator)
        rng = numpy.random.default_rng(seed=7355608)
        signal = rng.normal(0, 0.7, size=20)
        acoustics_signal = acoustics.Signal(signal, sample_rate)
        expected = acoustics_signal.weigh(weighting='A')
        got = numpy.zeros(signal.shape)
        df.filter(signal, got)
        for expected, got in zip(expected, got):
            # Use error delta in linear scale
            self.assertAlmostEqual(expected, got,
                                   delta=1e-12,
                                   msg="%f != %f" %
                                       (expected, got))

    def test_weighting_c_acoustics(self):
        sample_rate = 48000
        f = FilterDesign(sample_rate=sample_rate,
                         first_frequency_band=50,
                         last_frequency_band=16000)
        f.down_sampling = f.G10
        f.band_division = 3
        configuration = f.generate_configuration()
        numerator = numpy.array(
            configuration["c_weighting"]["filter_numerator"])
        denominator = numpy.array(
            configuration["c_weighting"]["filter_denominator"])
        df = DigitalFilter(numerator, denominator)
        rng = numpy.random.default_rng(seed=7355608)
        signal = rng.normal(0, 0.7, size=20)
        acoustics_signal = acoustics.Signal(signal, sample_rate)
        expected = acoustics_signal.weigh(weighting='C')
        got = numpy.zeros(signal.shape)
        df.filter(signal, got)
        for expected, got in zip(expected, got):
            # Use error delta in linear scale
            self.assertAlmostEqual(expected, got,
                                   delta=1e-12,
                                   msg="%f != %f" %
                                       (expected, got))


if __name__ == '__main__':
    unittest.main()
