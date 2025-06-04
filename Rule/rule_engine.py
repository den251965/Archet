import json
import collections
import paho.mqtt.client as mqtt
import psycopg2
from datetime import datetime
import socket
import redis

# Определяем структуру Point
Point = collections.namedtuple("Point", ["device_id", "siteid", "upnom", "putnom", "lon", "lat", "timest"])
id = 50 # кэшируем данные этого устройства
cash = redis.Redis(host='localhost', port=6379, db=0)

# Название таблицы
table = 'route'
port_mqtt = 1883

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

# Функция для подключения к базе данных
def ConnectorDB():
    # return psycopg2.connect('postgresql://postgres:cadri@localhost:5432/postgres')
    # return psycopg2.connect('postgresql://postgres:cadri@postgres_container:5432/postgres')
    # return psycopg2.connect('postgresql://postgres:cadri@postgres:5432/postgres')
    return psycopg2.connect('postgresql://postgres:cadri@postgres-primary:5432/postgres')

# Проверка и создание таблицы при необходимости
def isCreated_DB():
    conn = ConnectorDB()
    cur = conn.cursor()
    # Проверка существования таблицы
    cur.execute('SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s);', (table,))
    existtable = bool(cur.fetchone()[0])
    cur.close()
    conn.close()
    # print(f"Таблица существует: {existtable}")
    Log(f"Таблица существует: {existtable}")
    if not existtable:
        # print(f"Таблица '{table}' не найдена. Создаю таблицу...")
        Log(f"Таблица '{table}' не найдена. Создаю таблицу...")
        conn = ConnectorDB()
        cur = conn.cursor()
        cur.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {table} (
                id SERIAL PRIMARY KEY,
                DEVICE_ID VARCHAR(100),
                SITEID int,
                UPNOM VARCHAR(100),
                PUTNOM VARCHAR(100),
                LON DOUBLE PRECISION,
                LAT DOUBLE PRECISION,
                TIMESTP TIMESTAMP
            );
            '''
        )
        conn.commit()
        cur.close()
        conn.close()
        # print(f"Таблица '{table}' успешно создана.")
        Log(f"Таблица '{table}' успешно создана.")
    else:
        # print(f"Таблица '{table}' уже существует.")
        Log(f"Таблица '{table}' уже существует.")

# Вставка данных в БД
def Insert_DB(datapoints):
    print(f"Вставка данных в таблицу '{table}'")
    # Log(f"Вставка данных в таблицу '{table}'")
    conn = ConnectorDB()
    cur = conn.cursor()
    for point in datapoints:
        cur.execute(
            f"INSERT INTO {table} (DEVICE_ID, SITEID, UPNOM, PUTNOM, LON, LAT, TIMESTP) VALUES (%s, %s, %s, %s, %s, %s, %s);",
            (point)
        )
    conn.commit()
    cur.close()
    conn.close()

# Обработка входящих сообщений
def on_message(client, userdata, msg):
    try:
        payload_str = msg.payload.decode()
        jsn = json.loads(payload_str)
        # print(f"Получено сообщение с топика '{msg.topic}': {jsn}")
        Log(f"Получено сообщение с топика '{msg.topic}': {jsn}")

        # Проверка наличия всех необходимых ключей
        required_keys = ['device_id', 'siteid', 'upnom', 'putnom', 'lon', 'lat', 'time']
        if all(k in jsn for k in required_keys):
            temp = Point(
                device_id=jsn['device_id'],
                siteid=jsn['siteid'],
                upnom=jsn['upnom'],
                putnom=jsn['putnom'],
                lon=jsn['lon'],
                lat=jsn['lat'],
                timest=jsn['time']
            )
            # кэш по правилу
            if (jsn['device_id'] == id) :
                export_reddis(jsn)

            Insert_DB([temp])
        else:
            # print("Некоторые ключи отсутствуют в JSON")
            Log("Некоторые ключи отсутствуют в JSON")
    except json.JSONDecodeError as e:
        # print(f"Ошибка парсинга JSON: {e}")
        Log(f"Ошибка парсинга JSON: {e}")
    except Exception as e:
        # print(f"Общая ошибка: {e}")
        Log(f"Общая ошибка: {e}")

# Обработка соединения
def on_connect(client, userdata, flags, rc, properties=None):
    # print("Подключено с результатом кода " + str(rc))
    client.subscribe("#")
    # print("Подписка на топики выполнена: '#'")
    Log("Подписка на топики выполнена: '#'")

# Обработка в реддис
def export_reddis(jsn) :
    if (cash.ping()) :
        cash.set(jsn, json.dumps(jsn))
    else:
        print("Redis не доступен")


if __name__ == '__main__':
    now = datetime.now()
    fl = "rule_" + now.strftime("%Y_%m_%d")
    # Проверяем и создаем таблицу при запуске
    isCreated_DB()

    # Создаем MQTT клиента
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    # client.connect("localhost", port_mqtt, 60)
    client.connect("nanomq", port_mqtt, 60)
    client.loop_forever()