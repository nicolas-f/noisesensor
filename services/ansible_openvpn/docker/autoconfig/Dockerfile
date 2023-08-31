FROM python:3.9

WORKDIR /usr/app/

COPY ./requirements.txt /usr/app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /usr/app/requirements.txt

COPY ./src /usr/app/

CMD ["python3", "/usr/app/src/main.py"]
