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
import sys
import collections
import argparse
import time

try:
    from Crypto.Cipher import PKCS1_OAEP
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import AES
    from Crypto import Random
    from Crypto.Random import get_random_bytes
    import numpy
except ImportError:
    print("Please install PyCryptodome")
    print("pip install pycryptodome")
    print("Audio encryption has been disabled")

import soundfile as sf
import io
import datetime


class TriggerProcessor:
    """
    Service listening to zero_record and trigger sound recording according to pre-defined noise events
    """

    def __init__(self, config):
        self.config = config
        self.sample_rate = self.config["sample_rate"]
        format_byte_width = {"S16_LE": 2, "S32_LE": 4, "FLOAT_LE": 4, "S24_3LE": 3, "S24_LE": 4}
        sample_length = format_byte_width[self.config["sample_format"]]
        self.bytes_per_seconds = self.sample_rate * sample_length
        self.samples_stack = None
        self.remaining_samples = 0
        self.remaining_triggers = 10
        self.last_fetch_trigger_info = 0
        self.epoch = datetime.datetime.utcfromtimestamp(0)
        # Prepare for collecting samples

        # Cache samples for configured length before trigger
        self.samples_stack = collections.deque(maxlen=math.ceil(
            (self.bytes_per_seconds * (self.config["cached_length"] + 1)) / (self.bytes_per_seconds * 0.125)))
        if self.push_data_samples not in self.data["callback_samples"]:
            self.data["callback_samples"].append(self.push_data_samples)
        if self.push_data_fast not in self.data["callback_fast"]:
            self.data["callback_fast"].append(self.push_data_fast)

    def push_data_samples(self, samples):
        stack = self.samples_stack
        if stack is not None:
            stack.append(samples)

    def push_data_fast(self, line):
        self.fast.append(line)

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
            if sys.version_info.major == 2:
                audio_data = audio_data.ljust(len(audio_data) + AES.block_size - len(audio_data) % AES.block_size,
                                              str('\0'))
            else:
                audio_data = audio_data.ljust(len(audio_data) + AES.block_size - len(audio_data) % AES.block_size,
                                              b'\0')
        # Write AES data
        output_encrypted.write(aes_cipher.encrypt(audio_data))
        return output_encrypted.getvalue()

    def run(self):
        trigger_sha = str("")
        status = "wait_trigger"
        start_processing = self.unix_time()
        trigger_time = 0
        samples_trigger = io.BytesIO()
        last_day_of_year = datetime.datetime.now().timetuple().tm_yday
        while self.data["running"]:
            if last_day_of_year != datetime.datetime.now().timetuple().tm_yday and "trigger_count" in self.config:
                # reset trigger counter each day
                print("Reset trigger counter")
                last_day_of_year = datetime.datetime.now().timetuple().tm_yday
                self.remaining_triggers = self.config["trigger_count"]
            if self.config is not None and status == "wait_trigger":
                cur_time = time.time() * 1000
                if cur_time > self.config["date_end"]:
                    # Do not cache samples anymore
                    if self.push_data_samples in self.data["callback_samples"]:
                        self.data["callback_samples"].remove(self.push_data_samples)
                    if self.push_data_fast in self.data["callback_fast"]:
                        self.data["callback_fast"].remove(self.push_data_fast)
                    self.fast.clear()
                    self.samples_stack = None
                elif self.remaining_triggers > 0 and cur_time > self.config["date_start"] and self.check_hour():
                    # Time condition ok
                    # now check audio condition
                    while len(self.fast) > 0 and status == "wait_trigger":
                        try:
                            spectrum = self.fast.popleft()

                            laeq = spectrum[2]
                            print(sum([len(s) for s in self.samples_stack]))
                            if self.data["debug"] or laeq >= self.config["min_leq"]:
                                # leq condition ok
                                # check for sound recognition tags
                                # status = "record"
                                # self.remaining_samples = int(self.bytes_per_seconds * self.config["total_length"])
                                # print("Start %.3f recording cosine:%.3f expecting %d samples" % (spectrum[0],
                                # cosine_similarity, self.remaining_samples))
                                # self.remaining_triggers -= 1
                                # trigger_time = spectrum[0]
                                # break
                                pass

                        except IndexError:
                            pass
            elif status == "record":
                while status == "record" and self.samples_stack is not None and len(self.samples_stack) > 0:
                    samples = self.samples_stack.popleft()
                    size = min(self.remaining_samples, len(samples))
                    samples_trigger.write(samples[:size])
                    self.remaining_samples -= size
                    if self.remaining_samples == 0:
                        status = "wait_trigger"
                        audio_processing_start = time.clock()
                        # Compress audio samples
                        output = io.BytesIO()
                        data, samplerate = sf.read(samples_trigger, format='RAW',
                                                   channels=1 if self.data['mono'] else 2,
                                                   samplerate=int(self.sample_rate),
                                                   subtype=['PCM_16', 'PCM_32'][
                                                       ['S16_LE', 'S32_LE'].index(self.data["sample_format"])])
                        data = data[:, 0]
                        channels = 1
                        with sf.SoundFile(output, 'w', samplerate, channels, format='OGG') as f:
                            f.write(data)
                            f.flush()
                        audio_data_encrypt = self.encrypt(output.getvalue())
                        print("raw %d array %d bytes b64 ogg: %d bytes in %.3f seconds" % (
                            samples_trigger.tell(), data.shape[0], len(base64.b64encode(audio_data_encrypt)),
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This program read audio stream from zeromq and publish noise events',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--date_start", help="activate noise event detector from this epoch", default=0)
    parser.add_argument("--date_end", help="activate noise event detector up to this epoch", default=4106967057000)
    parser.add_argument("--trigger_count", help="limit the number of triggers by this count", default=10)
    parser.add_argument("--min_laeq", help="minimum laeq to trigger an event", default=30)
    parser.add_argument("--min_leq", help="minimum leq to trigger an event", default=30)
    parser.add_argument("--total_length", help="record length total in seconds", default=10)
    parser.add_argument("--cached_length", help="record length before the trigger", default=5)
    parser.add_argument("--sample_rate", help="audio sample rate", default=48000)
    parser.add_argument("--sample_format", help="audio format", default="FLOAT_LE")
    parser.add_argument("--ssh_file", help="public key file for audio encryption", default="~/.ssh/id_rsa.pub")
    trigger = TriggerProcessor(parser.parse_args())
    trigger.run()
