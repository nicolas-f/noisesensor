from noisesensor.filterdesign import FilterDesign
import json


f = FilterDesign(sample_rate=48000, first_frequency_band=50,
                 last_frequency_band=16000, window_samples=48000*0.125)
f.down_sampling = f.G2
f.band_division = 3

configuration = f.generate_configuration()

json.dump(configuration, fp=open("config_48000_third_octave.json", "w"),
          sort_keys=False, indent=4)

