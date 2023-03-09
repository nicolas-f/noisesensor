import asyncio
from bleak import BleakClient
from bleak import BleakScanner
import logging
import zmq
import argparse

UUID_NORDIC_TX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
UUID_NORDIC_RX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
logger = logging.getLogger(__name__)


def uart_data_received(sender, data):
    print("RX> {0}".format(data.decode('UTF-8')))


def process_message(socket):
    logger.info("Waiting for next zmq message")
    data = socket.recv_json()

    leq = data["leq"]
    scores = data["scores"]
    messages = ["leq: %.2f dB" % leq]
    max_line = 7
    for y, key_value in zip(range(len(scores)), sorted(scores.items(), key=lambda item: -item[1])):
        tag = key_value[0][slice(None, 12)]
        messages.append('{:12s}: {:.3f}'.format(tag, key_value[1]))
        if y >= max_line:
            break
    return b"\x03\x10messages=%s;\n\x10updateScreen();\n" % repr(messages).encode('UTF-8')


async def main(config):
    address = None
    while address is None:
        logger.info("Discover BLE devices..")
        devices = await BleakScanner.discover()
        for d in devices:
            if "Pixl.js" in d.name:
                address = d.address
                logger.info("Found Pixl.js " + repr(d))
                break
        if address is None:
            logger.info("Could not find Pixl.js device.")
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(config.input_address)
    socket.subscribe("")
    while True:
        c = process_message(socket)
        logger.info("Reconnect to " + repr(address))
        async with BleakClient(address) as client:
            await client.start_notify(UUID_NORDIC_RX, uart_data_received)
            while True:
                while len(c) > 0:
                    await client.write_gatt_char(UUID_NORDIC_TX, bytearray(c[0:20]), True)
                    c = c[20:]
                await asyncio.sleep(0.125)  # wait for a response
                event = socket.poll(timeout=config.disconnect_ble_timeout)
                if event == 0:
                    # Timeout, disconnect
                    break
                else:
                    process_message(socket)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This program read trigger tags from zeromq and display summary on '
                                                 'OLED display',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input_address", help="Address for zero_trigger tags", default="tcp://127.0.0.1:10002")
    parser.add_argument("--disconnect_ble_timeout", help="Disconnect ble if no new message in this delay in seconds",
                        default=10, type=int)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(args))

