FROM python:3
EXPOSE 10001/tcp
EXPOSE 10002/tcp

#RUN apt install build-essential
WORKDIR /usr/src/app

RUN pip install --upgrade pip

RUN pip instal

COPY ../.. .

RUN pip install .

RUN curl https://storage.googleapis.com/audioset/yamnet.h5 -o third_parties/yamnet/yamnet.h5

RUN cd third_parties

RUN pip install .

CMD [ "python", "./src/zero_trigger.py" ]
