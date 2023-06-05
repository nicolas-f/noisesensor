import numpy
from numba.experimental import jitclass
from numba import float64     # import the types
import math

""" A digital biquad filter is a second order recursive linear filter,
 containing two poles and two zeros. "Biquad" is an abbreviation of "bi-quadratic",
  which refers to the fact that in the Z domain, its transfer function is the ratio of two quadratic functions
    
BSD 3-Clause License

Copyright (c) 2023, University Gustave Eiffel
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

 Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

 Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

 Neither the name of the copyright holder nor the names of its
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

__authors__ = ["Valentin Le Bescond, Université Gustave Eiffel",
              "Nicolas Fortin, Université Gustave Eiffel"]
__license__ = "BSD3"

spec = [
    ('_delay_1', float64[:]),
    ('_delay_2', float64[:]),
    ('b0', float64[:]),
    ('b1', float64[:]),
    ('b2', float64[:]),
    ('a1', float64[:]),
    ('a2', float64[:])
]


@jitclass(spec)
class BiquadFilter:
    def __init__(self, b0, b1, b2, a1, a2):
        assert len(b0) == len(b1) == len(b2) == len(a1) == len(a2)
        self._delay_1 = numpy.zeros(shape=len(b0), dtype=float)
        self._delay_2 = numpy.zeros(shape=len(b0), dtype=float)
        self.b0 = b0
        self.b1 = b1
        self.b2 = b2
        self.a1 = a1
        self.a2 = a2
        assert len(b0) == len(b1) == len(b2) == len(a1) == len(a2)

    def reset(self):
        """
        Reset delays of this filter
        """
        self._delay_1 = numpy.zeros(shape=len(self.b0), dtype=float)
        self._delay_2 = numpy.zeros(shape=len(self.b0), dtype=float)

    def filter_then_leq(self, samples: float64[:]):
        samples_len = len(samples)
        filter_length = len(self.b0)
        square_sum = 0.0
        for i in range(samples_len):
            input_acc = samples[i]
            for j in range(filter_length):
                input_acc -= self._delay_1[j] * self.a1[j]
                input_acc -= self._delay_2[j] * self.a2[j]
                output_acc = input_acc * self.b0[j]
                output_acc += self._delay_1[j] * self.b1[j]
                output_acc += self._delay_2[j] * self.b2[j]

                self._delay_2[j] = self._delay_1[j]
                self._delay_1[j] = input_acc

                input_acc = output_acc
            square_sum += input_acc * input_acc
        return 10 * math.log10(square_sum / samples_len)

    def filter_slice(self, samples_in: float64[:], samples_out: float64[:],
                     subsampling_factor: int):
        samples_len = len(samples_in)
        filter_length = len(self.b0)
        samples_out_index = 0
        for i in range(samples_len):
            input_acc = samples_in[i]
            for j in range(filter_length):
                input_acc -= self._delay_1[j] * self.a1[j]
                input_acc -= self._delay_2[j] * self.a2[j]
                output_acc = input_acc * self.b0[j]
                output_acc += self._delay_1[j] * self.b1[j]
                output_acc += self._delay_2[j] * self.b2[j]

                self._delay_2[j] = self._delay_1[j]
                self._delay_1[j] = input_acc

                input_acc = output_acc
            if i % subsampling_factor == 0:
                samples_out[samples_out_index] = input_acc
                samples_out_index += 1


