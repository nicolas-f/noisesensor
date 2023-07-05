# on root account (sudo su)
# install dep with pip install -r requirements.txt
# execute with cron (crontab -e)
# @reboot /usr/bin/python /home/pi/noisesensor/services/telit/autoconnect.py > autoconnect.log

import time
import serial
from colorama import Fore, Back, Style


def send_command(ser, cmd):
    print(Fore.YELLOW + cmd + Fore.RESET)
    ser.write(bytes(cmd + "\r", encoding='ascii'))
    return ser.read(64).decode("ascii").strip()


def print_comment(comment):
    print(Fore.GREEN + comment + Fore.RESET)


def main():
    while True:
        try:
            with serial.Serial('/dev/ttyUSB2', 115200, timeout=5) as ser:
                print_comment("Waiting for response")
                while "OK" not in send_command(ser, "AT"):
                    print_comment("Not ready..")
                    time.sleep(1)
                print_comment("Should return READY")
                print(send_command(ser, "AT+CPIN?"))
                print_comment("Should return 3 or 4")
                resp = send_command(ser, "AT#USBCFG?")
                print(resp)
                while "USBCFG: 4" not in resp:
                    send_command(ser, "AT#USBCFG=4")
                    time.sleep(5)
                    send_command(ser, "AT#REBOOT")
                    time.sleep(35)
                    resp = send_command(ser, "AT#USBCFG?")
                    print(resp)
                print_comment("Should return the APN details and IP address")
                resp = send_command(ser, "AT+CGDCONT?")
                print(resp)
                if "mmsbouygtel" not in resp:
                    print(send_command(ser, 'AT+CGDCONT=1,"IP","mmsbouygtel.com"'))
                    print(send_command(ser, 'AT+CGDCONT=2,"IPV4V6",""'))
                    print(send_command(ser, 'AT+CGDCONT=3,"IPV4V6",""'))
                    print(send_command(ser, "AT#REBOOT"))
                    time.sleep(35)
                print_comment("Should return 0,1")
                resp = send_command(ser, "AT#ECM?")
                print(resp)
                while "0,1" not in resp:
                    print_comment("Start connection")
                    print(send_command(ser, "AT#ECM=1,0"))
                    while "OK" not in send_command(ser, "AT"):
                        print_comment("Not ready..")
                        time.sleep(1)
                    print_comment("Should return 0,1")
                    resp = send_command(ser, "AT#ECM?")
                    print(resp)
                print_comment("Should return 0,1 or 0,5")
                print(send_command(ser, "AT+CREG?"))
                return
        except serial.serialutil.SerialException:
            pass

main()
