import logging
import unittest
import noisepy
import math

"""
Some basic tests
"""

logging.basicConfig(level=logging.DEBUG)

##
# Unit test, check ut_reference.py for reference values on this unit test
class TestAcousticIndicators(unittest.TestCase):

    ##
    # Test leq 1s
    def test_leq(self):
        expected_leqs = [-26.21,-27.94,-29.12,-28.92,-40.39,-24.93,-31.55,-29.04,-31.08,-30.65]
        results = []
        np = noisepy.noisepy(False, False, 32767.)
        f = open("../../test/speak_32000Hz_16bitsPCM_10s.raw", "rw")
        while not f is None:
            data = f.read(np.max_samples_length() * 2)
            if not data:
                break
            if np.push(data, len(data) / 2) == noisepy.feed_complete:
                results.append(np.get_leq_slow())
        f.close()
        for i in range(len(expected_leqs)):
            self.assertAlmostEqual(expected_leqs[i], results[i], 1)

    ##
    # Test laeq 1s
    def test_laeq(self):
        expected_leqs = [-31.37, -33.74, -33.05, -33.61, -43.68, -29.96, -35.53, -34.12, -37.06, -37.19]
        results = []
        np = noisepy.noisepy(True, False, 32767.)
        f = open("../../test/speak_32000Hz_16bitsPCM_10s.raw", "rw")
        while not f is None:
            data = f.read(np.max_samples_length() * 2)
            if not data:
                break
            if np.push(data, len(data) / 2) == noisepy.feed_complete:
                results.append(np.get_leq_slow())
        f.close()
        for i in range(len(expected_leqs)):
            self.assertAlmostEqual(expected_leqs[i], results[i], 1)

    ##
    # Test leq spectrum 10s
    def test_leq_spectrum(self):
        expected_leqs = [-64.59,-62.82,-63.14,-64.93,-65.03,-66.43,-65.56,-66.  ,-68.06,-66.28,-43.34,
                             -31.93,-37.28,-47.33,-35.33,-42.68,-42.91,-48.51,-49.1 ,-52.9 ,-52.15,-52.8 ,
                             -52.35,-52.31,-53.39,-52.53,-53.73,-53.56,-57.9]
        results = []
        np = noisepy.noisepy(False, True, 32767.)
        f = open("../../test/speak_32000Hz_16bitsPCM_10s.raw", "rw")
        while not f is None:
            data = f.read(np.max_samples_length() * 2)
            if not data:
                break
            if np.push(data, len(data) / 2) == noisepy.feed_complete:
                results.append(map(lambda x : 10. ** (np.get_leq_band_slow(x) / 10.), range(29)))
        f.close()

        err = 0
        for idband, band_leq in enumerate(zip(*results)):
            leq = 10 * math.log10(sum(band_leq) / len(band_leq))
            err += (expected_leqs[idband] - leq) ** 2
        mean_squared_error = math.sqrt(err / len(expected_leqs))
        expected_mean_squared_error = 2.83
        self.assertTrue(mean_squared_error < expected_mean_squared_error, "mean squared error %.2f > %.2f" % (mean_squared_error, expected_mean_squared_error))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAcousticIndicators)
    unittest.TextTestRunner(verbosity=2).run(suite)
