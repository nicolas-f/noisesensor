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

cimport cnoisepy
from libc.stdint cimport int8_t, int16_t, int32_t
from cpython.bytes cimport PyBytes_FromStringAndSize
from libcpp cimport bool

cdef class noisepy:
    cdef cnoisepy.AcousticIndicatorsData* _c_noisepy
    cdef bool a_filter
    cdef bool third_octave
    cdef float ref_pressure
    cdef bool window
    cdef bool init
    def __cinit__(self):
        self.init = False
        self._c_noisepy = cnoisepy.ai_NewAcousticIndicatorsData()
        if self._c_noisepy is NULL:
            raise MemoryError()

    def __dealloc__(self):
        if self.init:
            cnoisepy.ai_free_acoustic_indicators_data(self._c_noisepy)

    def __init__(self, a_filter, third_octave, ref_pressure, window, sample_rate_index, basestring format, mono):
        self.a_filter = a_filter
        self.ref_pressure = ref_pressure
        self.third_octave = third_octave
        self.window = window
        res = cnoisepy.ai_init_acoustic_indicators_data(self._c_noisepy, self.a_filter, self.third_octave, self.ref_pressure, self.window, sample_rate_index, format.encode('utf8'), mono)
        if res != 0:
            raise Exception("Init error %d" % res)
        self.init = True

    def push(self, const int8_t* python_samples, int length):
      return cnoisepy.ai_add_sample(self._c_noisepy, length, python_samples)

    def get_leq_slow(self):
      return cnoisepy.ai_get_leq_slow(self._c_noisepy)

    def set_tukey_alpha(self, float tukey_alpha):
      cnoisepy.ai_SetTukeyAlpha(self._c_noisepy, tukey_alpha)

    def get_leq_fast(self):
      return cnoisepy.ai_get_leq_fast(self._c_noisepy)

    def get_leq_band_fast(self, int band_id):
      return cnoisepy.ai_get_leq_band_fast(self._c_noisepy, band_id)

    def max_samples_length(self):
      return cnoisepy.ai_get_maximal_sample_size(self._c_noisepy)

    def get_leq_band_slow(self, int band_id):
      return cnoisepy.ai_get_band_leq(self._c_noisepy, band_id)

    def get_rms_spectrum(self):
      return [cnoisepy.ai_GetThinBandRMS(self._c_noisepy, i) for i in range(cnoisepy.ai_get_leq_band_fast_size(self._c_noisepy))]
