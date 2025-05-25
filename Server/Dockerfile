FROM python:latest
# доставляем библиотеки питона
RUN python -m pip install --upgrade pip && \
    pip install flask flask_cors paho-mqtt prometheus-flask-exporter

ADD server_rule.py /Server/
WORKDIR /Server/
