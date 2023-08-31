# syntax=docker/dockerfile:1.3-labs
FROM semaphoreui/semaphore:latest

USER root

RUN <<EOF
apk add rsync py3-pip
mkdir /home/semaphore/data
mkdir /home/semaphore/authorized_keys
chown -R semaphore:root /home/semaphore/
EOF

USER 1001

