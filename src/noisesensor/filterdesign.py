try:
    import scipy.signal as signal
    from acoustics.standards.iec_61672_1_2013 import WEIGHTING_SYSTEMS
except ImportError as e:
    print("This optional module is requiring test dependencies."
          "pip install noisesensor[test]")
    raise e

"""
Create Filters parameters according to provided audio signal characteristics
 and wanted noise indicators.

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

OCTAVE_FREQUENCIES = [16.0, 31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0,
                      4000.0, 8000.0, 16000.0]

THIRD_FREQUENCIES = [10.0, 12.5, 16.0, 20.0, 25.0, 31.5, 40.0, 50.0, 63.0,
                     80.0, 100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0,
                     500.0, 630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0,
                     2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0, 10000.0,
                     12500.0, 16000.0, 20000.0]


class FilterDesign:
    """
        Create multiple filter configuration for a cascaded band pass filtering
    """
    def __init__(self, sample_rate=48000, first_frequency_band=50,
                 last_frequency_band=20000, filter_order=6,
                 window_samples=48000):
        """
        :param sample_rate: Sample rate must be greater than 0
        :param first_frequency_band: First pass band (no limitation)
        :param last_frequency_band: Last pass band, should be less than
         sample_rate / 2
        :@param window_samples: Limit the depth of subsampling in order to fit
        with the provided window size
        """
        self.sample_rate = sample_rate
        self.window_samples = window_samples
        self.first_frequency_band = first_frequency_band
        self.last_frequency_band = last_frequency_band
        self.G10 = 10.0 ** (3.0 / 10.0)
        self.G2 = 2.0
        self.down_sampling = self.G10
        self.band_division = 3
        self.filter_order = filter_order
        self.order_aliasing = 20

    def get_bands(self, x):
        frequency_mid = (self.down_sampling **
                         (x / self.band_division)) * 1000
        frequency_max = (self.down_sampling **
                         (1 / (2 * self.band_division))) * frequency_mid
        frequency_min = (self.down_sampling **
                         (- 1 / (2 * self.band_division))) * frequency_mid
        return frequency_min, frequency_mid, frequency_max

    def get_nominal_frequency(self, x):
        if self.band_division == 3:
            if -20 <= x < 14:
                return THIRD_FREQUENCIES[x + 20]
            elif x >= 14:
                return 10 * self.get_nominal_frequency(x-10)
            else:
                return 1/10 * self.get_nominal_frequency(x+10)
        else:
            if -20 <= x < 14:
                return OCTAVE_FREQUENCIES[x + 6]
            elif x >= 14:
                return 2 * self.get_nominal_frequency(x-1)
            else:
                return 1/2 * self.get_nominal_frequency(x+1)

    def get_filter(self, x):
        nyquist = self.sample_rate / 2.0
        frequency_min, frequency_mid, frequency_max = self.get_bands(x)
        w = [frequency_min / nyquist,
             frequency_max / nyquist]
        w[0] = min(0.99999, max(0.00001, w[0]))
        w[1] = min(0.99999, max(0.00001, w[1]))
        sos_bank = signal.butter(self.filter_order, w, 'bandpass',
                                 False, output='sos')

        return {"sos": {"b0": [sos[0] for sos in sos_bank],
                         "b1": [sos[1] for sos in sos_bank],
                         "b2": [sos[2] for sos in sos_bank],
                         "a1": [sos[4] for sos in sos_bank],
                         "a2": [sos[5] for sos in sos_bank]},
                "center_frequency": frequency_mid,
                "max_frequency": frequency_max,
                "min_frequency": frequency_min,
                "nominal_frequency": self.get_nominal_frequency(x)}

    def get_band_from_frequency(self, frequency):
        frequency_band_index = 0
        while True:
            frequency_min, frequency_mid, frequency_max = \
                self.get_bands(frequency_band_index)
            if frequency < frequency_min:
                frequency_band_index -= 1
            elif frequency > frequency_max:
                frequency_band_index += 1
            else:
                break
        return frequency_band_index

    def generate_configuration(self):
        """
        :return: Python dictionary to use in audio processing code
        """
        assert self.last_frequency_band > self.first_frequency_band
        assert self.band_division in [1, 3]
        assert self.filter_order > 0
        assert self.down_sampling in [self.G10, self.G2]
        assert self.sample_rate > 0
        assert self.sample_rate >= self.last_frequency_band * 2
        frequencies = []
        first_band = self.get_band_from_frequency(self.first_frequency_band)
        last_band = self.get_band_from_frequency(self.last_frequency_band)

        for x in range(first_band, last_band + 1):
            subsampling_depth = 0
            data = self.get_filter(x)
            frequency_mid = data["center_frequency"]
            frequency_high = data["max_frequency"]
            ds_factor = 10 if self.down_sampling == self.G10\
                else 2
            while self.sample_rate % \
                    ds_factor ** (subsampling_depth+1) == 0\
                    and self.sample_rate / ds_factor **\
                    (subsampling_depth+1) >= frequency_high * 2 and \
                    self.window_samples % ds_factor ** (subsampling_depth+1)\
                    == 0:
                subsampling_depth += 1
            data["subsampling_depth"] = subsampling_depth
            # compute the target frequency index for the used down-sampling
            ss_freq = frequency_mid * ds_factor ** subsampling_depth
            s_index = self.get_band_from_frequency(ss_freq)
            data["subsampling_filter"] =\
                self.get_filter(s_index)
            frequencies.append(data)
        frequency_aliasing = self.sample_rate / 10 \
            if self.down_sampling == self.G10 else self.sample_rate / 2
        aliasing_sos = signal.butter(self.order_aliasing,
                                     frequency_aliasing / self.sample_rate,
                                     'low', False, output='sos')
        anti_aliasing = {"b0": [sos[0] for sos in aliasing_sos],
                         "b1": [sos[1] for sos in aliasing_sos],
                         "b2": [sos[2] for sos in aliasing_sos],
                         "a1": [sos[4] for sos in aliasing_sos],
                         "a2": [sos[5] for sos in aliasing_sos]}
        # compute weighting filters coefficients
        num, den = WEIGHTING_SYSTEMS['A']()
        b, a = signal.bilinear(num, den, self.sample_rate)
        a_weighting = {"filter_denominator": list(a),
                       "filter_numerator": list(b)}

        num, den = WEIGHTING_SYSTEMS['C']()
        b, a = signal.bilinear(num, den, self.sample_rate)
        c_weighting = {"filter_denominator": list(a),
                       "filter_numerator": list(b)}
        # output sample ratio
        anti_aliasing["sample_ratio"] = 10 if self.down_sampling == self.G10 \
            else 2
        return {"bandpass": frequencies, "anti_aliasing": anti_aliasing,
                "configuration": {"sample_rate": self.sample_rate},
                "a_weighting": a_weighting, "c_weighting": c_weighting}


if __name__ == "__main__":
    cfg = FilterDesign()
    cfg.generate_configuration()
