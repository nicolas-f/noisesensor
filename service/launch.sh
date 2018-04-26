#!/bin/bash

#set the signal to enable the power supply of the MIC
enable_audio ()
{
  echo "24" > /sys/class/gpio/export
  echo "out" > /sys/class/gpio/gpio24/direction
  echo "1" > /sys/class/gpio/gpio24/value
}

#set the signal to disable the power supply of the MIC
disable_audio ()
{
  echo "0" > /sys/class/gpio/gpio24/value
  echo "24" > /sys/class/gpio/unexport 
}

#when the script die (sudo service anr_record stop) this function is called
on_die()
{
  # print message
  #
  disable_audio

  exit 0
}



trap 'on_die' TERM
enable_audio
sleep 1

echo "Waiting for microphone startup.."
while :
do
  # Compute statistics, maxlvl should be != than -Inf
  maxlvl=$(arecord -D hw:1 -d 1 -r 32000 -f S32_LE -c2 -t wav | sox -twav - -n channels 1 stats 2>&1  | grep "Pk lev dB" | sed 's/[^0-9.-]*//g')
  if [ ! -z "$maxlvl" ]
  then
    break
  fi
done

# Display statistics
arecord -D hw:1 -d 1 -r 32000 -f S32_LE -c2 -t wav | sox -twav - -n channels 1 stats 2>&1

echo "Microphone ready"

while :
do
  arecord -D hw:1 -r 32000 -f S32_LE -c2 -t wav | /usr/bin/sox -t wav - -b 16 -e signed-integer -L -t raw -c 1 - | /home/anr_br/noisesensor/bin/python -u noisesensor.py -f/home/anr_br/noisesensor/ftpconfig.json
  # Audio stream issue, relaunch
  echo "program terminated, relaunch"
  sleep 1
done
disable_audio
