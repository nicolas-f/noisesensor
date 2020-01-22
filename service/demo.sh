arecord -D hw:2,0 -r 48000 -f S16_LE -c2 -t raw | python -u noisesensor.py -c 2 -f S16_LE -r 48000 -p 8090

