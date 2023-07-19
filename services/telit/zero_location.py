import sys

import gpsd
import argparse
import serial
import time
import threading
import zmq
import subprocess  # For executing a shell command


def ping(host):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """
    # Option for the number of packets as a function of
    param = '-c'
    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]
    return subprocess.call(command) == 0


def send_command(ser, cmd, comment=""):
    if len(comment) == 0:
        print("SEND: " + cmd)
    else:
        print("%s: %s" % (comment, cmd))
    ser.write(bytes(cmd + "\r", encoding='ascii'))
    return ser.read(64).decode("ascii").strip()


def lte_config(args):
    ####################
    # LTE Configuration and initialisation
    while True:
        try:
            with serial.Serial('/dev/ttyUSB2', 115200, timeout=5) as ser:
                print("Waiting for response")
                while "OK" not in send_command(ser, "AT"):
                    print("Not ready..")
                    time.sleep(1)
                print("Should return READY")
                print(send_command(ser, "AT+CPIN?"))
                print("Should return 3 or 4")
                resp = send_command(ser, "AT#USBCFG?")
                print(resp)
                while "USBCFG: 4" not in resp:
                    send_command(ser, "AT#USBCFG=4")
                    time.sleep(5)
                    send_command(ser, "AT#REBOOT")
                    time.sleep(35)
                    resp = send_command(ser, "AT#USBCFG?")
                    print(resp)
                print("Should return the APN details and IP address")
                resp = send_command(ser, "AT+CGDCONT?")
                print(resp)
                if args.apn not in resp:
                    print(send_command(ser, 'AT+CGDCONT=1,"%s","%s"' % (
                     'IPV4V6' if args.ipv6 else "IP", args.apn)))
                    print(send_command(ser, "AT#REBOOT"))
                    time.sleep(35)
                print("Should return 0,1")
                resp = send_command(ser, "AT#ECM?")
                print(resp)
                while "0,1" not in resp:
                    print("Start connection")
                    print(send_command(ser, "AT#ECM=1,0"))
                    while "OK" not in send_command(ser, "AT"):
                        print("Not ready..")
                        time.sleep(1)
                    print("Should return 0,1")
                    resp = send_command(ser, "AT#ECM?")
                    print(resp)
                print("Should return 0,1 or 0,5")
                print(send_command(ser, "AT+CREG?"))
                return
        except serial.serialutil.SerialException as e:
            print("Got disconnected from serial reason:\n%s" % e,
                  file=sys.stderr)
            wait(35)


def wait(wait_time):
    cpt = wait_time
    while cpt > 0:
        cpt -= 1
        print("Waiting %d" % cpt)
        time.sleep(1)


def gps_config(args):
    while True:
        try:
            with serial.Serial('/dev/ttyUSB2', 115200, timeout=5) as ser:
                print("Waiting for response")
                while "OK" not in send_command(ser, "AT"):
                    print("Not ready..")
                    time.sleep(1)
                print("READY")
                resp = send_command(ser, "AT$GPSP?")
                print(resp)
                while "GPSP: 1" not in resp:
                    resp = send_command(ser, "AT$GPSP=1", "Enable GPS")
                    print(resp)
                    if "ERROR" in resp:
                        print(send_command(ser, "AT$GPSRST", "Restore factory configuration"))
                        print(send_command(ser, "AT$GPSNVRAM=15,0", "Delete the GPS information stored in NVM"))
                        wait(10)
                        print(send_command(ser, "AT$GPSACP", "Check that after history buffer cleaning no GPS information is available"))
                        resp = send_command(ser, "AT$GPSP=1", "Enable GPS")
                        print(send_command(ser, "AT$GPSSAV", "save settings"))
                        wait(300)
                        resp = send_command(ser, "AT$GPSP?")
            return
        except serial.serialutil.SerialException as e:
            print("Got disconnected from serial reason:\n%s" % e,
                  file=sys.stderr)
            wait(35)


def main():
    parser = argparse.ArgumentParser(
        description='This program read json documents on zeromq channels'
                    ' and write in the specified folder', formatter_class=
        argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--apn", help="APN name", default="mmsbouygtel.com", type=str)
    parser.add_argument("--output_address",
                        help="Address for publishing JSON of GPS data",
                        default="tcp://*:10006")
    parser.add_argument("--ipv6",
                        help="Activate IPV6", default=False,
                        action="store_true")
    parser.add_argument("--wait_check",
                        help="Time to wait for next lte and GPS check",
                        default=300, type=int)
    parser.add_argument("--push_interval",
                        help="JSON GPS push interval in second",
                        default=1, type=int)
    parser.add_argument("-v", "--verbose",
                        help="Verbose mode", default=False,
                        action="store_true")
    parser.add_argument("--check_ip",
                        help="Check internet ip address",
                        default="8.8.8.8")

    args = parser.parse_args()
    args.running = True
    context = zmq.Context()
    socket_out = context.socket(zmq.PUB)
    try:
        while True:
            last_config_check = time.time()
            # configuration
            if not ping(args.check_ip):
                lte_config(args)
            gps_config(args)
            print("Connect to GPSD")
            gpsd.connect()
            while args.running:
                try:
                    # Get gps position
                    packet = gpsd.get_current()
                    document = {
                       "location": {
                           "type": "Point",
                           "coordinates": packet.position()
                       }, "properties": {
                            "accuracy": packet.position_precision(),
                            "speed": packet.speed(),
                            "speed_vertical": packet.speed_vertical(),
                            "altitude": packet.altitude(),
                            "time": packet.get_time().isoformat(),
                            "satellites": packet.sats,
                            "satellites_valid": packet.sats_valid
                        }
                    }
                    # Read stuff from telit
                    try:
                        with serial.Serial('/dev/ttyUSB2', 115200, timeout=5) as ser:
                            resp = send_command(ser, "AT#TEMPMON=1")
                            if "TEMPMEAS" in resp and "," in resp:
                                temperature = int(resp[resp.rfind(",") + 1:resp.find("\r")].strip())
                                document["temperature_module"] = temperature
                            resp = send_command(ser, "AT+CSQ")
                            if "CSQ:" in resp:
                                document["lte_strength"] = resp[resp.rfind(":") + 1:resp.find("\r")].strip()
                    except serial.serialutil.SerialException as e:
                        print("Got disconnected from serial reason:\n%s" % e,
                              file=sys.stderr)
                    if args.verbose:
                        print(repr(document))
                    socket_out.send_json(document)
                    last_push = time.time()
                    while time.time() < min(last_push + args.push_interval,
                                            last_config_check+args.wait_check):
                        time.sleep(0.1)
                    if time.time() >= last_config_check+args.wait_check:
                        break  # go check GPS and LTE status
                except Exception as e:
                    print(repr(e), file=sys.stderr)
                    time.sleep(5)
    finally:
        args.running = False


if __name__ == "__main__":
    main()
