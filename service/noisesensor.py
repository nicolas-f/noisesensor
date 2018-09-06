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

from __future__ import print_function

try:
    from http.server import HTTPServer, BaseHTTPServer
    from http.server import BaseHTTPRequestHandler
    from http import HTTPStatus
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

import noisepy
import getopt
import sys
import os
import threading
import struct
import time
import datetime
import StringIO
import json
import ftplib
import uuid
import collections

## Usage
# This script expect signed 16 bits mono audio on stdin
# arecord -D hw:2,0 -f S16_LE -r 32000 -c 2 -t wav | sox -t wav - -b 16 -t raw --channels 1 - | python -u noisesensor.py
ftp_sleep = 0.02

__version__ = "1.0.0-dev"

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

    def unix_time(self):
        return (datetime.datetime.utcnow() - self.epoch).total_seconds()

    def run(self):
        db_delta = 94-51.96
        ref_sound_pressure = 1 / 10 ** (db_delta / 20.)
        np = noisepy.noisepy(False, True, ref_sound_pressure, True)
        npa = noisepy.noisepy(True, False, ref_sound_pressure, True)
        np.set_tukey_alpha(0.2)
        npa.set_tukey_alpha(0.2)
        short_size = struct.calcsize('h')
        while True:
            audiosamples = sys.stdin.read(np.max_samples_length() * short_size)
            if not audiosamples:
                print("%s End of audio samples" % datetime.datetime.now().isoformat())
                break
            else:
                resp = np.push(audiosamples, len(audiosamples) / short_size)
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
                    leqSpectrum = map(np.get_leq_band_fast, range(len(freqs)))
                    push_fast = True
                    if resp == noisepy.feed_complete:
                        leq1s = np.get_leq_slow()
                        push_slow = True
                resp = npa.push(audiosamples, len(audiosamples) / short_size)
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


class AcousticIndicatorsServer(HTTPServer):
    def __init__(self, data, *args, **kwargs):
        # Because HTTPServer is an old-style class, super() can't be used.
        HTTPServer.__init__(self, *args, **kwargs)
        self.daemon = True
        self.data = data
        self.fast = collections.deque(maxlen=data['row_cache_fast'])
        self.slow = collections.deque(maxlen=data['row_cache_slow'])
        self.data["callback_fast"].append(self.push_data_fast)
        self.data["callback_slow"].append(self.push_data_slow)

    def push_data_fast(self, line):
        self.fast.append(line)

    def push_data_slow(self, line):
        self.slow.append(line)

