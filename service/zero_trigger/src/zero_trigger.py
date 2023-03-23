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
import os.path
import collections
import argparse
import threading
import time
import array
import math
import csv

import numpy as np
from scipy import signal
try:
    import zmq
except ImportError as e:
    print("Please install pyzmq")
    print("pip install pyzmq")
    print("Audio capture has been disabled")
    raise e

try:
    from Crypto.Cipher import PKCS1_OAEP
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import AES
    from Crypto import Random
    from Crypto.Random import get_random_bytes
    import base64
except ImportError:
    print("Please install PyCryptodome, base64 and numpy")
    print("pip install pycryptodome")
    print("Audio encryption has been disabled")

import soundfile as sf
import io
import datetime
from yamnet import yamnet, params
import resampy
from importlib.resources import files


def encrypt(audio_data, ssh_file):
    """
    Encrypt the provided string using the provided ssh public key
    :param audio_data: Audio data in bytes
    :param ssh_file: Path of the public key
    :return: Encrypted data
    """
    output_encrypted = io.BytesIO()

    # Open public key to encrypt AES key
    key = RSA.importKey(open(ssh_file).read())
    cipher = PKCS1_OAEP.new(key)

    aes_key = get_random_bytes(AES.block_size)
    iv = Random.new().read(AES.block_size)

    # Write OAEP header
    output_encrypted.write(cipher.encrypt(aes_key + iv))

    aes_cipher = AES.new(aes_key, AES.MODE_CBC, iv)
    # pad audio data
    if len(audio_data) % AES.block_size > 0:
        audio_data = audio_data.ljust(len(audio_data) + AES.block_size - len(audio_data) % AES.block_size, b'\0')
    # Write AES data
    output_encrypted.write(aes_cipher.encrypt(audio_data))
    return output_encrypted.getvalue()


class StatusThread(threading.Thread):
    def __init__(self, trigger_processor, config):
        threading.Thread.__init__(self)
        self.trigger_processor = trigger_processor
        self.config = config

    def run(self):
        while self.config.running:
            record_time = str(datetime.timedelta(seconds=
                                                 round(self.trigger_processor.total_read / self.config.sample_rate)))
            print("%s samples read: %ld (%s)" % (datetime.datetime.now().replace(microsecond=0).isoformat(),
                                                 self.trigger_processor.total_read, record_time))
            time.sleep(self.config.delay_print_samples)


def read_yamnet_class_and_threshold(class_map_csv):
    with open(class_map_csv) as csv_file:
        reader = csv.reader(csv_file)
        next(reader)  # Skip header
        names, threshold = zip(*[[display_name.strip(), float(threshold)] for _, _, display_name, threshold in reader])
        return names, np.array(threshold, dtype=float)


