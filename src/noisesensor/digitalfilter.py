import numpy
from numba.experimental import jitclass
from numba import float64, int32     # import the types
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
    ('order', int32),
    ('numerator', float64[:]),
    ('denominator', float64[:])
]


@jitclass(spec)
class DigitalFilter:
    def __init__(self, numerator, denominator):
        assert len(numerator) == len(denominator)
        self.order = len(numerator)
        self.numerator = numerator
        self.denominator = denominator

    def filter(self, samples_in: float64[:], samples_out: float64[:]):
        samples_len = len(samples_in)
        samples_out_index = 0
        delay_1 = numpy.zeros(shape=len(samples_in) * (self.order - 1), dtype=float)
        for i in range(samples_len):
            sample = samples_in[i]
            samples_out[i] = self.numerator[0] * sample + (0 if i==0 else delay_1[i-1])
            delay_1[i] = self.numerator[1] * sample + (0 if i==0 else delay_1[samples_len + i - 1]) - self.denominator[1] * sample
            for k in range(self.order - 2):
                delay_1[k*samples_len+i] = self.numerator[k+1] * sample + (0 if i==0 else delay_1[(k+1)*samples_len + i - 1]) - self.denominator[k+1] * samples_out[i]
            delay_1[samples_len * (self.order - 2) + i] = self.numerator[self.order - 1] * sample - self.denominator[self.order-1] * samples_out[i]


def main():
    numerator = numpy.array([0.23430179229951348, -0.46860358459902696,
                            -0.23430179229951348, 0.9372071691980539,
                            -0.23430179229951348, -0.46860358459902696,
                            0.23430179229951348])
    denominator = numpy.array([1.0, -4.113043408775871, 6.553121752655046,
                              -4.990849294163378, 1.785737302937571,
                              -0.2461905953194862, 0.011224250033231168])
    df = DigitalFilter(numerator, denominator)
    signal = numpy.random.normal(0, 0.7, size=48)
    result = numpy.zeros(signal.shape)
    df.filter(signal, result)
    import scipy
    result2 = scipy.signal.lfilter(numerator, denominator, signal)
    print(result)
    print(result2)


if __name__ == "__main__":
    main()
