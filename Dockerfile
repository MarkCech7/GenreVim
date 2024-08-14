FROM python:3.11-slim AS builder

RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y ffmpeg
RUN apt-get install -y sqlite3

WORKDIR /app

COPY requirements.txt /app
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

COPY . /app

RUN cp patches/cipher.py /usr/local/lib/python3.11/site-packages/pytube

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]