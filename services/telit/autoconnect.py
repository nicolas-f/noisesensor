# on root account (sudo su)
# install dep with pip install -r requirements.txt
# execute with cron (crontab -e)
# @reboot /usr/bin/python /home/pi/noisesensor/services/telit/autoconnect.py > autoconnect.log

import time
import serial
from colorama import Fore, Back, Style

def send_command(ser, cmd):
    ser.write(bytes(cmd + "\r", encoding='ascii'))
    return ser.read(64).decode("ascii").strip()

def print_comment(comment):
    print(Fore.GREEN + comment + Fore.RESET)


def main():
    with serial.Serial('/dev/ttyUSB2', 115200, timeout=5) as ser:
        print_comment("Waiting for response")
        while "OK" not in send_command(ser, "AT"):
            print_comment("Not ready..")
            time.sleep(1)
        print_comment("Should return 3 or 4")
        print(send_command(ser, "AT#USBCFG?"))
        print_comment("Should return 0,1")
        print(send_command(ser, "AT#ECM?"))
        print_comment("Should return READY")
        print(send_command(ser, "AT+CPIN?"))
        print_comment("Should return 0,1 or 0,5")
        print(send_command(ser, "AT+CREG?"))
        print_comment("Should return the APN details and IP address")
        print(send_command(ser, "AT+CGDCONT?"))
        print_comment("Start connection")
        print(send_command(ser, "AT#ECM=1,0"))


main()
