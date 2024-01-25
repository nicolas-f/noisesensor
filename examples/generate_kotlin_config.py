#  BSD 3-Clause License
#
#  Copyright (c) 2023, University Gustave Eiffel
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
#   Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#   Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
#  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#  SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#  OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from noisesensor.filterdesign import FilterDesign

class_source = """

data class SpectrumChannelConfiguration (
    val bandpass: List<Bandpass>,
    val antiAliasing: AntiAliasing,
    val aWeighting: DigitalFilterConfiguration,
    val cWeighting: DigitalFilterConfiguration,
    val configuration: GeneralConfiguration
)

data class DigitalFilterConfiguration(
    val filterDenominator: DoubleArray,
    val filterNumerator: DoubleArray
)

data class AntiAliasing(
    val a1: DoubleArray,
    val a2: DoubleArray,
    val b0: DoubleArray,
    val b1: DoubleArray,
    val b2: DoubleArray,
    val sampleRatio: Int
)

data class Bandpass(
    val centerFrequency: Double,
    val maxFrequency: Double,
    val minFrequency: Double,
    val nominalFrequency: Double,
    val subsamplingDepth: Int,
    val sos: Sos,
    val subsamplingFilter: SubsamplingFilter
)

data class GeneralConfiguration(
    val sampleRate: Int
)

data class Sos(
    val a1: DoubleArray,
    val a2: DoubleArray,
    val b0: DoubleArray,
    val b1: DoubleArray,
    val b2: DoubleArray
)

data class SubsamplingFilter(
    val centerFrequency: Double,
    val maxFrequency: Double,
    val minFrequency: Double,
    val nominalFrequency: Double,
    val sos: Sos
)
"""


def write_array(fw, array_in):
    for li, val in enumerate(array_in):
        if li > 0:
            fw.write(",%s" % val)
        else:
            fw.write("%s" % val)


def dump_sos(fw, sos):
    fw.write("Sos(a1=doubleArrayOf(")
    write_array(fw, sos["a1"])
    fw.write("), a2=doubleArrayOf(")
    write_array(fw, sos["a2"])
    fw.write("), b0=doubleArrayOf(")
    write_array(fw, sos["b0"])
    fw.write("), b1=doubleArrayOf(")
    write_array(fw, sos["b1"])
    fw.write("), b2=doubleArrayOf(")
    write_array(fw, sos["b2"])
    fw.write("))")


def main():
    with open("ConfigSpectrumChannel.kt", "w") as fw:
        fw.write(class_source)

        for freq in [44100, 48000]:
            f = FilterDesign(sample_rate=freq, first_frequency_band=50,
                             last_frequency_band=16000,
                             window_samples=freq * 0.125)

            f.down_sampling = f.G2
            f.band_division = 3

            configuration = f.generate_configuration()
            fw.write("\n\nfun get%dHZ() : SpectrumChannelConfiguration {\n" % f.sample_rate)
            fw.write(
                "  return SpectrumChannelConfiguration(\n    bandpass=listOf(")
            for bi, bandpass in enumerate(configuration["bandpass"]):
                if bi > 0:
                    fw.write(",\n      ")
                else:
                    fw.write("\n      ")
                fw.write("Bandpass({center_frequency},{max_frequency},"
                         "{min_frequency},{nominal_frequency},"
                         "{subsampling_depth},"
                         .format(**bandpass))
                dump_sos(fw, bandpass["sos"])
                fw.write(
                    ",subsamplingFilter=SubsamplingFilter({center_frequency},"
                    "{max_frequency},{min_frequency},{nominal_frequency}"
                    ",sos=".format(**bandpass["subsampling_filter"]))
                dump_sos(fw, bandpass["subsampling_filter"]["sos"])
                fw.write("))")
            fw.write("),\n    antiAliasing=")
            fw.write("AntiAliasing(a1=doubleArrayOf(")
            write_array(fw, configuration["anti_aliasing"]["a1"])
            fw.write("), a2=doubleArrayOf(")
            write_array(fw, configuration["anti_aliasing"]["a2"])
            fw.write("), b0=doubleArrayOf(")
            write_array(fw, configuration["anti_aliasing"]["b0"])
            fw.write("), b1=doubleArrayOf(")
            write_array(fw, configuration["anti_aliasing"]["b1"])
            fw.write("), b2=doubleArrayOf(")
            write_array(fw, configuration["anti_aliasing"]["b2"])
            fw.write("),sampleRatio=%d" % configuration["anti_aliasing"]["sample_ratio"])
            fw.write(")")
            fw.write(",\n    aWeighting=DigitalFilterConfiguration(filterDenominator=doubleArrayOf(")
            write_array(fw, configuration["a_weighting"]["filter_denominator"])
            fw.write("), filterNumerator=doubleArrayOf(")
            write_array(fw, configuration["a_weighting"]["filter_numerator"])
            fw.write("))") # end DigitalFilterConfiguration
            fw.write(",\n    cWeighting=DigitalFilterConfiguration(filterDenominator=doubleArrayOf(")
            write_array(fw, configuration["c_weighting"]["filter_denominator"])
            fw.write("), filterNumerator=doubleArrayOf(")
            write_array(fw, configuration["c_weighting"]["filter_numerator"])
            fw.write("))") # end DigitalFilterConfiguration
            fw.write(",\n    configuration=GeneralConfiguration(sampleRate=%d)"
                     % configuration["configuration"]["sample_rate"])
            fw.write(")\n") # end SpectrumChannel
            fw.write("}\n")


main()
