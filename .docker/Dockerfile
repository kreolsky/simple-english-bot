FROM python:3-slim

RUN groupadd -r uwsgi && \
    useradd -r -g uwsgi uwsgi && \
    mkdir -p /home/bot &&  \
    mkdir -p /home/config

ADD ./config/ /home/config/
WORKDIR /home/bot

RUN apt-get update && \
    apt-get install -y gcc ssh && \
    pip install -r /home/config/requirements.txt

CMD [ "uwsgi", "--ini", "/home/config/uwsgi.ini", "--http", "0.0.0.0:80" ]
