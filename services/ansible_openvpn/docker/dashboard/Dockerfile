# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM panubo/sshd AS builder

WORKDIR /dashboard

RUN apk add --no-cache nano py3-pip

COPY . /dashboard

COPY flask_service.sh /etc/entrypoint.d/

RUN chmod +x /etc/entrypoint.d/flask_service.sh \
    --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt


