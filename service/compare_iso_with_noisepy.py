import noisepy
import acoustics
import math
import numpy
import time

def analyze(raw_path, print_freqs):
    # Process with acoustics
    dat = numpy.fromfile(raw_path, dtype=numpy.int16)
    # convert to mono and remove first and last 2 seconds
    rate = 32000
    #dat = dat[::2]
    dat = dat[rate * 2: - rate * 2]
    s = acoustics.Signal(dat, rate)
    leqs = []
    freqs = []
    frequencies, filtered_signals = s.third_octaves()
    start = time.time()
    for freq, filtered_signal in list(zip(frequencies, filtered_signals))[3:]:
        leq = acoustics.standards.iec_61672_1_2013.time_averaged_sound_level(filtered_signal.values, filtered_signal.fs, len(dat) / rate, numpy.iinfo(numpy.int16).max)[1]
        freqs.append(freq.nominal[0])
        leqs.append(leq[0])
    print("Done in %0.4f s" % (time.time() - start))
    if print_freqs:
        print("freqs, " + ",".join(["%.1f" % f for f in freqs]))

    print("iec_61672_1_2013(%s)," % raw_path +",".join(["%.2f" % f for f in leqs]))
    # Process with noisepy
    np = noisepy.noisepy(False, True, 1., True, noisepy.ai_sample_rate_32000,
                         'S16_LE', True)
    np.set_tukey_alpha(0.2)
    results = []
    with open(raw_path, "rb") as f:
        while not f is None:
            data = f.read(np.max_samples_length())
            if not data:
                break
            if np.push(data, len(data)) == noisepy.feed_complete:
                results.append(map(lambda x: 10. ** (np.get_leq_band_slow(x) / 10.), range(29)))
    print("code_ifsttar(%s)," % raw_path + ",".join(["%.2f" % (10 * math.log10(sum(band_leq) / len(band_leq))) for idband, band_leq in
                    enumerate(zip(*results[2:-2]))]))

fichs = ["core/test/speak_32000Hz_16bitsPCM_10s.raw"]

for i, p in zip(range(len(fichs)), fichs):
    analyze(p, i == 0)
