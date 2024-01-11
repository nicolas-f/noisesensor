# Sixfab Telit LE910C4-EU

This python module connect to, configure Sixfab Telit LE910C4-EU Raspberry pi hat.

GPS locations are transmitted through zeromq.

# configure access to pi with /dev/ttyUSB2

You may have to reboot or logout/login after usemod

```shell
sudo usermod -a -G dialout pi
sudo systemctl stop ModemManager.service
sudo systemctl disable ModemManager.service
```

# Install gpsd

```shell
sudo apt-get install gpsd
```

Select ttyUSB1 for device

```shell
sudo nano /etc/default/gpsd
```

```ini
# Devices gpsd should collect to at boot time.
# They need to be read/writeable, either by user gpsd or the group dialout.
DEVICES="/dev/ttyUSB1"

# Other options you want to pass to gpsd
GPSD_OPTIONS=""

# Automatically hot add/remove USB GPS devices via gpsdctl
USBAUTO="true"
```

Install libs

```shell
pip install -r requirements.txt
```

You can see GPS status using the application `gpsmon`

