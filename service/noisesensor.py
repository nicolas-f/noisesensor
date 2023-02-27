#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
BSD 3-Clause License

Copyright (c) 2018, Ifsttar Wi6labs LS2N
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

from __future__ import print_function, division, unicode_literals

from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import noisepy
import getopt
import sys
import os
import pathlib
import threading
import datetime
import collections
import time
import base64

## Usage ex for Umik-1 on ubuntu
# arecord --disable-softvol -D hw:1 -r 48000 -f S24_3LE -c 2 -t raw | python3 -u noisesensor.py -c 2 -f S24_3LE -r 48000

__version__ = "1.2.0-dev"

freqs = [20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500]


class AcousticIndicatorsProcessor(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data
        self.epoch = datetime.datetime.utcfromtimestamp(0)

    def push_data_fast(self, line):
        for fun in self.data["callback_fast"]:
            fun(line)

    def push_data_slow(self, line):
        for fun in self.data["callback_slow"]:
            fun(line)

    def push_samples(self, samples):
        for fun in self.data["callback_samples"]:
            fun(samples)

    def unix_time(self):
        return (datetime.datetime.utcnow() - self.epoch).total_seconds()

    def run(self):
        db_delta = 94 + 28.34  # sensitivity of my Umik-1 is -28.34 dBFS @ 94 dB/1khz
        ref_sound_pressure = 1 / 10 ** (db_delta / 20.)
        np = noisepy.noisepy(False, True, ref_sound_pressure, True, self.data["rate"],
                             self.data["sample_format"].encode('UTF-8'), self.data["mono"])
        npa = noisepy.noisepy(True, False, ref_sound_pressure, True, self.data["rate"],
                              self.data["sample_format"].encode('UTF-8'), self.data["mono"])
        print(repr(np.myfunc()))
        np.set_tukey_alpha(0.2)
        npa.set_tukey_alpha(0.2)
        start = 0
        total_bytes_read = 0
        bytes_per_seconds = [32000.0, 48000.0][self.data["rate"]] * [2, 4, 4, 3, 4][["S16_LE", "S32_LE", "FLOAT_LE",
                                                                                     "S24_3LE", "S24_LE"].index(
            self.data["sample_format"])] * (1 if self.data["mono"] else 2)
        try:
            input_stream = None
            if self.data["debug"]:
                input_stream = open(self.data["debug_file"], 'rb')
            else:
                if sys.version_info.major == 2:
                    input_stream = sys.stdin
                else:
                    input_stream = sys.stdin.buffer

            while True:
                audiosamples = input_stream.read(np.max_samples_length())
                if not audiosamples:
                    print("%s End of audio samples, duration %.3f seconds" % (datetime.datetime.now().isoformat(),
                                                                              total_bytes_read / bytes_per_seconds))
                    break
                else:
                    total_bytes_read += len(audiosamples)
                    self.push_samples(audiosamples)
                    if self.data["debug"]:
                        # Pause stream before gathering more samples
                        cur = time.time()
                        samples_time = len(audiosamples) / bytes_per_seconds
                        if cur - start < samples_time:
                            time.sleep(samples_time - (cur - start))
                        start = time.time()
                    resp = np.push(audiosamples, len(audiosamples))
                    leq125ms = 0
                    laeq125ms = 0
                    leq1s = 0
                    laeq1s = 0
                    leqSpectrum = []
                    push_fast = False
                    push_slow = False
                    # time can be in iso format using datetime.datetime.now().isoformat()
                    if resp == noisepy.feed_complete or resp == noisepy.feed_fast:
                        leq125ms = np.get_leq_fast()
                        leqSpectrum = list(map(np.get_leq_band_fast, range(len(freqs))))
                        push_fast = True
                        if resp == noisepy.feed_complete:
                            leq1s = np.get_leq_slow()
                            push_slow = True
                    resp = npa.push(audiosamples, len(audiosamples))
                    if resp == noisepy.feed_complete or resp == noisepy.feed_fast:
                        laeq125ms = npa.get_leq_fast()
                        push_fast = True
                        if resp == noisepy.feed_complete:
                            laeq1s = npa.get_leq_slow()
                            push_slow = True
                    if push_fast:
                        self.push_data_fast([self.unix_time(), leq125ms, laeq125ms] + leqSpectrum)
                    if push_slow:
                        self.push_data_slow([self.unix_time(), leq1s, laeq1s])
        finally:
            self.data["running"] = False


class AcousticIndicatorsServer(HTTPServer):
    def __init__(self, data, *args, **kwargs):
        # Because HTTPServer is an old-style class, super() can't be used.
        HTTPServer.__init__(self, *args, **kwargs)
        self.daemon = True
        self.data = data
        self.fast = collections.deque(maxlen=data['row_cache_fast'])
        self.slow = collections.deque(maxlen=data['row_cache_slow'])
        self.samples = collections.deque()
        self.data["callback_fast"].append(self.push_data_fast)
        self.data["callback_slow"].append(self.push_data_slow)
        self.data["callback_encrypted_audio"].append(self.push_samples)

    def push_data_fast(self, line):
        self.fast.append(line)

    def push_data_slow(self, line):
        self.slow.append(line)

    def push_samples(self, t, samples):
        self.samples.append("%s,%s\n" % (t, base64.b64encode(samples)))


class AcousticIndicatorsHttpServe(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain;charset=UTF-8')
        self.end_headers()
        if self.path.startswith("/fast"):
            while len(self.server.fast) > 0:
                self.wfile.write(self.server.data["format_fast"] % tuple(self.server.fast.popleft()))
        elif self.path.startswith("/samples"):
            while len(self.server.samples) > 0:
                self.wfile.write(self.server.samples.popleft())
        else:
            while len(self.server.slow) > 0:
                self.wfile.write(self.server.data["format_slow"] % tuple(self.server.slow.popleft()))
        return

    def log_message(self, format, *args):
        if self.server.data["debug"]:
            sys.stderr.write("%s - - [%s] %s\n" %
                             (self.client_address[0],
                              self.log_date_time_string(),
                              format%args))
        return


# Push results to ftp folder
class HttpServer(threading.Thread):
    def __init__(self, data, server_class=AcousticIndicatorsServer, handler_class=AcousticIndicatorsHttpServe, port=8000):
        threading.Thread.__init__(self)
        self.port = port
        self.daemon = True
        server_address = ('0.0.0.0', port)
        self.httpd = server_class(data, server_address, handler_class)

    def run(self):
        try:
            print("Server works on http://localhost:%d" % self.port)
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            print("Stop the server on http://localhost:%d" % self.port)
            self.httpd.socket.close()


def build_csv_path(folder, epoch):
    return os.path.join(folder, datetime.datetime.utcfromtimestamp(epoch).strftime("%Y_%m_%d.csv"))


class CsvWriter(threading.Thread):
    """
    Handle the writing of CSV files in the provided folder(s)
    """
    def __init__(self, data, csv_files):
        threading.Thread.__init__(self)
        self.data = data
        self.csv_temp_files = [None] * len(csv_files)
        self.csv_files = csv_files
        self.fast = collections.deque(maxlen=data['row_cache_fast'])
        self.data["callback_fast"].append(self.push_data_fast)

    def push_data_fast(self, line):
        self.fast.append(line)

    def run(self):
        while self.data["running"]:
            # rows_to_write will contains all rows to write that belong to the same UTC day
            rows_to_write = []
            epoch = None
            while len(self.fast) > 0:
                new_epoch = self.fast[0][0]
                if len(rows_to_write) > 0:
                    # break if we change to a new day (in UTC)
                    if datetime.datetime.utcfromtimestamp(epoch).day != \
                            datetime.datetime.utcfromtimestamp(new_epoch).day:
                        break
                else:
                    epoch = new_epoch
                rows_to_write.append(self.data["format_fast"] % tuple(self.fast.popleft()))
            if len(rows_to_write) > 0:
                for file_index, file_folder in enumerate(self.csv_files):
                    file_path = build_csv_path(file_folder, epoch) + ".tmp"
                    write_header = False
                    if not os.path.exists(file_path):
                        parent_folder = pathlib.Path(file_path).parent
                        if not os.path.exists(parent_folder):
                            os.mkdir(parent_folder)
                        # file does not exists so we will write the header first
                        write_header = True
                    with open(file_path, 'ab') as file_object:
                        if write_header:
                            file_object.write(bytes("epoch,leq,laeq," + ",".join(map(str, freqs)) + "\n", encoding='UTF-8'))
                            if self.csv_temp_files[file_index] is not None:
                                # remove .tmp extension of completed file
                                os.rename(self.csv_temp_files[file_index], self.csv_temp_files[file_index][:-len(".tmp")])
                            self.csv_temp_files[file_index] = file_path
                        for row in rows_to_write:
                            file_object.write(row)
            time.sleep(10)
        for file_index, file_folder in enumerate(self.csv_files):
            if self.csv_temp_files[file_index] is not None:
                # remove .tmp extension of completed file
                os.rename(self.csv_temp_files[file_index], self.csv_temp_files[file_index][:-len(".tmp")])




def usage():
    print(
        "This program read audio stream from std input and compute acoustics parameters.")
    print(
        "ex: arecord -D hw:2,0 -f S32_LE -r 32000 -c 2 -t raw | python -u noisesensor.py -f S32_LE -r 32000 -c 2 -p 8080")
    print("Usage:")
    print(" -p:\t Serve as http on specified port (Optional) http://localhost:port/fast")
    print(" -f:\t Sample format")
    print(" -r:\t Sample rate in Hz")
    print(" -c:\t Number of channels")
    print(" -o:\t Folder that will contain csv files (can be repeated for multiple copies)")


##
# FTP Configuration file example
# {
#    "protocol": "ftp",
#    "host": "192.168.1.1",
#    "folder" : "",
#    "port": 21,
#    "user": "user",
#    "pass": "password",
#    "timeout": 10000,
#    "filePermissions":"0644"
# }
def main():
    # Shared data between process
    data = {'running': True, 'debug': False, 'leq': [], "callback_fast": [], "callback_slow": [],
            "callback_samples": [], "row_cache_fast": 60 * 8, "row_cache_slow": 60,
            "format_fast": b'%.3f,%.2f,%.2f,' + b",".join([b"%.2f"] * len(freqs)) + b'\n',
            "format_slow": b'%d,%.2f,%.2f\n', "callback_encrypted_audio": []}
    # parse command line options
    port = 0
    outputs_csv = []
    try:
        for opt, value in getopt.getopt(sys.argv[1:], "p:f:r:c:d:o:")[0]:
            if opt == "-p":
                port = int(value)
            elif opt == "-r":
                rates = ["32000", "48000"]
                data["rate"] = rates.index(value)
            elif opt == "-f":
                data["sample_format"] = value
            elif opt == "-c":
                data["mono"] = value == "1"
            elif opt == "-d":
                data["debug"] = True
                data["debug_file"] = value
            elif opt == "-o":
                outputs_csv.append(value)
    except getopt.error as msg:
        usage()
        exit(-1)

    # run audio processing thread
    processing_thread = AcousticIndicatorsProcessor(data)
    processing_thread.start()

    # run trigger processing thread
    if "sf" in globals() and "yamnet" in globals() and "resampy" in globals():
        print("Starting sound source recognition thread..")
        trigger_thread = TriggerProcessor(data)
        trigger_thread.start()

    # Http server
    if port > 0:
        httpserver = HttpServer(data, port=port)
        httpserver.start()

    if len(outputs_csv) > 0:
        csv_writer = CsvWriter(data, outputs_csv)
        csv_writer.start()

    # End program when audio processing end
    try:
        processing_thread.join()
    finally:
        data["running"] = False

if __name__ == "__main__":
    main()
