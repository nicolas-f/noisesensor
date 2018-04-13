from __future__ import print_function
import numpy
import acoustics

def tostr(arr):
    return numpy.array2string(arr, separator=",", max_line_width=9999999, precision=2)

p = "speak_32000Hz_16bitsPCM_10s.raw"

dat = numpy.fromfile(p, dtype=numpy.short)

s = acoustics.Signal(dat, 32000)

print("Slow 1 seconds")

print("leq = %s" % tostr(acoustics.standards.iec_61672_1_2013.time_averaged_sound_level(s.values, s.fs, 1., 32767)[1]))

s_weigh = s.weigh()

print("laeq = %s" % tostr(acoustics.standards.iec_61672_1_2013.time_averaged_sound_level(s_weigh.values, s.fs, 1., 32767)[1]))

frequencies, filtered_signals = s.third_octaves()

print("Spectrum 10s")

leqs = []
freqs = []
for freq, filtered_signal in zip(frequencies, filtered_signals)[3:]:
    leq = acoustics.standards.iec_61672_1_2013.time_averaged_sound_level(filtered_signal.values, filtered_signal.fs, 10., 32767)[1]
    freqs.append(freq.nominal[0])
    leqs.append(leq[0])
print("freqs = %s" % tostr(numpy.array(freqs)))

print("leq = %s" % tostr(numpy.array(leqs)))

frequencies, filtered_signals = s_weigh.third_octaves()
laeqs = []
for freq, filtered_signal in zip(frequencies, filtered_signals)[3:]:
    leq = acoustics.standards.iec_61672_1_2013.time_averaged_sound_level(filtered_signal.values, filtered_signal.fs, 10., 32767)[1]
    leqs.append(leq[0])

print("laeq = %s" % tostr(numpy.array(leqs)))
