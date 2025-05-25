import json
from datetime import datetime
import threading
import paho.mqtt.client as mqtt
import socket

from flask import Flask, request, jsonify
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Gauge, Counter

app = Flask(__name__)
CORS(app)
PrometheusMetrics(app)

fl = ""

port = 30880
port_mqtt = 1883
publisher_client = mqtt.Client()

def Connect_brocker():
    # publisher_client.connect("localhost", port_mqtt, keepalive=120)
    publisher_client.connect("nanomq", port_mqtt, keepalive=120)

# def Log(mess):   
#     timestamp = datetime.now().isoformat() # Получаем текущий timestamp в ISO 8601 формате   
#     # Формируем лог в виде словаря
#     log_entry = {
#         "timestamp": timestamp,
#         "level": "INFO",
#         "message": mess
#     }
#     with open(fl, "a", encoding='utf-8') as f:
#        f.write(json.dumps(log_entry, ensure_ascii = False) + "\n")

# LOGSTASH_HOST = '127.0.0.1'  # IP Logstash
LOGSTASH_HOST = 'logstash'  # IP Logstash
LOGSTASH_PORT = 5044        # порт, указанный в конфигурации

def Log(mess):
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "level": "INFO",
        "message": mess
    }
    log_json = json.dumps(log_entry, ensure_ascii=False)

    try:
        with socket.create_connection((LOGSTASH_HOST, LOGSTASH_PORT)) as sock:
            sock.sendall((log_json + "\n").encode('utf-8'))
    except Exception as e:
        print(f"Ошибка при отправке лога: {e}")

# Создаем переменную для хранения таймера
timer = None

def start_timer():
    global timer
    # Если таймер уже есть, отменяем его перед созданием нового
    if timer is not None:
        timer.cancel()
    # Создаем новый таймер
    timer = threading.Timer(120, Connect_brocker)
    timer.start()

# Сервак
# Формируем данные
def jsoncreat(errore):
    if (errore == 0) :
        st = {'status': 'ok'}
    else :
        st = {'status': 'err'}
    return st

@app.route('/', methods=['GET'])
def get():
    return jsoncreat(0)

@app.route('/', methods=['POST'])
def post():
    global timer
    # Перезапускаем таймер
    start_timer()
    data = request.get_json()
    # print(f"Loading of server inserting:\t{data}")
    t = data['siteid']
    if (t == -1) :
        # print(f"Loading of server inserting:\t{data}")
        Log(data)
        return jsoncreat(1)
    device_id = data.get('device_id')
    # print(f"{device_id}")
    publisher_client.publish(f"{device_id}", json.dumps(data))
    return jsoncreat(0)

if __name__ == '__main__':
    now = datetime.now()
    fl = "server_" + now.strftime("%Y_%m_%d")
    start_timer()
    Connect_brocker()
    app.run(host = "0.0.0.0", threaded = True, port = port, debug = False)
