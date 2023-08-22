#!/usr/bin/env python
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

import datetime
import os.path
import time
from noisesensor.spectrumchannel import SpectrumChannel, compute_leq
import sys
import argparse
import zmq
import numpy as np
import json


def epoch_to_elasticsearch_date(epoch):
    """
    strict_date_optional_time in elastic search format is
    yyyy-MM-dd'T'HH:mm:ss.SSSZ
    @rtype: string
    """
    return datetime.datetime.utcfromtimestamp(epoch).strftime(
        "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def generate_stack_dict(filter_config, push_time):
    stack_dict = {"LZeq": []}
    fields = []
    if "bandpass" in filter_config:
        fields = ["%gHZ" % bp["nominal_frequency"] for bp in
                  filter_config["bandpass"]]
    if "a_weighting" in filter_config:
        stack_dict["LAeq"] = []
    if "c_weighting" in filter_config:
        stack_dict["LCeq"] = []
    for field in fields:
        stack_dict[field] = []
    if push_time:
        stack_dict["timestamps"] = []
    return fields, stack_dict


class AcousticIndicatorsProcessor:
    def __init__(self, config):
        self.config = config
        self.epoch = datetime.datetime.utcfromtimestamp(0)
        self.total_read = 0
        self.current_stack_time = 0
        self.filter_config = json.load(open(self.config.configuration_file,
                                            "r"))
        self.channel = SpectrumChannel(self.filter_config, use_scipy=False,
                                       use_cascade=True)
        fields, stack_dict = generate_stack_dict(self.filter_config,
                                                 self.config.output_time)
        self.fields = fields
        self.current_stack_dict = stack_dict
        self.stack_count = 0
        self.socket = None
        self.socket_out = None

    def init_socket(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect(self.config.input_address)
        self.socket.subscribe("")
        self.socket_out = context.socket(zmq.PUB)
        self.socket_out.bind(self.config.output_address)

    def run(self):
        self.init_socket()
        sample_rate = self.filter_config["configuration"]["sample_rate"]
        # sensitivity of my Umik-1 is -28.34 dBFS @ 94 dB/1khz
        db_delta = 94 - self.config.sensitivity
        ref_sound_pressure = 1 / 10 ** (db_delta / 20.)
        window_samples = int(
            self.config.window * self.filter_config["configuration"][
                "sample_rate"])
        if sample_rate % (
                1 / self.config.window) != 0:
            print("Warning ! window does not fit with sample rate")
        current_window = np.zeros(shape=window_samples, dtype=np.single)
        cursor = 0
        while True:
            audio_data_bytes = np.frombuffer(self.socket.recv(),
                                             dtype=np.single)
            if self.current_stack_time == 0:
                self.current_stack_time = time.time() - len(audio_data_bytes)\
                          / self.filter_config["configuration"]["sample_rate"]
            buffer_cursor = 0
            while buffer_cursor < len(audio_data_bytes):
                # Process part of samples to fit configured windows
                to_read = min(window_samples-cursor, len(audio_data_bytes)
                              - buffer_cursor)
                current_window[cursor:cursor+to_read] = \
                    audio_data_bytes[buffer_cursor:buffer_cursor+to_read]
                cursor += to_read
                buffer_cursor += to_read
                self.total_read += to_read
                if cursor == window_samples:
                    # analysis window filled
                    cursor = 0
                    lzeq = round(compute_leq(current_window) + db_delta, 2)
                    self.current_stack_dict["LZeq"].append(lzeq)
                    if "a_weighting" in self.filter_config:
                        laeq = round(self.channel.process_samples_weight_a(
                            current_window) + db_delta, 2)
                        self.current_stack_dict["LAeq"].append(laeq)
                    if "c_weighting" in self.filter_config:
                        lceq = round(self.channel.process_samples_weight_c(
                            current_window) + db_delta, 2)
                        self.current_stack_dict["LCeq"].append(lceq)
                    if "bandpass" in self.filter_config:
                        spectrum = self.channel.process_samples(current_window)
                        for column, lzeq in zip(self.fields, spectrum):
                            self.current_stack_dict[column].append(
                                round(lzeq + db_delta, 2))
                    if self.config.output_time:
                        self.current_stack_dict["timestamps"].append(
                            round(time.time() - window_samples/sample_rate, 3))
                    self.stack_count += 1
                    if self.stack_count == self.config.output_stack:
                        # stack of noise indicator complete
                        # send the full document
                        self.stack_count = 0
                        self.current_stack_dict[
                            "date_start"] = epoch_to_elasticsearch_date(
                            self.current_stack_time)
                        self.current_stack_dict[
                            "date_end"] = epoch_to_elasticsearch_date(
                            time.time())
                        self.socket_out.send_json(self.current_stack_dict)
                        self.current_stack_time = 0
                        fields, stack_dict = generate_stack_dict(
                            self.filter_config, self.config.output_time)
                        self.current_stack_dict = stack_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='This program read audio stream from zeromq and publish'
                    ' noise events', formatter_class=
        argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-c", "--configuration_file", help="Configuration file generated by filterdesign.py", required=True, type=str)
    parser.add_argument("--sensitivity", help="Microphone sensitivity in dBFS at 94 dB 1 kHz", default=-28.34, type=float)
    parser.add_argument("-w", "--window", help="Will produce one indicator per provided time frame in seconds", default=0.125, type=float)
    parser.add_argument("-s", "--output_stack", help="Each output document will provide this number of indicators (related to window)", default=80, type=int)
    parser.add_argument("-t", "--output_time",
                        help="Output time for each time frame", default=False,
                        action="store_true")
    parser.add_argument("--input_address", help="Address for zero_record samples", default="tcp://127.0.0.1:10001")
    parser.add_argument("--output_address", help="Address for publishing JSON of noise indicators",
                        default="tcp://127.0.0.1:10005")
    args = parser.parse_args()
    print("Configuration: " + repr(args))
    if not os.path.exists(args.configuration_file):
        parser.print_help()
        print("File not found "+args.configuration_file)
    ai = AcousticIndicatorsProcessor(args)
    ai.run()

