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
    # For Python 3.0 and later
    from http.server import HTTPServer
    from http.server import BaseHTTPRequestHandler
    from http import HTTPStatus
except ImportError:
    # Fall back to Python 2's urllib2
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

try:
    # For Python 3.0 and later
    from urllib.request import urlopen
    from urllib.error import URLError
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen, URLError

import noisepy
import getopt
import sys
import threading
import datetime
import collections
import time
import json
import ssl
import math
import numpy
import io
import base64

try:
    from Crypto.Cipher import PKCS1_OAEP
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import AES
    from Crypto import Random
    from Crypto.Random import get_random_bytes
except ImportError:
    print("Please install PyCrypto")
    print("pip install pycrypto")

import soundfile as sf



## Usage ex
# arecord -D hw:1 -r 48000 -f S32_LE -c2 -t raw | python -u noisesensor.py -c 2 -f S32_LE -r 48000 -p 8090

__version__ = "1.1.1-dev"

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
        db_delta = 123.34
        ref_sound_pressure = 1 / 10 ** (db_delta / 20.)
        np = noisepy.noisepy(False, True, ref_sound_pressure, True, self.data["rate"], self.data["sample_format"], self.data["mono"])
        npa = noisepy.noisepy(True, False, ref_sound_pressure, True, self.data["rate"], self.data["sample_format"], self.data["mono"])
        np.set_tukey_alpha(0.2)
        npa.set_tukey_alpha(0.2)
        start = 0
        total_bytes_read = 0
        bytes_per_seconds = [32000.0, 48000.0][self.data["rate"]] * [2, 4][["S16_LE", "S32_LE"].index(self.data["sample_format"])] * (1 if self.data["mono"] else 2)
        try:
            while True:
                audiosamples = sys.stdin.read(np.max_samples_length())
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
                        leqSpectrum = map(np.get_leq_band_fast, range(len(freqs)))
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


