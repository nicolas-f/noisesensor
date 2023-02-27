arecord --disable-softvol -D plughw:CARD=U18dB,DEV=0 -r 48000 -f FLOAT_LE -c 1 -t raw | python3 -u noisesensor.py -c 1 -f FLOAT_LE -r 48000 -p 8090
