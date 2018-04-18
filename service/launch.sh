arecord -D hw:2,0 -f S16_LE -r 32000 -c 2 -t wav | sox -t wav - -b 16 -t raw --channels 1 - | python -u noisesensor.py -p8080
