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
from libc.stdint cimport int16_t, int32_t
from cpython.bytes cimport PyBytes_FromStringAndSize
from libcpp cimport bool



cdef class noisepy:
    cdef cnoisepy.AcousticIndicatorsData* _c_noisepy
    cdef bool a_filter
    cdef bool third_octave
    cdef float ref_pressure
    cdef bool window
    def __cinit__(self):
        self._c_noisepy = cnoisepy.ai_NewAcousticIndicatorsData()
        if self._c_noisepy is NULL:
            raise MemoryError()

    def __dealloc__(self):
        if self._c_noisepy is not NULL:
            cnoisepy.ai_FreeAcousticIndicatorsData(self._c_noisepy)

    def __init__(self, a_filter, third_octave, ref_pressure, window):
        self.a_filter = a_filter
        self.ref_pressure = ref_pressure
        self.third_octave = third_octave
        self.window = window
        cnoisepy.ai_InitAcousticIndicatorsData(self._c_noisepy, self.a_filter, self.third_octave, self.ref_pressure, self.window)

    def push(self, unsigned char* python_samples, int length):
      return cnoisepy.ai_AddSample(self._c_noisepy, length, <int16_t*>python_samples)

    def get_leq_slow(self):
      return cnoisepy.ai_get_leq_slow(self._c_noisepy)

    def get_leq_fast(self):
      return cnoisepy.ai_get_leq_fast(self._c_noisepy)

    def get_leq_band_fast(self, int band_id):
      return cnoisepy.ai_get_leq_band_fast(self._c_noisepy, band_id)

    def max_samples_length(self):
      return cnoisepy.ai_GetMaximalSampleSize(self._c_noisepy)

    def get_leq_band_slow(self, int band_id):
      return cnoisepy.ai_get_band_leq(self._c_noisepy, band_id)
