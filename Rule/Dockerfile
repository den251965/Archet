FROM python:latest
# доставляем библиотеки питона
RUN python -m pip install --upgrade pip && \
    pip install psycopg2 paho-mqtt prometheus-flask-exporter reddis

ADD rule_engine.py /Rule/
WORKDIR /Rule/
