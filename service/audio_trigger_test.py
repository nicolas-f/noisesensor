import numpy
from scipy.spatial import distance
import matplotlib.pyplot as plt

ref_spectrum = numpy.genfromtxt('test/ref_audio.csv', delimiter=',', skip_header=1, usecols=range(5, 34))

test1_spectrum = numpy.genfromtxt('test/test1_near.csv', delimiter=',', skip_header=1, usecols=range(5, 34))

test2_spectrum = numpy.genfromtxt('test/test2_far.csv', delimiter=',', skip_header=1, usecols=range(5, 34))

ref_spectrum = numpy.rot90(ref_spectrum)

test1_spectrum = numpy.rot90(test1_spectrum)

test2_spectrum = numpy.rot90(test2_spectrum)


dist1 = [distance.cosine(ref_spectrum[idfreq], test1_spectrum[idfreq]) for idfreq in range(len(ref_spectrum))]
dist2 = [distance.cosine(ref_spectrum[idfreq], test2_spectrum[idfreq]) for idfreq in range(len(ref_spectrum))]

plt.subplot(3, 2, 1)

plt.imshow(ref_spectrum)

plt.subplot(3, 2, 3)

plt.imshow(test1_spectrum)

ax1 = plt.subplot(3, 2, 4)
plt.plot(dist1)

plt.subplot(3, 2, 5)

plt.imshow(test2_spectrum)

plt.subplot(3, 2, 6, sharey=ax1)
plt.plot(dist2)

plt.show()