class TriggerProcessor:
    """
    Service listening to zero_record and trigger sound recording according to pre-defined noise events
    """

    def __init__(self, config):
        self.config = config
        self.total_read = 0  # Total audio samples read
        self.sample_rate = self.config.sample_rate
        format_byte_width = {"S16_LE": 2, "S32_LE": 4, "FLOAT_LE": 4, "S24_3LE": 3, "S24_LE": 4}
        sample_length = format_byte_width[self.config.sample_format]
        self.bytes_per_seconds = self.sample_rate * sample_length
        self.remaining_samples = 0
        self.remaining_triggers = self.config.trigger_count
        self.last_fetch_trigger_info = 0
        self.epoch = datetime.datetime.utcfromtimestamp(0)
        # Cache samples for configured length before trigger
        self.samples_stack = collections.deque()
        self.socket = None
        self.socket_out = None
        self.yamnet_config = params.Params()
        self.yamnet = yamnet.yamnet_frames_model(self.yamnet_config)
        yamnet_weights = self.config.yamnet_weights
        if yamnet_weights is None:
            yamnet_weights = files('yamnet').joinpath('yamnet.h5')
        self.yamnet.load_weights(yamnet_weights)
        yamnet_class_map = self.config.yamnet_class_map
        if yamnet_class_map is None:
            yamnet_class_map = files('yamnet').joinpath('yamnet_class_threshold_map.csv')
        self.yamnet_classes = read_yamnet_class_and_threshold(yamnet_class_map)
        self.sos = self.butter_highpass(self.config.yamnet_cutoff_frequency,
                                        self.yamnet_config.sample_rate)

    def butter_highpass(self, cutoff, fs, order=4):
        return signal.butter(order, cutoff / (fs / 2.0), btype='high', output='sos')

    def butter_highpass_filter(self, waveform):
        return signal.sosfilt(self.sos, waveform)

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

    def init_socket(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect(self.config.input_address)
        self.socket.subscribe("")
        self.socket_out = context.socket(zmq.PUB)
        self.socket_out.bind(self.config.output_address)

    def process_tags(self, samples_to_process: int):
        # check for sound recognition tags
        waveform = np.zeros((int(self.yamnet_config.patch_window_seconds * self.config.sample_rate)),
                            dtype=np.float32)
        total_samples = sum([len(s) for s in self.samples_stack])
        first_index = max(0, total_samples - samples_to_process)
        # copy from older samples to newer samples (using only the last samples_to_process of the stack)
        cursor = 0
        for samples in self.samples_stack:
            if cursor + len(samples) <= first_index:
                # We have already processed those samples (not marked as to process)
                cursor += len(samples)
                continue
            if cursor < first_index:
                # only some samples from this array have to be processed
                samples_slice = samples[first_index - cursor:]
                waveform[0:len(samples_slice)] = samples_slice
                cursor += len(samples_slice)
            else:
                copy_from = cursor - first_index
                copy_to = min(len(samples), first_index + len(waveform) - cursor)
                if copy_to > 0:
                    waveform[copy_from:copy_from + copy_to] = samples[:copy_to]
                    cursor += copy_to
                else:
                    break
        # resample if necessary
        if self.config.sample_rate != self.yamnet_config.sample_rate:
            waveform = resampy.resample(waveform, self.config.sample_rate, self.yamnet_config.sample_rate)
        # filter and normalize signal
        if self.config.yamnet_cutoff_frequency > 0:
            waveform = self.butter_highpass_filter(waveform)
        if self.config.yamnet_max_gain > 0:
            # apply gain
            max_value = max(1e-12, float(np.max(np.abs(waveform))))
            gain = 10 * math.log10(1 / max_value)
            gain = min(self.config.yamnet_max_gain, gain)
            waveform *= 10 ** (gain / 10.0)
        # Predict YAMNet classes.
        scores, embeddings, spectrogram = self.yamnet(waveform)
        return scores, embeddings, spectrogram

    def fetch_audio_data(self, feed_cache=True):
        if feed_cache:
            if self.samples_stack is None:
                self.samples_stack = collections.deque()
        audio_data_bytes = array.array('f', self.socket.recv())
        self.total_read += len(audio_data_bytes)
        if feed_cache:
            self.samples_stack.append(audio_data_bytes)
            # will keep keep_only_samples samples, and drop older stack elements
            keep_only_samples = max(self.config.cached_length, self.yamnet_config.patch_window_seconds) * \
                                self.config.sample_rate
            while sum([len(s) for s in self.samples_stack]) > keep_only_samples + len(audio_data_bytes):
                self.samples_stack.popleft()
        return audio_data_bytes

    def run(self):
        trigger_sha = str("")
        status = "wait_trigger"
        start_processing = self.unix_time()
        trigger_time = 0
        last_day_of_year = datetime.datetime.now().timetuple().tm_yday
        self.init_socket()
        document = {}
        while True:
            if last_day_of_year != datetime.datetime.now().timetuple().tm_yday and "trigger_count" in self.config:
                # reset trigger counter each day
                print("Reset trigger counter")
                last_day_of_year = datetime.datetime.now().timetuple().tm_yday
                self.remaining_triggers = self.config.trigger_count
            if self.config is not None and status == "wait_trigger":
                cur_time = time.time() * 1000
                if cur_time > self.config.date_end:
                    # Do not cache samples anymore
                    self.samples_stack = collections.deque()
                elif self.remaining_triggers > 0 and cur_time > self.config.date_start and self.check_hour():
                    # Time condition ok
                    # now check audio condition
                    unprocessed_samples = 0
                    while status == "wait_trigger":
                        # fetch next packet
                        audio_data_bytes = self.fetch_audio_data()
                        unprocessed_samples += len(audio_data_bytes)
                        if unprocessed_samples / self.config.sample_rate >= self.config.yamnet_leq_interval:
                            # compute leq
                            reference_pressure = 1 / 10 ** ((94 - self.config.sensitivity) / 20.0)
                            sum_samples = 1e-12
                            processed_samples = 0
                            samples_to_process = int(self.config.yamnet_leq_interval * self.config.sample_rate)
                            # retrieve the last samples_to_process samples to a numpy array
                            for samples in reversed(self.samples_stack):
                                if processed_samples >= samples_to_process:
                                    break
                                waveform = samples
                                if len(waveform) + processed_samples > samples_to_process:
                                    window = len(waveform) - (samples_to_process - processed_samples)
                                    waveform = waveform[window:]
                                processed_samples += len(waveform)
                                sum_samples += np.sum(np.power(np.array(waveform) / reference_pressure, 2.0))
                            leq = 10 * math.log10(sum_samples / processed_samples)
                            if leq >= self.config.min_leq:
                                print("Leq: %.2f dB > %.2f dB, so now try to recognize sound source "
                                      % (leq, self.config.min_leq))
                                status = "sound_event_detection"
                                break
            if status == "sound_event_detection":
                # Samples pushed to samples_stack but not processed in sound recognition algorithm
                unprocessed_samples = sum([len(s) for s in self.samples_stack])
                remaining_window_count = self.config.yamnet_sound_event_windows
                all_scores = None
                total_process_time = 0
                total_processed_samples = 0
                while status == "sound_event_detection":
                    while unprocessed_samples / self.config.sample_rate >= self.yamnet_config.patch_window_seconds:
                        # leq condition ok
                        deb_process = time.time()
                        scores, embeddings, spectrogram = self.process_tags(unprocessed_samples)
                        unprocessed_samples -= int(self.yamnet_config.patch_window_seconds * self.config.sample_rate)
                        total_processed_samples += int(
                            self.yamnet_config.patch_window_seconds * self.config.sample_rate)
                        if all_scores is None:
                            all_scores = scores
                        else:
                            all_scores = np.concatenate((all_scores, scores))
                        total_process_time += time.time() - deb_process
                        remaining_window_count -= 1
                        if remaining_window_count <= 0:
                            # Scores is a matrix of (time_frames, num_classes) classifier scores.
                            # Average them along with time to get an overall classifier output for the clip.
                            prediction = np.max(all_scores, axis=0)
                            # filter out classes that are below threshold values
                            classes_threshold_index = list(map(int, (prediction > self.yamnet_classes[1]).nonzero()[0]))
                            if len(classes_threshold_index) == 0:
                                # classifier rejected all known classes
                                print("No classes found above yamnet threshold")
                                status = "wait_trigger"
                                break
                            # Sort by score
                            classes_threshold_index = [classes_threshold_index[j] for j in
                                       np.argsort([prediction[i]-self.yamnet_classes[1][i]
                                                   for i in classes_threshold_index])[::-1]]
                            # Compute a score between 0-100% from threshold to 1.0
                            scores = {self.yamnet_classes[0][i]:
                                      round(float(((prediction[i]-self.yamnet_classes[1][i]) /
                                            (1-self.yamnet_classes[1][i])) * 100)) for i in classes_threshold_index}
                            document = {"scores": scores,
                                        "spectrogram": [[round(v, 3) for v in band] for band in
                                                        spectrogram.numpy().tolist()],
                                        "leq": round(leq, 2), "epoch_millisecond": int(cur_time)}
                            tags = ' '.join('{:s}({:d}%)'.format(k, v)
                                            for k,v in scores.items())
                            self.remaining_triggers -= 1
                            print("%s tags:%s processed in %.3f seconds for %.1f seconds of audio."
                                  " Remaining triggers for today %d" % (time.strftime("%Y-%m-%d %H:%M:%S"),
                                                                        tags, total_process_time,
                                                                        total_processed_samples /
                                                                        self.config.sample_rate,
                                                                        self.remaining_triggers))
                            status = "record"
                            break
                    # fetch next packet
                    audio_data_bytes = self.fetch_audio_data()
                    unprocessed_samples += len(audio_data_bytes)
            elif status == "record":
                while status == "record":
                    audio_data_encrypt = ""
                    ssh_file = os.path.expanduser(self.config.ssh_file)
                    if "AES" in globals() and os.path.exists(ssh_file):
                        # empty audio cache
                        samples_trigger = io.BytesIO()
                        remaining_samples = int(self.config.total_length * self.config.sample_rate)
                        while len(self.samples_stack) > 0:
                            audio_samples = self.samples_stack.popleft()
                            remaining_samples -= len(audio_samples)
                            samples_trigger.write(audio_samples)
                        # read audio samples until remaining_samples reached
                        while remaining_samples > 0:
                            audio_samples = self.fetch_audio_data(False)
                            remaining_samples -= len(audio_samples)
                            samples_trigger.write(audio_samples)
                        audio_processing_start = time.time()
                        # Compress audio samples
                        output = io.BytesIO()
                        data, samplerate = sf.read(samples_trigger, format='RAW',
                                                   channels=1 if self.config.mono else 2,
                                                   samplerate=int(self.config.sample_rate),
                                                   subtype=['PCM_16', 'PCM_32', 'PCM_32'][
                                                       ['S16_LE', 'S32_LE', 'FLOAT_LE']
                                                   .index(self.config.sample_format)])
                        channels = 1
                        with sf.SoundFile(output, 'w', samplerate, channels, format='OGG') as f:
                            f.write(data)
                            f.flush()
                        audio_data_encrypt = base64.b64encode(encrypt(output.getvalue(), ssh_file)).decode("UTF-8")
                        print("raw %d array %d bytes b64 ogg: %d bytes in %.3f seconds" % (
                            samples_trigger.tell(), data.shape[0], len(audio_data_encrypt),
                            time.time() - audio_processing_start))
                        info = sf.info(io.BytesIO(output.getvalue()))
                        print("Audio duration %.2f s, remaining triggers %d" % (info.duration, self.remaining_triggers))
                    document["encrypted_audio"] = audio_data_encrypt
                    self.socket_out.send_json(document)
                    self.samples_stack.clear()
                    status = "wait_trigger"
            time.sleep(0.125)

    def unix_time(self):
        return (datetime.datetime.utcnow() - self.epoch).total_seconds()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This program read audio stream from zeromq and publish noise events',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--date_start", help="activate noise event detector from this epoch", default=0, type=int)
    parser.add_argument("--date_end", help="activate noise event detector up to this epoch", default=4106967057000,
                        type=int)
    parser.add_argument("--trigger_count", help="limit the number of triggers by this count", default=10, type=int)
    parser.add_argument("--min_leq", help="minimum leq to trigger an event", default=30, type=float)
    parser.add_argument("--total_length", help="record length total in seconds", default=10, type=float)
    parser.add_argument("--cached_length", help="record length before the trigger", default=5, type=float)
    parser.add_argument("--sample_rate", help="audio sample rate", default=48000, type=int)
    parser.add_argument("--sample_format", help="audio format", default="FLOAT_LE")
    parser.add_argument("--ssh_file", help="public key file for audio encryption", default="~/.ssh/id_rsa.pub")
    parser.add_argument("--input_address", help="Address for zero_record samples", default="tcp://127.0.0.1:10001")
    parser.add_argument("--output_address", help="Address for publishing JSON of sound recognition",
                        default="tcp://*:10002")
    parser.add_argument("--yamnet_class_map", help="Yamnet HDF5 class csv file path", default=None)
    parser.add_argument("--yamnet_weights", help="Yamnet HDF5 weight file path", default=None)
    parser.add_argument("--yamnet_cutoff_frequency", help="Yamnet highpass filter frequency", default=100, type=float)
    parser.add_argument("--yamnet_max_gain", help="Yamnet maximum gain in dB", default=20.0, type=float)
    parser.add_argument("--yamnet_sound_event_windows", help="Number of windows to recognise sound source", default=10,
                        type=int)
    parser.add_argument("--yamnet_leq_interval", help="Leq period for triggering scan of audio source", default=1.0,
                        type=float)
    parser.add_argument("--sensitivity", help="Microphone sensitivity in dBFS at 94 dB 1 kHz", default=-28.34,
                        type=float)
    parser.add_argument("--mono", help="Mono audio", default=True,
                        type=bool)
    parser.add_argument("--delay_print_samples", help="Delay in second between each print of number of samples read",
                        default=0, type=float)
    args = parser.parse_args()
    print("Configuration: " + repr(args))
    trigger = TriggerProcessor(args)
    args.running = True
    status_thread = StatusThread(trigger, args)
    if args.delay_print_samples > 0:
        # run stats thread
        status_thread.start()
    try:
        trigger.run()
    finally:
        args.running = False
