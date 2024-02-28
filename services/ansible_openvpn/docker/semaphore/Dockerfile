# syntax=docker/dockerfile:1.3-labs
FROM semaphoreui/semaphore:latest

USER root

RUN <<EOF
apk add rsync py3-pip
mkdir /home/semaphore/data
chown -R semaphore:root /home/semaphore/
chown -R semaphore:root /home/semaphore/dashboard_website
EOF

USER 1001

