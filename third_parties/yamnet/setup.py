
from setuptools import setup


NAME = "yamnet"
VERSION = "1.0.0"
DESCR = "YAMNet is a pretrained deep net that predicts 521 audio event classes based on the AudioSet-YouTube corpus," \
        " and employing the Mobilenet_v1 depthwise-separable convolution architecture."
URL = "https://github.com/tensorflow/models/tree/master/research/audioset/yamnet"
REQUIRES = ["tensorflow"]

AUTHOR = "Manoj Plakal and Dan Ellis."
EMAIL = "dan.ellis - at - gmail.com"

LICENSE = "Apache2"

SRC_DIR = "yamnet"
PACKAGES = [SRC_DIR]

if __name__ == "__main__":
    setup(install_requires=REQUIRES,
          packages=PACKAGES,
          include_package_data=True,
          zip_safe=False,
          name=NAME,
          version=VERSION,
          description=DESCR,
          author=AUTHOR,
          author_email=EMAIL,
          url=URL,
          license=LICENSE
          )
