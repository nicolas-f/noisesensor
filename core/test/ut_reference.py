"""
BSD 3-Clause License

Copyright (c) 2018, Ifsttar Wi6labs LS2N
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from __future__ import print_function

import numpy
import acoustics

def tostr(arr):
    return numpy.array2string(arr, separator=",", max_line_width=9999999, precision=2)

p = "ref94dB_48000Hz_32bitsPCM.raw" #"speak_32000Hz_16bitsPCM_10s.raw"
rate = 48000
length = 2 # in seconds
mono = False
data_type = numpy.int32 # numpy.short
dat = numpy.fromfile(p, dtype=data_type)
if not mono:
    dat = dat[::2]
s = acoustics.Signal(dat, rate)

print("Slow 1 seconds")

print("leq = %s" % tostr(acoustics.standards.iec_61672_1_2013.time_averaged_sound_level(s.values, s.fs, 1., numpy.iinfo(data_type).max)[1]))

s_weigh = s.weigh()

print("laeq = %s" % tostr(acoustics.standards.iec_61672_1_2013.time_averaged_sound_level(s_weigh.values, s.fs, 1., numpy.iinfo(data_type).max)[1]))

frequencies, filtered_signals = s.third_octaves()

print("Spectrum 10s")

leqs = []
freqs = []
for freq, filtered_signal in list(zip(frequencies, filtered_signals))[3:]:
    leq = acoustics.standards.iec_61672_1_2013.time_averaged_sound_level(filtered_signal.values, filtered_signal.fs, length, numpy.iinfo(data_type).max)[1]
    freqs.append(freq.nominal[0])
    leqs.append(leq[0])
print("freqs = %s" % tostr(numpy.array(freqs)))

print("leq = %s" % tostr(numpy.array(leqs)))

frequencies, filtered_signals = s_weigh.third_octaves()
laeqs = []
for freq, filtered_signal in list(zip(frequencies, filtered_signals))[3:]:
    leq = acoustics.standards.iec_61672_1_2013.time_averaged_sound_level(filtered_signal.values, filtered_signal.fs, length, numpy.iinfo(data_type).max)[1]
    laeqs.append(leq[0])

print("laeq = %s" % tostr(numpy.array(laeqs)))
