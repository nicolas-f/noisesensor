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





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This program read trigger tags from zeromq and display summary on '
                                                 'OLED display',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input_address", help="Address for zero_tigger tags", default="tcp://127.0.0.1:10002")
    args = parser.parse_args()
    print("Configuration: " + repr(args))
    display_tags(args)

