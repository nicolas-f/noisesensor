import logging
import unittest
import noisepy
"""
Some basic tests
"""

logging.basicConfig(level=logging.DEBUG)


class TestAcousticIndicators(unittest.TestCase):

    def test_leq(self):
        expected_leqs = [-26.21,-27.94,-29.12,-28.92,-40.39,-24.93,-31.55,-29.04,-31.08,-30.65]
        results = []
        np = noisepy.noisepy(False, False, 32767.)
        f = open("../../core/test/speak_32000Hz_16bitsPCM_10s.raw", "rw")
        while not f is None:
            data = f.read(np.max_samples_length() * 2)
            if not data:
                break
            if np.push(data, len(data) / 2) == noisepy.feed_complete:
                results.append(np.get_leq_slow())
        f.close()
        for i in range(len(expected_leqs)):
            self.assertAlmostEqual(expected_leqs[i], results[i], 1)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAcousticIndicators)
    unittest.TextTestRunner(verbosity=2).run(suite)
