FROM python:3.10

WORKDIR /usr/src/app

COPY ./ .

RUN pip install --upgrade pip \
    && pip install resampy \
    && pip install soundfile \
    && curl -C - https://storage.googleapis.com/audioset/yamnet.h5 -o yamnet/yamnet.h5 \
    && pip install .

WORKDIR /usr/src/app/yamnet

CMD ["python", "inference.py", "../24968__wwwbonsonca__train_tgv_passing_06.wav" ]