class TriggerProcessor(threading.Thread):
    def __init__(self, data):
        threading.Thread.__init__(self)
        self.data = data
        self.config = {}
        self.fast = collections.deque(maxlen=data['row_cache_fast'])
        self.sample_rate = [32000.0, 48000.0][self.data["rate"]]
        self.bytes_per_seconds = self.sample_rate * [2, 4][["S16_LE", "S32_LE"].index(self.data["sample_format"])] * (1 if self.data["mono"] else 2)
        self.samples_stack = None
        self.remaining_samples = 0
        self.remaining_triggers = 0
        self.last_fetch_trigger_info = 0
        self.epoch = datetime.datetime.utcfromtimestamp(0)

    def push_data_samples(self, samples):
        stack = self.samples_stack
        if stack is not None:
            stack.append(samples)

    def push_data_fast(self, line):
        self.fast.append(line)

    # from scipy
    def _validate_weights(self,w, dtype=numpy.double):
        w = self._validate_vector(w, dtype=dtype)
        if numpy.any(w < 0):
            raise ValueError("Input weights should be all non-negative")
        return w

    # from scipy
    def _validate_vector(self,u, dtype=None):
        # XXX Is order='c' really necessary?
        u = numpy.asarray(u, dtype=dtype, order='c').squeeze()
        # Ensure values such as u=1 and u=[1] still return 1-D arrays.
        u = numpy.atleast_1d(u)
        if u.ndim > 1:
            raise ValueError("Input vector should be 1-D.")
        return u

    # from scipy
    def dist_cosine(self,u, v, w=None):
        u = self._validate_vector(u)
        v = self._validate_vector(v)
        if w is not None:
            w = self._validate_weights(w)
        uv = numpy.average(u * v, weights=w)
        uu = numpy.average(numpy.square(u), weights=w)
        vv = numpy.average(numpy.square(v), weights=w)
        dist = 1.0 - uv / numpy.sqrt(uu * vv)
        return dist

    def check_hour(self):
        t = datetime.datetime.now()
        if "start_hour" not in self.config:
            return True
        h, m = map(int, self.config["start_hour"].split(":"))
        start_ok = False
        if t.hour > h or (t.hour == h and t.minute >= m):
            start_ok = True
        end_ok = False
        if "end_hour" not in self.config:
            end_ok = True
        else:
            h, m = map(int, self.config["end_hour"].split(":"))
            if t.hour < h or (t.hour == h and t.minute < m):
                end_ok = True
        return start_ok and end_ok

    def encrypt(self, audio_data):
        output_encrypted = io.BytesIO()

        # Open public key to encrypt AES key
        key = RSA.importKey(self.config["file"])
        cipher = PKCS1_OAEP.new(key)

        aes_key = get_random_bytes(AES.block_size)
        iv = Random.new().read(AES.block_size)

        # Write OAEP header
        output_encrypted.write(cipher.encrypt(aes_key + iv))

        aes_cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        # pad audio data
        if len(audio_data) % AES.block_size > 0:
            audio_data = audio_data.ljust(len(audio_data) + AES.block_size - len(audio_data) % AES.block_size, '\0')
        # Write AES data
        output_encrypted.write(aes_cipher.encrypt(audio_data))
        return output_encrypted.getvalue()

    def run(self):
        status = "wait_trigger"
        start_processing = self.unix_time()
        trigger_time = 0
        samples_trigger = io.BytesIO()
        while self.data["running"]:
            if ("spectrum" not in self.config or self.data["debug"] or datetime.datetime.now().hour >= 23)\
                    and time.time() - self.last_fetch_trigger_info >= 2 * 3600.0:
                # Fetch trigger information
                try:
                    print("Download trigger information")
                    res = urlopen("https://dashboard.raw.noise-planet.org/get-trigger",
                                  context=ssl._create_unverified_context() if self.data["debug"] else None)
                    self.config = json.loads(res.read())
                    self.remaining_triggers = self.config["trigger_count"]
                    if time.time() * 1000 < self.config["date_end"]:
                        # Cache samples for configured length before trigger
                        self.samples_stack = collections.deque(maxlen=math.ceil((self.bytes_per_seconds * (self.config["cached_length"] + 1)) / (self.bytes_per_seconds * 0.125)))
                        if self.push_data_samples not in self.data["callback_samples"]:
                            self.data["callback_samples"].append(self.push_data_samples)
                        if self.push_data_fast not in self.data["callback_fast"]:
                            self.data["callback_fast"].append(self.push_data_fast)
                    self.last_fetch_trigger_info = time.time()
                except [URLError, ValueError, KeyError] as e:
                    # ignore
                    print(self.config)
                    print(e)
                    time.sleep(60)
            elif self.config is not None and status == "wait_trigger":
                cur_time = time.time() * 1000
                if cur_time > self.config["date_end"] or self.remaining_triggers == 0:
                    # Do not cache samples anymore
                    self.data["callback_samples"].remove(self.push_data_samples)
                    self.data["callback_fast"].remove(self.push_data_fast)
                    self.fast.clear()
                    self.samples_stack = None
                elif self.remaining_triggers > 0 and cur_time > self.config["date_start"] and self.check_hour():
                    # Time condition ok
                    # now check audio condition
                    while len(self.fast) > 0:
                        try:
                            spectrum = self.fast.popleft()
                            laeq = spectrum[2]
                            if self.data["debug"] or laeq >= self.config["min_leq"]:
                                # leq condition ok
                                # check for spectrum condition
                                cosine_similarity = 1 - self.dist_cosine(spectrum[3:], self.config["spectrum"], w=self.config["weight"])
                                if self.data["debug"]:
                                    if int(spectrum[0] - start_processing) == 15:
                                        cosine_similarity = 1
                                    else:
                                        cosine_similarity = 0
                                if cosine_similarity > self.config["cosine"] / 100.0:
                                    status = "record"
                                    self.remaining_samples = int(self.bytes_per_seconds * self.config["total_length"])
                                    print("Start %.3f recording cosine:%.3f expecting %d samples" % (spectrum[0], cosine_similarity, self.remaining_samples))
                                    self.remaining_triggers -= 1
                                    trigger_time = spectrum[0]
                                    break

                        except IndexError:
                            pass
            elif status == "record":
                while status == "record" and len(self.samples_stack) > 0:
                    samples = self.samples_stack.popleft()
                    size = min(self.remaining_samples, len(samples))
                    samples_trigger.write(samples[:size])
                    self.remaining_samples -= size
                    if self.remaining_samples == 0:
                        status = "wait_trigger"
                        audio_processing_start = time.clock()
                        # Compress audio samples
                        output = io.BytesIO()
                        data, samplerate = sf.read(samples_trigger, format='RAW', channels=1 if self.data['mono'] else 2, samplerate=int(self.sample_rate),
                                                   subtype=['PCM_16', 'PCM_32'][['S16_LE', 'S32_LE'].index(self.data["sample_format"])])
                        data = data[:, 0]
                        channels = 1
                        with sf.SoundFile(output, 'w', samplerate, channels, format='OGG') as f:
                            f.write(data)
                            f.flush()
                        audio_data_encrypt = self.encrypt(output.getvalue())
                        print("raw %d array %d bytes b64 ogg: %d bytes in %.3f seconds" % (
                        samples_trigger.tell(),data.shape[0], len(base64.b64encode(audio_data_encrypt)),
                        time.clock() - audio_processing_start))
                        samples_trigger = io.BytesIO()
                        info = sf.info(io.BytesIO(output.getvalue()))
                        print("duration %.2f s, remaining triggers %d" % (info.duration, self.remaining_triggers))
                        for f in self.data["callback_encrypted_audio"]:
                            f(trigger_time, audio_data_encrypt)
                        self.samples_stack.clear()
                        time.sleep(self.config["cached_length"])
                        self.fast.clear()
            time.sleep(0.125)

    def unix_time(self):
        return (datetime.datetime.utcnow() - self.epoch).total_seconds()

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

