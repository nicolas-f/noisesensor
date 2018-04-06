import logging
import unittest
import noisepy
"""
Some basic tests
"""

logging.basicConfig(level=logging.DEBUG)


class TestAcousticIndicators(unittest.TestCase):

    def test_leq(self):
        np = noisepy.noisepy(False, 32767.)
        f = open("../../core/test/speak_32000Hz_16bitsPCM_10s.raw", "rw")
        while not f is None:
            data = f.read(np.max_samples_length() * 2)
            if not data:
                break
            res = np.push(data, len(data) / 2)
            if not res is None:
                print len(data) / 2
                print str(res)+" dB"
        f.close()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAcousticIndicators)
    unittest.TextTestRunner(verbosity=2).run(suite)
