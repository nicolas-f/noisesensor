import numpy
from numba.experimental import jitclass
from numba import float64, int32     # import the types
import math

"""
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
    ('order', int32),
    ('delay_1', float64[:]),
    ('delay_2', float64[:]),
    ('numerator', float64[:]),
    ('denominator', float64[:]),
    ('circular_index', int32)
]


@jitclass(spec)
class DigitalFilter:
    def __init__(self, numerator, denominator):
        assert len(numerator) == len(denominator)
        self.order = len(numerator)
        self.numerator = numerator
        self.circular_index = 0
        self.denominator = denominator
        self.delay_1 = numpy.zeros(shape=self.order, dtype=float)
        self.delay_2 = numpy.zeros(shape=self.order, dtype=float)

    def clear_delay(self):
        self.circular_index = 0
        self.delay_1 = numpy.zeros(shape=self.order, dtype=float)
        self.delay_2 = numpy.zeros(shape=self.order, dtype=float)

    def filter(self, samples_in, samples_out):
        """
        Direct form II transposed filter
        @param samples_in: Input samples
        @param samples_out: Output samples (must be same length as input)
        @see Adapted & Converted from
        https://rosettacode.org/wiki/Apply_a_digital_filter_(
        direct_form_II_transposed)#Java
        """
        samples_len = len(samples_in)
        for i in range(samples_len):
            input_acc = 0
            self.delay_2[self.circular_index] = samples_in[i]
            for j in range(self.order):
                input_acc += self.numerator[j] * self.delay_2[
                    (self.circular_index - j) % self.order]
                if j == 0:
                    continue
                input_acc -= self.denominator[j] * self.delay_1[
                    (self.order - j + self.circular_index) % self.order]
            input_acc /= self.denominator[0]
            self.delay_1[self.circular_index] = input_acc
            self.circular_index = self.circular_index + 1
            if self.circular_index == self.order:
                self.circular_index = 0
            samples_out[i] = input_acc

    def filter_leq(self, samples_in):
        """
        Direct form II transposed filter
        @param samples_in: Input samples
        @see Adapted & Converted from
        https://rosettacode.org/wiki/Apply_a_digital_filter_(
        direct_form_II_transposed)#Java
        """
        square_sum = 0.0

        samples_len = len(samples_in)
        for i in range(samples_len):
            input_acc = 0
            self.delay_2[self.circular_index] = samples_in[i]
            for j in range(self.order):
                input_acc += self.numerator[j] * self.delay_2[
                    (self.circular_index - j) % self.order]
                if j == 0:
                    continue
                input_acc -= self.denominator[j] * self.delay_1[
                    (self.order - j + self.circular_index) % self.order]
            input_acc /= self.denominator[0]
            self.delay_1[self.circular_index] = input_acc
            self.circular_index = self.circular_index + 1
            if self.circular_index == self.order:
                self.circular_index = 0
            square_sum += input_acc * input_acc
        return 10 * math.log10(square_sum / samples_len)

