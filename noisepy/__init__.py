from .wrapped import noisepy

feed_window_overflow = -1
feed_idle = 0
feed_complete = 1
feed_fast = 2

ai_sample_rate_32000 = 0
ai_sample_rate_48000 = 1

ai_format_s16_le = 0
ai_format_s32_le = 1
ai_format_float_le = 2
ai_format_s24_3le = 3
ai_format_s24_le = 4

ai_formats = [b"S16_LE", b"S32_LE", b"FLOAT_LE", b"S24_3LE", b"S24_LE"]
