#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
BSD 3-Clause License

Copyright (c) 2022, Université Gustave-Eiffel
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import sys
import zmq
import argparse
import time
import datetime

def publish_samples(interface: str, port: int, block_size: int, byte_rate: int):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    address = "tcp://%s:%d" % (interface, port)
    socket.bind(address)
    print("Publishing samples on interface:")
    print(address)
    input_buffer = sys.stdin.buffer
    start = time.time()
    total_bytes_read = 0
    while True:
        audio_data_bytes = input_buffer.read(block_size)
        if not audio_data_bytes:
            print("%s End of audio samples, total bytes read %d" % (datetime.datetime.now().isoformat(),
                                                                    total_bytes_read))
            break
        total_bytes_read += len(audio_data_bytes)
        if byte_rate > 0:
            # if byte rate provided by user
            # pause time before reading the next bytes according to expected byte rate
            cur = time.time()
            samples_time = len(audio_data_bytes) / byte_rate
            if cur - start < samples_time:
                time.sleep(samples_time - (cur - start))
            start = time.time()
        # audio_data contains a list of block_size // 4 floats representing audio values
        socket.send(audio_data_bytes)


def main():
    parser = argparse.ArgumentParser(description='This program read audio stream from std input and publish through'
                                                 ' zeromq.', epilog='''example:  arecord --disable-softvol -D 
                                                 plughw:CARD=U18dB,DEV=0 -r 48000 -f FLOAT_LE -c 1 -t raw |
                                                 python3 -u zero_record.py -p 10001''',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-p", "--port", help="Port to publish samples", default=10001, type=int)
    parser.add_argument("-i", "--interface", help="Interface to publish", default="*", type=str)
    parser.add_argument("-b", "--block_size", help="Number of bytes to publish per message", default=1024, type=int)
    parser.add_argument("--debug_byte_rate", help="You can use a raw file input and provide the expected bytes per"
                                                  " second of transfer", default=0, type=int)
    args = parser.parse_args()
    publish_samples(args.interface, args.port, args.block_size, args.debug_byte_rate)


if __name__ == "__main__":
    main()
