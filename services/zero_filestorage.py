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

import argparse
import gzip
import time
import zmq
import os
import threading
import collections
import datetime
import json
import itertools
import fcntl
import socket
import struct
import signal

def get_hw_address(interface_name):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack(
        '256s', bytes(interface_name, 'utf-8')[:15]))
    return ''.join('%02x' % b for b in info[18:24])


class ZeroMQThread(threading.Thread):
    def __init__(self, global_settings, name, address):
        threading.Thread.__init__(self)
        self.global_settings = global_settings
        self.name = name
        self.address = address

    def run(self):
        context = zmq.Context()
        zmq_socket = context.socket(zmq.SUB)
        print("Looking for json content in " + self.address)
        zmq_socket.connect(self.address)
        zmq_socket.subscribe("")
        hwa = ""
        if self.global_settings.insert_hwa:
            hwa = get_hw_address(self.global_settings.insert_hwa)
        while self.global_settings.running:
            try:
                json_data = zmq_socket.recv_json(flags=zmq.NOBLOCK)
                if hwa:
                    json_data["hwa"] = hwa
                self.global_settings.documents_stack.append([self.name,
                                                             json_data])
            except zmq.ZMQError as e:
                time.sleep(0.05)


def open_file_for_write(filename, configuration):
    if configuration.compress:
        return gzip.open(filename, 'at')
    else:
        return open(filename, 'a')


# Close and rename files when filestorage service is closed
def stop(sig, frame, args):
    print("Clean closing of temporary files")
    args.running = False


def rename_file(temporary_extension, file_path, extension):
    final_name = file_path + extension
    cpt = 2
    while os.path.exists(final_name):
        final_name = file_path + "_%d" % cpt + extension
        cpt += 1
    os.rename(temporary_extension, final_name)

def main():
    parser = argparse.ArgumentParser(
        description='This program read json documents on zeromq channels'
                    ' and write in the specified folder', formatter_class=
        argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input_address", nargs="+", action='append',
                        help="Address and file name for zero_record json"
                             " channel, you can provide it multiple times. "
                             "ex: tcp://127.0.0.1:10005/indicators",
                        required=True, type=str)
    parser.add_argument("-o", "--output_folder", help="Json output folder",
                        required=True, type=str)
    parser.add_argument("-t", "--time_format",
                        help="Time format name for the file,"
                             " if the file already exists the json"
                             " will be added as a new line",
                        default="%Y_%m_%d.%Hh%Mm%S.%f",
                        type=str)
    parser.add_argument("-r", "--row_count",
                        help="Maximum row count for stacked json in one file",
                        default=1,  type=int)
    parser.add_argument("-c", "--compress",
                        help="Compress output files", default=False,
                        action="store_true")
    parser.add_argument("--insert_hwa",
                        help="Insert hardware address of the specified"
                             " interface as a new field 'hwa'", default="")
    args = parser.parse_args()
    print("Configuration: " + repr(args))

    args.documents_stack = collections.deque()
    args.running = True
    extension = ".json"
    if args.compress:
        extension = ".json.gz"
        import gzip
    try:
        for input_data in itertools.chain.from_iterable(args.input_address):
            t_sep = input_data.rfind("/")
            t_name = input_data[t_sep+1:]
            t_address = input_data[:t_sep]
            t = ZeroMQThread(args, t_name, t_address)
            t.start()
        document_tracker = {}
        signal.signal(signal.SIGTERM,
                      lambda sig, frame: stop(sig, frame, args))
        signal.signal(signal.SIGINT,
                      lambda sig, frame: stop(sig, frame, args))
        while args.running:
            while len(args.documents_stack) > 0:
                document_name, document_json = args.documents_stack.popleft()
                time_part = datetime.datetime.now().\
                    strftime(args.time_format)
                file_path = os.path.join(args.output_folder,
                                         document_name+"_%s" % time_part)
                # append to document if it has been tracked
                if document_name not in document_tracker:
                    document_tracker[document_name] = [1, file_path]
                else:
                    document_tracker[document_name][0] += 1
                    file_path = document_tracker[document_name][1]
                # make tmp extension in order to not process this file
                # until it has been fully saved
                temporary_extension = file_path+extension+".tmp"
                exists = os.path.exists(temporary_extension)
                if not os.path.exists(args.output_folder):
                    print("Try to create parent folder " + args.output_folder)
                    os.mkdir(args.output_folder)
                with open_file_for_write(temporary_extension, args) as fp:
                    if exists:
                        fp.write("\n")
                    json.dump(document_json, fp, allow_nan=True)
                # rename to the final name if document file is complete
                if args.row_count <= document_tracker[document_name][0]:
                    rename_file(temporary_extension, file_path, extension)
                    del(document_tracker[document_name])
            time.sleep(0.005)
        # close/rename remaining files
        for document_name, document_data in document_tracker.items():
            file_path = document_data[1]
            temporary_extension = file_path + extension + ".tmp"
            print("Rename incomplete file " + temporary_extension)
            rename_file(temporary_extension, file_path, extension)
    finally:
        args.running = False


if __name__ == "__main__":
    main()
