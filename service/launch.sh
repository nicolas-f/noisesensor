arecord --disable-softvol -D hw:CARD=U18dB,DEV=0 -r 48000 -f S24_3LE -c 2 -t raw | python3 -u noisesensor.py -c 2 -f S24_3LE -r 48000
