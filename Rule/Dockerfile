FROM python:latest
# доставляем библиотеки питона
RUN python -m pip install --upgrade pip && \
    pip install psycopg2 paho-mqtt prometheus-flask-exporter redis

ADD rule_engine.py /Rule/
WORKDIR /Rule/
