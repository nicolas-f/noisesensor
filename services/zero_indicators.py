import datetime
import noisepy
import sys
import argparse
import zmq


class AcousticIndicatorsProcessor:
    def __init__(self, config):
        self.config = config
        self.epoch = datetime.datetime.utcfromtimestamp(0)

    def init_socket(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect(self.config.input_address)
        self.socket.subscribe("")
    def unix_time(self):
        return (datetime.datetime.utcnow() - self.epoch).total_seconds()

    def run(self):
        self.init_socket()
        # sensitivity of my Umik-1 is -28.34 dBFS @ 94 dB/1khz
        db_delta = 94 - self.config("sensitivity") 
        ref_sound_pressure = 1 / 10 ** (db_delta / 20.)
        audio_bytes = self.socket.recv()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This program read audio stream from zeromq and publish noise events',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--configuration_file", help="Configuration file created with filterdesign.py")
    parser.add_argument("--sensitivity", help="Microphone sensitivity in dBFS at 94 dB 1 kHz", default=-28.34, type=float)
    parser.add_argument("--input_address", help="Address for zero_record samples", default="tcp://127.0.0.1:10001")
    args = parser.parse_args()
    print("Configuration: " + repr(args))
    ai = AcousticIndicatorsProcessor(args)
    ai.run()

