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
    from http.server import HTTPServer
    from http.server import BaseHTTPRequestHandler
    from http import HTTPStatus
except ImportError:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

import noisepy
import getopt
import sys
import threading

## Usage
# This script expect signed 16 bits mono audio on stdin
# arecord -D hw:2,0 -f S16_LE -r 32000 -c 2 -t wav | sox -t wav - -b 16 -t raw --channels 1 - | python -u noisesensor.py


__version__ = "1.0.0-dev"

class AcousticIndicatorsHttpServe(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'Hello, Python!')
        return

class AcousticIndicatorsProcessor(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data

    def run(self):
        np = noisepy.noisepy(False, False, 32767.)
        while True:
            audiosamples = sys.stdin.read(np.max_samples_length() * 2)
            if not audiosamples:
                break
            if np.push(audiosamples, len(audiosamples) / 2) == noisepy.feed_complete:
                self.data["leq"].append(np.get_leq_slow())
                print("Leq %.2f" % np.get_leq_slow())



def run(server_class=HTTPServer, handler_class=AcousticIndicatorsHttpServe, port=8000):
    server_address = ('localhost', port)
    httpd = server_class(server_address, handler_class)
    try:
        print("Server works on http://localhost:%d" % port)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Stop the server on http://localhost:%d" % port)
        httpd.socket.close()

def usage():
    print("This program read audio stream from std input and compute acoustics parameters. This script expect signed 16 bits mono audio on stdin")
    print("ex: arecord -D hw:2,0 -f S16_LE -r 32000 -c 2 -t wav | sox -t wav - -b 16 -t raw --channels 1 - | python -u noisesensor.py")
    print("Usage:")
    print(" -p:\t Serve as http on specified port (Optional)")

def main():
    # Shared data between process
    data = {'leq' : []}
    # parse command line options
    port = 0
    try:
        for opt, value in getopt.getopt(sys.argv[1:], "p")[0]:
            if opt == "-p":
                port = value
    except getopt.error as msg:
        usage()
        exit(-1)
    # run processing thread
    processing_thread = AcousticIndicatorsProcessor(data)
    processing_thread.start()

    if port > 0:
        run(port=port)

if __name__ == "__main__":
    main()
