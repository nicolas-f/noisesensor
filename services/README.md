This folder contain scripts that will use noisesensor to convert
a linux os into an advanced noise measurement device:

- Computation of noise indicators LZeq LAeq LCeq with iec_61672_1_2013 spectrum analysis.
- Sound classification using tensorflow light and Yamnet with 521 tags
- Optional recording of short audio sequence triggered by sound classification tags
- Storage of analysis into bulked compressed json files, compatible with big-data analysis such as Elastic-Search

On raspberry-pi, using symbolic link, customize and install all systemd services defined in [rpi_systemd](rpi_systemd) folder.
