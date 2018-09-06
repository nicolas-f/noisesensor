import scipy.io.wavfile
import scipy.signal
from scipy.interpolate import interp1d
import numpy as np
import sys
import math


def rms(signal):
    return math.sqrt(np.mean(signal**2))

# Converted from https://fr.mathworks.com/matlabcentral/fileexchange/40455-computes-the-total-harmonic-distortion-thd-of-a-signal
def THDNoctave(f0, signal, sample_rate):
    signal = signal.astype(np.double)
    sample_rate = float(sample_rate)
    if not rms(signal) > 0:
        print "no signal"
        return
    t = np.arange(0, len(signal)/sample_rate, 1/sample_rate)
    T = len(signal)/sample_rate
    freq = f0
    # condition input time vector
    input_error = 0
    # add two samples to complete the last cycle.
    dtt = 1/sample_rate
    x = signal

    # truncate extra samples, to fit in an integer number of cycles of freq
    T = math.floor(T * freq) / freq

    # resample on a linear grid:
    # t1, x1 is the new input, not including the last sample
    x = x - sum(x)/len(x)  # remove any DC offset

    N = max(1e6, len(x))   # number of samples
    dt = T/N
    t1 = np.arange(0, t[-1], dt)  # 0:dt:(T-dt);
    x1 = interp1d(t, x, kind='cubic')(t1) #interp1(t,x,t1,'cubic');

    # compute cos-sin fourier coefficients
    w = 2*math.pi*freq
    acs = (2/T) * sum(x1*np.cos(w*t1))*dt  # basic frequency cos coefficient.
    bsn = (2/T) * sum(x1*np.sin(w*t1))*dt  # basic frequency sin coefficient.
    amp = (acs**2 + bsn**2)**0.5
    ph = math.pi/2 - np.sign(acs) * math.acos(bsn/amp)

    rms22 = (2/T) * sum(x1**2) * dt
    THD = (rms22/amp**2 - 1)**0.5

    # correct phase to be in the range [-pi : pi]
    if ph > math.pi:
        ph = ph - 2*math.pi
    if ph < -math.pi:
        ph = ph + 2*math.pi

    print "THD+N:     %.1f%% or %.1f dB" % (THD * 100, 20 * math.log10(THD))

    return THD, ph, amp


def THDN(f0, signal, sample_rate):
    signal = signal.astype(np.double)
    signal = signal * scipy.signal.hann(len(signal))
    if not rms(signal) > 0:
        print "no signal"
        return


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

    return (thdn, 0, 0)

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
def testSquare():
    # Square signal analytic expected result
    analytic_result = math.sqrt((math.pi**2/8.)-1)
    freq = 10.
    number_of_cycles = 4
    dt = 0.0001
    t = np.arange(0, number_of_cycles / freq, dt)
    x = (np.mod(t, 1. / freq) < 0.5 / freq)
    x = 1 * (2 * x - 1)
    print "expected %.4f got %.4f " % (analytic_result, THDN(freq, x, 1/dt)[0])

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
    testSquare()
    sys.exit("You must provide the test frequency and at least one file to analyze")

