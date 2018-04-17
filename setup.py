from setuptools import setup, Extension
from Cython.Distutils import build_ext

NAME = "noisepy"
VERSION = "0.1"
DESCR = "Convert audio feed into noise indicators"
URL = "http://noise-planet.org"
REQUIRES = ['cython']

AUTHOR = "Nicolas Fortin"
EMAIL = "nicolas.fortin -at- ifsttar.fr"

LICENSE = "BSD3"

SRC_DIR = "noisepy"
PACKAGES = [SRC_DIR]

ext_1 = Extension(SRC_DIR + ".wrapped",
                  ["core/src/acoustic_indicators.c","core/src/kiss_fft.c", SRC_DIR + "/noisepy.pyx"],
                  libraries=[],
                  include_dirs=["core/include"])


EXTENSIONS = [ext_1]

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
          cmdclass={"build_ext": build_ext},
          ext_modules=EXTENSIONS
          )
