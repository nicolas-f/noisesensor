import os
from setuptools import setup, Extension

NAME = "noisepy"
VERSION = "1.2.0"
DESCR = "Convert audio feed into noise indicators"
URL = "http://noise-planet.org"
REQUIRES = []

AUTHOR = "Nicolas Fortin"
EMAIL = "nicolas.fortin -at- ifsttar.fr"

LICENSE = "BSD3"

SRC_DIR = "noisepy"
PACKAGES = [SRC_DIR]

try:
    import Cython
    USE_CYTHON = True
except ImportError as e:
    USE_CYTHON = False

ext = ".pyx" if USE_CYTHON else ".c"

ext_1 = Extension(SRC_DIR + ".wrapped",
                  ["core/src/acoustic_indicators.c","core/src/kiss_fft.c","core/src/kiss_fftr.c", SRC_DIR + "/noisepy" + ext],
                  libraries=[],
                  include_dirs=["core/include"])

EXTENSIONS = [ext_1]

if USE_CYTHON:
    from Cython.Build import cythonize
    EXTENSIONS = cythonize(EXTENSIONS)

if __name__ == "__main__":
    setup(install_requires=REQUIRES,
          packages=PACKAGES,
          zip_safe=False,
          name=NAME,
          version=VERSION,
          description=DESCR,
          author=AUTHOR,
          author_email=EMAIL,
          url=URL,
          license=LICENSE,
          test_suite="tests",
          ext_modules=EXTENSIONS
          )
