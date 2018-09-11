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
        distFreq = [abs(f - self.data["frequency"]) for f in freqs]
        self.third_octave_index = distFreq.index(min(distFreq))

    def unix_time(self):
        return (datetime.datetime.utcnow() - self.epoch).total_seconds()

    def getrms(self, rmsvalues):
        return sum(rmsvalues)  # / len(rmsvalues)

    def run(self):
        db_delta = 0
        ref_sound_pressure = 1 / 10 ** (db_delta / 20.)
        np = noisepy.noisepy(False, True, ref_sound_pressure, True)
        np.set_tukey_alpha(0.2)
        short_size = struct.calcsize('h')
        while True:
            audiosamples = sys.stdin.read(np.max_samples_length() * short_size)
            if not audiosamples:
                print("%s End of audio samples" % datetime.datetime.now().isoformat())
                break
            else:
                resp = np.push(audiosamples, len(audiosamples) / short_size)
                # time can be in iso format using datetime.datetime.now().isoformat()
                if resp == noisepy.feed_complete or resp == noisepy.feed_fast:
                    leqSpectrum = map(np.get_leq_band_fast, range(len(freqs)))
                    # fast_spectrum = np.get_rms_spectrum()
                    #rms_tot = self.getrms(fast_spectrum)
                    #fast_spectrum[self.cellLower:self.cellUpper] = [0 for i in range(self.cellUpper-self.cellLower)]
                    #rms_noise = self.getrms(fast_spectrum)
                    #print("%.2f/%.2f %.2f%% %.1f dB@1khz %.1f dB" % (rms_noise, rms_tot, rms_noise/rms_tot * 100, leqSpectrum[freqs.index(self.data["frequency"])], np.get_leq_fast()))
                    rms_tot = sum([10**(v/10) for v in leqSpectrum])
                    rms_noise = rms_tot - 10**(leqSpectrum[self.third_octave_index]/10)
                    thdn = (rms_noise/rms_tot)*100
                    print("THD-N %.2f%% (%.2f/%.2f)" % (thdn, rms_noise, rms_tot))









def usage():
    print("-s 1000 for 1000 Hz tone")


def main():
    # parse command line options
    freq = 0
    data = {}
    try:
        for opt, value in getopt.getopt(sys.argv[1:], "s:")[0]:
            if opt == "-s":
                freq = float(value)
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

