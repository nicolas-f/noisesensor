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
import io
import os
import collections
import threading

ALERT_STACK_BYTES = 960000
ALERT_DELAY = 5.0


class ZeroMQThread(threading.Thread):
    def __init__(self, args, data: dict):
        threading.Thread.__init__(self)
        self.samples_queue = collections.deque()
        self.args = args
        self.data = data
        self.last_warning = 0

    def push_bytes(self, samples_bytes):
        self.samples_queue.append(samples_bytes)
        sum_bytes = sum([len(element) for element in self.samples_queue])
        if sum_bytes > ALERT_STACK_BYTES and \
                time.time() - self.last_warning > ALERT_DELAY:
            print("Warning buffer overflowing with %d bytes" % sum_bytes)
            self.last_warning = time.time()

    def run(self):
        interface = self.args.interface
        port = self.args.port

        context = zmq.Context()
        socket = context.socket(zmq.PUB)
        address = "tcp://%s:%d" % (interface, port)
        socket.bind(address)
        print("Publishing samples on interface:")
        print(address)
        while self.data["running"] or len(self.samples_queue) > 0:
            while len(self.samples_queue) > 0:
                audio_data_bytes = self.samples_queue.popleft()
                socket.send(audio_data_bytes)
            time.sleep(0.05)


class AudioFolderPlayListBuffer(io.BytesIO):
    def __init__(self, folder_or_file, sample_rate):
        super().__init__(b"")
        self.sample_rate = sample_rate
        self.playlist = []
        if os.path.isdir(folder_or_file):
            self.playlist = [folder_or_file+os.sep+filepath for filepath in os.listdir(folder_or_file) if filepath.lower().endswith(".wav")]
        else:
            self.playlist.append(folder_or_file)

    def get_bytes_rate(self):
        return self.sample_rate * 4

    def read(self, __size: int = ...) -> bytes:
        if len(self.getbuffer()) == self.tell():
            import soundfile as sf
            import random
            import numpy as np
            # push new data
            file_name = self.playlist[random.randrange(0, len(self.playlist))]
            print("Playing " + file_name)
            wav_data, sr = sf.read(file_name, dtype=np.int16)
            assert wav_data.dtype == np.int16, 'Bad sample type: %r' % wav_data.dtype
            waveform = wav_data / 32768.0  # Convert to [-1.0, +1.0]
            waveform = waveform.astype('float32')
            # Convert to mono and the sample rate expected by YAMNet.
            if len(waveform.shape) > 1:
              waveform = np.mean(waveform, axis=1)
            if sr != self.sample_rate:
                import resampy
                waveform = resampy.resample(waveform, sr, self.sample_rate)
            super().__init__(b"")
            self.write(waveform.tobytes())
            self.seek(0)
        return super().read(__size)


def publish_samples(args):
    block_size = args.block_size
    byte_rate = args.debug_byte_rate
    if byte_rate > 0:
        print("Warning zero_record in debug mode, sampling clocked at %d Hz" %
              byte_rate)
    if args.wave == "":
        input_buffer = sys.stdin.buffer
    else:
        input_buffer = AudioFolderPlayListBuffer(args.wave, args.sample_rate)
        byte_rate = input_buffer.get_bytes_rate()
    total_bytes_read = 0
    data = {"running": True}
    manager = ZeroMQThread(args=args, data=data)
    manager.start()
    start = time.time()
    try:
        while data["running"]:
            audio_data_bytes = input_buffer.read(block_size)
            if not audio_data_bytes:
                print("%s End of audio samples, total bytes read %d" %
                      (datetime.datetime.now().isoformat(), total_bytes_read))
                break
            manager.push_bytes(audio_data_bytes)
            total_bytes_read += len(audio_data_bytes)
            if byte_rate > 0:
                # if byte rate provided by user
                # pause time before reading the next bytes according to expected byte rate
                cur = time.time()
                samples_time = len(audio_data_bytes) / byte_rate
                if cur - start < samples_time:
                    time.sleep(samples_time - (cur - start))
                start = time.time()
    finally:
        data["running"] = False

def main():
    epilog = "example:\narecord --disable-softvol " \
             "-D plughw:CARD=U18dB,DEV=0 -r 48000 -f FLOAT_LE -c 1 -t raw" \
             " | python3 -u zero_record.py -p 10001 \n\n" \
             "python zero_record.py -w " \
             "../third_parties/yamnet/" \
             "24968__wwwbonsonca__train_tgv_passing_06.wav"

    parser = argparse.ArgumentParser(description=
                                     'This program read audio stream from'
                                     ' std input and publish through zeromq.',
                                     epilog=epilog, formatter_class=
                                     argparse.RawTextHelpFormatter)

    parser.add_argument("-p", "--port", help="Port to publish samples", default=10001, type=int)
    parser.add_argument("-i", "--interface", help="Interface to publish", default="*", type=str)
    parser.add_argument("-b", "--block_size", help="Number of bytes to publish per message", default=16000, type=int)
    parser.add_argument("-r", "--sample_rate", help="Set frequency of debug file", default=16000, type=int)
    parser.add_argument("--debug_byte_rate", help="You can use a raw file input and provide the expected bytes per"
                                                  " second of transfer", default=0, type=int)
    parser.add_argument("-w", "--wave", help="File name or folder containing wave file(s), will be used instead of"
                                             " stdin", default="", type=str)
    args = parser.parse_args()
    publish_samples(args)


if __name__ == "__main__":
    main()
