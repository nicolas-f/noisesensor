"""
 Display sound recognition tags into Grove - OLED Yellow&Blue Display 0.96(SSD1315)
"""

import argparse
import zmq
import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
import json
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


def display_tags(config):
    # Raspberry Pi pin configuration:
    rst = None  # on the PiOLED this pin isnt used
    i2c_address = 0x3C
    disp = Adafruit_SSD1306.SSD1306_128_64(rst=rst, i2c_address=i2c_address)
    # Initialize library.
    disp.begin()

    # Clear display.
    disp.clear()
    disp.display()

    # Create blank image for drawing.
    # Make sure to create image with mode '1' for 1-bit color.
    width = disp.width
    height = disp.height
    image = Image.new('1', (width, height))

    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)

    # Draw a black filled box to clear the image.
    draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Draw some shapes.
    # First define some constants to allow easy resizing of shapes.
    padding = -2
    top = padding
    bottom = height - padding
    # Move left to right keeping track of the current x position for drawing shapes.
    x = 0

    # Load default font.
    font = ImageFont.load_default()

    draw.text((x, top), "Waiting next trigger..", font=font, fill=255)
    disp.image(image)
    disp.display()

    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(config.input_address)
    socket.subscribe("")
    line_height = 8
    while True:

        # Retrieve JSON data from zero_trigger
        data = socket.recv_json()

        # Draw a black filled box to clear the image.
        draw.rectangle((0, 0, width, height), outline=0, fill=0)

        leq = data["leq"]
        scores = data["scores"]
        draw.text((x, top), "leq: %.2f dB" % leq, font=font, fill=255)
        max_line = 7
        for y, key_value in zip(range(len(scores)), sorted(scores.items(), key=lambda item: -item[1])):
            tag = key_value[0][slice(None, 12)]
            draw.text((x, top + 2 * line_height + line_height * y), '{:12s} {:d} %'.format(tag, int(key_value[1])),
                      font=font, fill=255)
            if y >= max_line:
                break
        # Display image.
        disp.image(image)
        disp.display()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This program read trigger tags from zeromq and display summary on '
                                                 'OLED display',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input_address", help="Address for zero_tigger tags", default="tcp://127.0.0.1:10002")
    args = parser.parse_args()
    print("Configuration: " + repr(args))
    display_tags(args)