def usage():
    print(
        "This program read audio stream from std input and compute acoustics parameters.")
    print(
        "ex: arecord -D hw:2,0 -f S32_LE -r 32000 -c 2 -t raw | python -u noisesensor.py -f S32_LE -r 32000 -c 2 -p 8080")
    print("Usage:")
    print(" -p:\t Serve as http on specified port (Optional)")
    print(" -f:\t Sample format")
    print(" -r:\t Sample rate in Hz")
    print(" -c:\t Number of channels")


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
    data = {'running':True, 'debug':False, 'leq': [], "callback_fast": [], "callback_slow": [], "callback_samples": [], "row_cache_fast": 60 * 8, "row_cache_slow": 60,
            "format_fast" : b'%.3f,%.2f,%.2f,' + ",".join(["%.2f"]*len(freqs))+b'\n', "format_slow": b'%d,%.2f,%.2f\n', "callback_encrypted_audio": []}
    # parse command line options
    port = 0
    try:
        for opt, value in getopt.getopt(sys.argv[1:], "p:f:r:c:d:")[0]:
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
    except getopt.error as msg:
        usage()
        exit(-1)

    if data["debug"]:
        sys.stdin = open(data["debug_file"], 'rb')

    # run audio processing thread
    processing_thread = AcousticIndicatorsProcessor(data)
    processing_thread.start()

    # run trigger processing thread
    trigger_thread = TriggerProcessor(data)
    trigger_thread.start()

    # Http server
    if port > 0:
        httpserver = HttpServer(data, port=port)
        httpserver.start()

    # End program when audio processing end
    try:
        processing_thread.join()
    finally:
        data["running"] = False

if __name__ == "__main__":
    main()
