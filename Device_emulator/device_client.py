import random
import datetime
from time import sleep
import sqlite3
import requests
import threading

# HOST = "192.168.1.123"  # адрес сервера
HOST = "localhost"  # адрес сервера
PORT = 30880
http_adr = f"http://{HOST}:{PORT}"
time_sleepers = 3 # время между сообщениями
device_count = 300  # число устройств

gps_db_emultor = "D:\\ITMO\\ArchitectureVP\\Architectured\\Device_emulator\\emulator_data.db"

ways = dict()
gnsss = dict()
keygen_loader = []

def ConnectorDB():
    connection = sqlite3.connect(gps_db_emultor)
    cur = connection.cursor()
    cur.execute("SELECT WAY_ID, SITEID, UPNOM, PUTNOM, NAME, GUID, LAT, LON FROM GNSS a INNER JOIN WAY_DATA b on a.WAY_ID = b.ID ORDER BY WAY_ID")
    rows = cur.fetchall()
    cur.close()
    connection.close()
    return rows

def Load_Data(rows):
    ids = -100
    for WAY_ID, SITEID, UPNOM, PUTNOM, NAME, GUID, LAT, LON in rows:
        if ids != WAY_ID:
            way = [WAY_ID, SITEID, UPNOM, PUTNOM, NAME, GUID]
            ways[WAY_ID] = way
            gnsss[WAY_ID] = []
            keygen_loader.append(WAY_ID)
            ids = WAY_ID
        gnss = [LAT, LON]
        gnsss[WAY_ID].append(gnss)

class ClientThread(threading.Thread):
    def __init__(self, id_way_start, id_start_gps, device_id):
        super().__init__()
        self.id_way_start = id_way_start
        self.id_start_gps = id_start_gps
        self.device_id = device_id
        self.running = True

    def run(self):
        id_post = 0
        # подготовка начальных данных
        data = {
            "device_id": self.device_id,
            "lon": gnsss[self.id_way_start][self.id_start_gps][1],
            "lat": gnsss[self.id_way_start][self.id_start_gps][0],
            "siteid": ways[self.id_way_start][1],
            "upnom": ways[self.id_way_start][2],
            "putnom": ways[self.id_way_start][3],
            "time": str(datetime.datetime.now())
        }

        while self.running:
            if id_post >= 100:
                self.id_start_gps += 1
                if self.id_start_gps >= len(gnsss[self.id_way_start]):
                    self.id_start_gps = 0
                # обновляем координаты
                data['lat'] = gnsss[self.id_way_start][self.id_start_gps][0]
                data['lon'] = gnsss[self.id_way_start][self.id_start_gps][1]
                id_post = 0

            data['time'] = str(datetime.datetime.now())

            try:
                response = requests.post(http_adr, json=data, timeout=5)
                if response.status_code != 200:
                    print(f"Device {self.device_id} Ошибка: статус {response.status_code} - {response.text}")
                # можно распарсить ответ, если есть необходимость
                # resp_json = response.json()
                # print(f"Device {self.device_id} ответ: {resp_json.get('status')}")
            except requests.exceptions.RequestException as e:
                print(f"Device {self.device_id} ошибка связи: {e}")
                # задержка при ошибке
                sleep(5)

            id_post += 1
            sleep(time_sleepers)  # задержка между отправками

if __name__ == '__main__':
    print("Загрузка данных эмулятора устройств")
    rows = ConnectorDB()
    Load_Data(rows)
    print("Запуск эмулятора устройств")

    threads = []

    for i in range(device_count):
        # выбираем случайный стартовый путь и точку
        id_way = random.randrange(0, len(keygen_loader))
        id_way_start = keygen_loader[id_way]
        id_start_gps = random.randrange(0, len(gnsss[id_way_start]))

        # создаем и запускаем поток
        t = ClientThread(id_way_start, id_start_gps, device_id = i + 1)
        t.start()
        threads.append(t)