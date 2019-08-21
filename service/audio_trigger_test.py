import numpy
from scipy.spatial import distance
import matplotlib.pyplot as plt

trigger = [40.49, 39.14, 34.47, 30.5, 39.54, 31.98, 38.37, 43.84, 36.09, 43.72, 40.55, 39.25, 39.15, 38.36, 38.3, 36.58,
           39.9, 47.76, 51.64, 37.2, 44.89, 46.6, 51.08, 37.77, 28, 29.59, 30.25, 23.16, 25.74]
weight = [0.04,0.04,0.04,0.04,0.04,0.04,0.04,0.14,0.14,0.14,0.14,0.14,0.14,0.14,0.14,0.14,0.14,0.14,0.14, 0.24, 0.41,
          0.60, 0.80, 0.94, 1.0, 0.94, 0.80, 0.60, 0.41]

ref_spectrum = numpy.genfromtxt('test/test2_far.csv', delimiter=',', skip_header=1, usecols=range(5, 34))

test1_spectrum = numpy.genfromtxt('test/test1_near.csv', delimiter=',', skip_header=1, usecols=range(5, 34))

test2_spectrum = numpy.genfromtxt('test/test2_far_far.csv', delimiter=',', skip_header=1, usecols=range(5, 34))

dist0 = numpy.ones(len(ref_spectrum)) - [distance.cosine(trigger, ref_spectrum[idfreq], w=weight) for idfreq in range(len(ref_spectrum))]
dist1 = numpy.ones(len(ref_spectrum)) - [distance.cosine(trigger, test1_spectrum[idfreq], w=weight) for idfreq in range(len(ref_spectrum))]
dist2 = numpy.ones(len(ref_spectrum)) - [distance.cosine(trigger, test2_spectrum[idfreq], w=weight) for idfreq in range(len(ref_spectrum))]

ref_spectrum = numpy.rot90(ref_spectrum)

test1_spectrum = numpy.rot90(test1_spectrum)

test2_spectrum = numpy.rot90(test2_spectrum)

plt.subplot(3, 2, 1)

plt.imshow(ref_spectrum)

ax1 = plt.subplot(3, 2, 2)

ax1.set_ylim(0.98, 1.0)

plt.bar(numpy.arange(len(dist0)), dist0)

plt.subplot(3, 2, 3)

plt.imshow(test1_spectrum)

plt.subplot(3, 2, 4, sharey=ax1)

plt.bar(numpy.arange(len(dist1)), dist1)

plt.subplot(3, 2, 5)

plt.imshow(test2_spectrum)

plt.subplot(3, 2, 6, sharey=ax1)
plt.bar(numpy.arange(len(dist2)), dist2)

plt.show()
