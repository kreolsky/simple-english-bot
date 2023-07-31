FROM python:3.9-slim

RUN groupadd -r uwsgi && \
    useradd -r -g uwsgi uwsgi && \
    mkdir -p /home/bot &&  \
    mkdir -p /home/config

ADD ./etc/python/ /home/config/
WORKDIR /home/bot

RUN apt-get update && \
    apt-get install -y gcc ssh && \
    pip install --no-cache-dir -r /home/config/requirements.txt

CMD [ "uwsgi", "--ini", "/home/config/uwsgi.ini", "--http", "0.0.0.0:80" ]
