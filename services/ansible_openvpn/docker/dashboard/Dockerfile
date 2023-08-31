FROM python:3.9

RUN useradd -ms /bin/bash dashboard

WORKDIR /home/dashboard

COPY ./requirements.txt /home/dashboard/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /home/dashboard/requirements.txt

COPY ./app /home/dashboard/app

USER dashboard

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
