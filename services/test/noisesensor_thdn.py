#!/usr/bin/env python
# -*- coding: utf-8 -*-


from __future__ import print_function

import noisepy
import getopt
import sys
import struct
import math
import threading
import datetime



freqs = [20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500]



# test with arecord -D hw:2,0 -f S16_LE -r 32000 -c 2 -t wav | sox -t wav - -b 16 -t raw --channels 1 - | python -u noisesensor_thdn.py
class AcousticIndicatorsProcessor(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data
        self.epoch = datetime.datetime.utcfromtimestamp(0)
        freq_by_cell = 32000. / 4000.
        f_lower = data["frequency"] * math.pow(10, -1. / 20.)
        f_upper = data["frequency"] * math.pow(10, 1. / 20.)
        cell_floor = int(math.ceil(f_lower / freq_by_cell))
        cell_ceil = min(4000 - 1, int(math.floor(f_upper / freq_by_cell)))
        self.cellLower = min(cell_floor, cell_ceil)
        self.cellUpper = max(cell_floor, cell_ceil)

    def unix_time(self):
        return (datetime.datetime.utcnow() - self.epoch).total_seconds()

    def getrms(self, rmsvalues):
        return math.sqrt(sum(rmsvalues) / len(rmsvalues))

    def run(self):
        db_delta = 94-56.2
        ref_sound_pressure = 1 / 10 ** (db_delta / 20.)
        ref_sound_pressure = 1.0
        np = noisepy.noisepy(False, True, ref_sound_pressure, True, self.data["rate"], self.data["sample_format"], self.data["mono"])
        np.set_tukey_alpha(0.2)
        read = 0
        while True:
            audiosamples = sys.stdin.read(np.max_samples_length())
            read += len(audiosamples) / 32
            if not audiosamples:
                print("%s End of audio samples" % datetime.datetime.now().isoformat())
                break
            else:
                resp = np.push(audiosamples, len(audiosamples))
                # time can be in iso format using datetime.datetime.now().isoformat()
                if resp == noisepy.feed_complete or resp == noisepy.feed_fast:
                    leqSpectrum = map(np.get_leq_band_fast, range(len(freqs)))
                    fast_spectrum = np.get_rms_spectrum()
                    # print("\n".join(["%.2f"] * len(fast_spectrum)) % tuple(fast_spectrum))
                    rms_tot = self.getrms(fast_spectrum)
                    fast_spectrum[self.cellLower:self.cellUpper] = [0 for i in range(self.cellUpper-self.cellLower)]
                    rms_noise = self.getrms(fast_spectrum)
                    print("%.3f s\tTHD-N: %.2f%%\t%.1f dB@1khz\t%.1f dB leq" % (read / 32000., rms_noise/rms_tot * 100, leqSpectrum[freqs.index(self.data["frequency"])], np.get_leq_fast()))









def usage():
    print(" -s:\t 1000 for 1000 Hz tone")
    print(" -f:\t Sample format")
    print(" -r:\t Sample rate in Hz")
    print(" -c:\t Number of channels")


def main():
    # parse command line options
    freq = 0
    data = {}
    try:
        for opt, value in getopt.getopt(sys.argv[1:], "s:f:r:c:")[0]:
            if opt == "-s":
                freq = float(value)
            elif opt == "-r":
                rates = ["32000", "48000"]
                data["rate"] = rates.index(value)
            elif opt == "-f":
                data["sample_format"] = value
            elif opt == "-c":
                data["mono"] = value == "1"
    except getopt.error as msg:
        usage()
        exit(-1)
    if freq == 0:
        usage()
        sys.exit("You must specify the signal frequency")

    data["frequency"] = freq
    # run audio processing thread
    processing_thread = AcousticIndicatorsProcessor(data)
    processing_thread.start()

if __name__ == "__main__":
    main()

