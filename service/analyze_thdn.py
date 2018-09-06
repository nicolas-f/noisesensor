import scipy.io.wavfile
import scipy.signal
import numpy as np
import sys
import math
from matplotlib import pyplot


def rms(signal):
    return math.sqrt(np.mean(signal**2))


def THDN(f0, signal, sample_rate):
    signal = signal.astype(np.double)
    signal = signal * scipy.signal.hann(len(signal))
    if not rms(signal) > 0:
        print "no signal"
        return
    # remove first 2000 samples
    if len(signal) < sample_rate:
        sys.exit("Not enough signal length")

    #f0 Frequency to be removed from signal (Hz)
    q = math.trunc(math.sqrt(f0) / 2.)
    w0 = f0 / (sample_rate / 2.)
    b, a = scipy.signal.iirnotch(w0, q)

    filtered_signal = scipy.signal.filtfilt(b, a, signal)

    signal_original = signal

    #scipy.io.wavfile.write("filtered.wav", sample_rate, filtered_signal / max(signal))

    total_rms = rms(signal_original)
    other_rms = rms(filtered_signal)
    print "origin rms: %.2f filtered rms: %.2f" % (total_rms, other_rms)
    # thdn is (noise+harmonic) / fundamental
    thdn = other_rms / total_rms
    print "THD+N:     %.1f%% or %.1f dB" % (thdn * 100, 20 * math.log10(thdn))

def analyze_channels(freq, filename, function):
    """
    Given a filename, run the given analyzer function on each channel of the
    file
    """
    sample_rate, signal = scipy.io.wavfile.read(filename)
    print 'Analyzing "' + filename + '"...'

    if len(signal.shape) == 1:
        # Monaural
        function(freq, signal, sample_rate)
    elif signal.shape[1] == 2:
        # Stereo
        if np.array_equal(signal[:, 0], signal[:, 1]):
            print '-- Left and Right channels are identical --'
            function(freq, signal[:, 0], sample_rate)
        else:
            print '-- Left channel --'
            function(freq, signal[:, 0], sample_rate)
            print '-- Right channel --'
            function(freq, signal[:, 1], sample_rate)
    else:
        # Multi-channel
        for ch_no, channel in enumerate(signal.transpose()):
            print '-- Channel %d --' % (ch_no + 1)
            function(freq, channel, sample_rate)


if len(sys.argv) >= 2:
    files = sys.argv[2:]
    freq = float(sys.argv[1])
    for filename in files:
        try:
            analyze_channels(freq, filename, THDN)
        except Exception as e:
            print 'Couldn\'t analyze "' + filename + '"'
            print e
        print ''
else:
    sys.exit("You must provide the test frequency and at least one file to analyze")

