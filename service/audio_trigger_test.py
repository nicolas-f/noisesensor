import numpy
from scipy.spatial import distance
import matplotlib.pyplot as plt
from itertools import izip
import math

def cosine_distance(a, b, weight = None):
    assert len(a) == len(b)
    if weight is None:
        weight = [1.0] * len(a)
    ab_sum, a_sum, b_sum = 0, 0, 0
    for ai, bi, wi in izip(a, b, weight):
        ab_sum += ai * bi
        a_sum += ai * ai
        b_sum += bi * bi
    return 1 - ab_sum / math.sqrt(a_sum * b_sum)

# from scipy
def _validate_weights(w, dtype=numpy.double):
    w = _validate_vector(w, dtype=dtype)
    if numpy.any(w < 0):
        raise ValueError("Input weights should be all non-negative")
    return w

# from scipy
def _validate_vector(u, dtype=None):
    # XXX Is order='c' really necessary?
    u = numpy.asarray(u, dtype=dtype, order='c').squeeze()
    # Ensure values such as u=1 and u=[1] still return 1-D arrays.
    u = numpy.atleast_1d(u)
    if u.ndim > 1:
        raise ValueError("Input vector should be 1-D.")
    return u

# from scipy
def dist_cosine(u, v, w=None):
    u = _validate_vector(u)
    v = _validate_vector(v)
    if w is not None:
        w = _validate_weights(w)
    uv = numpy.average(u * v, weights=w)
    uu = numpy.average(numpy.square(u), weights=w)
    vv = numpy.average(numpy.square(v), weights=w)
    dist = 1.0 - uv / numpy.sqrt(uu * vv)
    return dist

def autocolor(bar):
    for col in bar:
        if col.get_height() > 0.995:
            col.set_color('r')

trigger = [40.49, 39.14, 34.47, 30.5, 39.54, 31.98, 38.37, 43.84, 36.09, 43.72, 40.55, 39.25, 39.15, 38.36, 38.3, 36.58,
           39.9, 47.76, 51.64, 37.2, 44.89, 46.6, 51.08, 37.77, 28, 29.59, 30.25, 23.16, 25.74]
weight = [0.04,0.04,0.04,0.04,0.04,0.04,0.04,0.14,0.14,0.14,0.14,0.14,0.14,0.14,0.14,0.14,0.14,0.14,0.14, 0.24, 0.41,
          0.60, 0.80, 0.94, 1.0, 0.94, 0.80, 0.60, 0.41]

ref_spectrum = numpy.genfromtxt('test/test2_far.csv', delimiter=',', skip_header=1, usecols=range(5, 34))

test1_spectrum = numpy.genfromtxt('test/test1_near.csv', delimiter=',', skip_header=1, usecols=range(5, 34))

test2_spectrum = numpy.genfromtxt('test/test2_far_far.csv', delimiter=',', skip_header=1, usecols=range(5, 34))

test3_spectrum = numpy.genfromtxt('test/test_background.csv', delimiter=',', skip_header=1, usecols=range(5, 34))

dist0 = numpy.ones(len(ref_spectrum)) - [distance.cosine(trigger, ref_spectrum[idfreq], w=weight) for idfreq in range(len(ref_spectrum))]
dist1 = numpy.ones(len(ref_spectrum)) - [distance.cosine(trigger, test1_spectrum[idfreq], w=weight) for idfreq in range(len(ref_spectrum))]
dist2 = numpy.ones(len(ref_spectrum)) - [distance.cosine(trigger, test2_spectrum[idfreq], w=weight) for idfreq in range(len(ref_spectrum))]
dist3 = numpy.ones(len(ref_spectrum)) - [distance.cosine(trigger, test3_spectrum[idfreq], w=weight) for idfreq in range(len(ref_spectrum))]

dist0_bis = numpy.ones(len(ref_spectrum)) - [dist_cosine(trigger, ref_spectrum[idfreq], w=weight) for idfreq in range(len(ref_spectrum))]

#print(numpy.around(dist0_bis - dist0, 3))

ref_spectrum = numpy.rot90(ref_spectrum)

test1_spectrum = numpy.rot90(test1_spectrum)

test2_spectrum = numpy.rot90(test2_spectrum)

test3_spectrum = numpy.rot90(test3_spectrum)

plt.subplot(4, 2, 1)

plt.imshow(ref_spectrum)

ax1 = plt.subplot(4, 2, 2)

autocolor(plt.bar(numpy.arange(len(dist0)), dist0))

plt.subplot(4, 2, 3)

plt.imshow(test1_spectrum)

plt.subplot(4, 2, 4, sharey=ax1)

autocolor(plt.bar(numpy.arange(len(dist1)), dist1))

plt.subplot(4, 2, 5)

plt.imshow(test2_spectrum)

plt.subplot(4, 2, 6, sharey=ax1)
autocolor(plt.bar(numpy.arange(len(dist2)), dist2))


plt.subplot(4, 2, 7)

plt.imshow(test3_spectrum)

plt.subplot(4, 2, 8, sharey=ax1)
plt.bar(numpy.arange(len(dist2)), dist3)

ax1.set_ylim([0.95, 1.0])

plt.show()
