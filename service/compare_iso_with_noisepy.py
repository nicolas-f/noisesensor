import noisepy
import acoustics
import math
import numpy

def analyze(raw_path, print_freqs):
    # Process with acoustics
    dat = numpy.fromfile(raw_path, dtype=numpy.int32)
    # convert to mono and remove first and last 2 seconds
    rate = 48000
    dat = dat[::2]
    dat = dat[rate * 2: - rate * 2]
    s = acoustics.Signal(dat, rate)
    leqs = []
    freqs = []
    frequencies, filtered_signals = s.third_octaves()
    for freq, filtered_signal in list(zip(frequencies, filtered_signals))[3:]:
        leq = acoustics.standards.iec_61672_1_2013.time_averaged_sound_level(filtered_signal.values, filtered_signal.fs, len(dat) / rate, numpy.iinfo(numpy.int32).max)[1]
        freqs.append(freq.nominal[0])
        leqs.append(leq[0])
    if print_freqs:
        print("freqs, " + ",".join(["%.1f" % f for f in freqs]))

    print("iec_61672_1_2013(%s)," % raw_path +",".join(["%.2f" % f for f in leqs]))
    # Process with noisepy
    np = noisepy.noisepy(False, True, 1., True, noisepy.ai_sample_rate_48000,
                         noisepy.ai_formats[noisepy.ai_format_s32_le], False)
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

fichs = ["record_31.5.raw", "record_63.raw", "record_125.raw", "record_150.raw", "record_500.raw", "record_1000.raw", "record_2000.raw", "record_3000.raw", "record_8000.raw", "record_12500.raw", "record_16000.raw", "record_background.raw"]

for i, p in zip(range(len(fichs)), fichs):
    analyze(p, i == 0)
