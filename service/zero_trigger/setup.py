
from setuptools import setup


NAME = "zero_trigger"
VERSION = "1.0.0"
DESCR = "zero_trigger use zeromq and yamnet in order to detect noise events an publish json documents according to" \
        "configured parameters"
URL = "https://github.com/nicolas-f/noisesensor"
REQUIRES = ["yamnet"]

AUTHOR = "Nicolas Fortin"
EMAIL = "nicolas.fortin - at - univ-eiffel.fr"

LICENSE = "Apache2"

SRC_DIR = "src"
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