class AcousticIndicatorsHttpServe(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain;charset=UTF-8')
        self.end_headers()
        if self.path.startswith("/fast"):
            while len(self.server.fast) > 0:
                self.wfile.write(self.server.data["format_fast"] % tuple(self.server.fast.popleft()))
        else:
            while len(self.server.slow) > 0:
                self.wfile.write(self.server.data["format_slow"] % tuple(self.server.slow.popleft()))
        return


# Push results to ftp folder
class FtpPush(threading.Thread):
    def __init__(self, data, config, prepend, leq_max_history, leq_refresh_history, write_format, header):
        threading.Thread.__init__(self)
        self.daemon = True
        self.data = data
        self.config = config
        self.csv_cache = collections.deque()
        self.prepend = prepend
        self.leq_max_history = leq_max_history
        self.leq_refresh_history = leq_refresh_history
        self.write_format = write_format
        self.header = header

    def on_new_record(self, line):
        self.csv_cache.append(line)

    def generate_filename(self):
        mac_adress = '-'.join(("%012X" % uuid.getnode())[i:i + 2] for i in range(0, 12, 2))
        date_iso = datetime.datetime.now().isoformat().replace(":", "-")
        return self.prepend + mac_adress + "_" + date_iso + ".csv"

    def connect_ftp(self):
        ftp = ftplib.FTP(timeout=self.config["timeout"])
        ftp.connect(self.config["host"], self.config["port"], self.config["timeout"])
        ftp.login(self.config["user"], self.config["pass"])
        if len(self.config["folder"]) > 0:
            ftp.cwd(self.config["folder"])
        return ftp

    def run(self):
        ftp_retries = 10
        ftp = self.connect_ftp()
        # main loop
        while True:
            filename = self.generate_filename()
            pushed_lines = 0
            pushed_bytes = 0
            while pushed_lines < self.leq_max_history:
                while len(self.csv_cache) < self.leq_refresh_history:
                    time.sleep(ftp_sleep)
                stringbuffer = StringIO.StringIO()
                if pushed_lines == 0:
                    stringbuffer.write(self.header+"\n")
                for i in range(self.leq_refresh_history):
                    stringbuffer.write(self.write_format % tuple(self.csv_cache.popleft()))
                pushed_lines += self.leq_refresh_history
                while True:
                    try:
                        stringbuffer.seek(0)
                        ftp.storbinary('STOR ' + filename, stringbuffer, rest=pushed_bytes)
                        ftp_retries = 10
                        break
                    except ftplib.error_perm as err:
                        if ftp_retries > 0:
                            ftp_retries -= 1
                            print("Error while transferring file, retry\n", err)
                            time.sleep(5)
                            ftp = self.connect_ftp()
                        else:
                            print("No retry left, ftp sent canceled\n", err)
                            return

                pushed_bytes += stringbuffer.tell()


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

def usage():
    print(
        "This program read audio stream from std input and compute acoustics parameters. This script expect signed 16 bits mono audio on stdin")
    print(
        "ex: arecord -D hw:2,0 -f S16_LE -r 32000 -c 2 -t wav | sox -t wav - -b 16 -t raw --channels 1 - | python -u noisesensor.py")
    print("Usage:")
    print(" -p:\t Serve as http on specified port (Optional)")
    print(" -f:\t Transfer data to files on ftp server, specify configuration file  (Optional)")


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
    data = {'leq': [], "callback_fast": [], "callback_slow": [], "row_cache_fast": 60 * 8, "row_cache_slow": 60,
            "format_fast" : b'%.3f,%.2f,%.2f,' + ",".join(["%.2f"]*len(freqs))+b'\n', "format_slow": b'%d,%.2f,%.2f\n' }
    ftpconfig = ""
    # parse command line options
    port = 0
    try:
        for opt, value in getopt.getopt(sys.argv[1:], "p:f:")[0]:
            if opt == "-p":
                port = int(value)
            elif opt == "-f":
                ftpconfig = value
    except getopt.error as msg:
        usage()
        exit(-1)
    # run audio processing thread
    processing_thread = AcousticIndicatorsProcessor(data)
    processing_thread.start()

    # ftp push threads
    if len(ftpconfig) > 0 and os.path.isfile(ftpconfig):
        config = json.load(open(ftpconfig))
        # Create a new file when reaching this time length
        leq_max_history = 30 * 60
        # push data to FTP when this number of seconds is cached
        leq_refresh_history = 30
        csv_header = "epoch,leq,laeq,"+",".join(map(lambda f: "%.1fHz" % f, freqs))
        ftp_thread_fast = FtpPush(data, config, "fast_", leq_max_history * 8, leq_refresh_history * 8, data["format_fast"], csv_header)
        data["callback_fast"].append(ftp_thread_fast.on_new_record)
        ftp_thread_fast.start()
        ftp_thread_slow = FtpPush(data, config, "slow_", leq_max_history, leq_refresh_history, data["format_slow"],
                                  "epoch,leq,laeq")
        data["callback_slow"].append(ftp_thread_slow.on_new_record)
        ftp_thread_slow.start()

    # Http server
    if port > 0:
        httpserver = HttpServer(data, port=port)
        httpserver.start()

    # End program when audio processing end
    processing_thread.join()


if __name__ == "__main__":
    main()
