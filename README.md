# NoiseSensor

Realtime computing of noise indicators and recognition of noise source.

# Launch unit test

```shell
tox run
```

# Install on Raspberry Pi

Clone or copy this repository on the rpi.

Install noisesensor library (from repository folder)

```shell
pip install .
```

Install services dependencies

```shell
cd services
pip -r requirements.txt
```

Edit recording service with the characteristics of your microphone (device name/sampling rate)

Select plughw:XXX in order to be able to output audio samples in FLOAT format.

```shell
arecord -L
nano rpi_systemd/zerorecord.service
```


Install systemd services

```shell
cd /etc/systemd/system
sudo ln -s /home/pi/noisesensor/services/rpi_systemd/*.service ./
sudo systemctl daemon-reload
sudo systemctl enable zero*
```



