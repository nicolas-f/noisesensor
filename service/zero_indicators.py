import datetime
import noisepy
import sys
import argparse
import zmq

freqs = [20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500]

class AcousticIndicatorsProcessor:
    def __init__(self, config):
        self.config = config
        self.epoch = datetime.datetime.utcfromtimestamp(0)

    def init_socket(self):
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect(self.config.input_address)
        self.socket.subscribe("")
    def unix_time(self):
        return (datetime.datetime.utcnow() - self.epoch).total_seconds()

    def run(self):
        self.init_socket()
        db_delta = 94 + 28.34  # sensitivity of my Umik-1 is -28.34 dBFS @ 94 dB/1khz
        ref_sound_pressure = 1 / 10 ** (db_delta / 20.)
        sample_rate_index = [32000, 48000].index(int(self.config.sample_rate))
        np = noisepy.noisepy(False, True, ref_sound_pressure, True, sample_rate_index,
                             self.config.sample_format.encode('UTF-8'), True)
        npa = noisepy.noisepy(True, False, ref_sound_pressure, True, sample_rate_index,
                              self.config.sample_format.encode('UTF-8'), True)
        np.set_tukey_alpha(0.2)
        npa.set_tukey_alpha(0.2)
        total_bytes_read = 0
        bytes_per_seconds = self.config.sample_rate * [2, 4, 4, 3, 4][["S16_LE", "S32_LE", "FLOAT_LE",
                                                                                     "S24_3LE", "S24_LE"].index(
            self.config.sample_format)]

        while True:
            audio_bytes = self.socket.recv()
            if not audio_bytes:
                print("%s End of audio samples, duration %.3f seconds" % (datetime.datetime.now().isoformat(),
                                                                          total_bytes_read / bytes_per_seconds))
                break
            else:
                while len(audio_bytes) > 0:
                    audio_samples = audio_bytes[:min(len(audio_bytes), np.max_samples_length())]
                    audio_bytes = audio_bytes[len(audio_samples):]
                    total_bytes_read += len(audio_samples)
                    resp = np.push(audio_samples, len(audio_samples))
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
                    resp = npa.push(audio_samples, len(audio_samples))
                    if resp == noisepy.feed_complete or resp == noisepy.feed_fast:
                        laeq125ms = npa.get_leq_fast()
                        push_fast = True
                        if resp == noisepy.feed_complete:
                            laeq1s = npa.get_leq_slow()
                            push_slow = True
                    if push_slow:
                        print("Leq %.2f dB LAeq %.2f dB" % (leq1s, laeq1s))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This program read audio stream from zeromq and publish noise events',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--sample_rate", help="audio sample rate", default=48000, type=int)
    parser.add_argument("--sample_format", help="audio format", default="FLOAT_LE")
    parser.add_argument("--sensitivity", help="Microphone sensitivity in dBFS at 94 dB 1 kHz", default=-28.34, type=float)
    parser.add_argument("--input_address", help="Address for zero_record samples", default="tcp://127.0.0.1:10001")
    args = parser.parse_args()
    print("Configuration: " + repr(args))
    ai = AcousticIndicatorsProcessor(args)
    ai.run()

