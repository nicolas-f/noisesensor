# noisesensor

[![NoiseSensor](https://github.com/nicolas-f/noisesensor/actions/workflows/build_noisesensor.yml/badge.svg)](https://github.com/nicolas-f/noisesensor/actions/workflows/build_noisesensor.yml)

Convert audio feed into noise indicators

## Installation

```shell
python3 -m venv venv
source venv/bin/activate
pip3 install cython
pip3 install .
```

# ZeroMQ services

Example with zero_record on rpi (raspbian):

Install the following systemd service by creating a file in

/etc/systemd/system/zerorecord.service

```ini
[Unit]
Description=Redirect audio samples to ZeroMQ publishing service
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/arecord -D plughw:CARD=Audio,DEV=0 -r 16000 -f FLOAT_LE -c 1 | /home/pi/noisesensor/venv/bin/python3 service/zero_record.py --block_size 32000
WorkingDirectory=/home/pi/noisesensor/
Restart=always
RestartSec=5s
User=pi
[Install]
WantedBy=multi-user.target
```

You can list all compatible device with this command

```bash
arecord -L
```




Then to install the service on the system:

```bash
sudo systemctl daemon-reload
sudo systemctl enable zerorecord
sudo systemctl start zerorecord
```

