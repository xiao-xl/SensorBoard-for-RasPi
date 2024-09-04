#!/home/xxlxxl/MySensor/bin/python3

import time
import board
import os
import adafruit_dht
import sqlite3
from datetime import datetime, timedelta

os.system('pkill -f libgpiod')
# Initial the dht device, with data pin connected to:
dhtDevice = adafruit_dht.DHT22(board.D18)

# you can pass DHT22 use_pulseio=False if you wouldn't like to use pulseio.
# This may be necessary on a Linux single board computer like the Raspberry Pi,
# but it will not work in CircuitPython.
# dhtDevice = adafruit_dht.DHT22(board.D18, use_pulseio=False)


def insert_data(temperature,humidity):
    conn = sqlite3.connect('/home/xxlxxl/DockerConf/HomeAssistant/SensorDB/SingleSensor.db')
    cursor = conn.cursor()
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO dht22 (time, temperature, humidity)
        VALUES (?, ?, ?)
    ''', (current_time, temperature, humidity))
    
    delete_timeline = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        DELETE FROM dht22 WHERE time < ?
    ''', (delete_timeline,))
    
    conn.commit()
    conn.close()

while True:
    try:
        # Print the values to the serial port
        temperature_c = dhtDevice.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = dhtDevice.humidity
#         print(
#             "Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
#                 temperature_f, temperature_c, humidity
#             )
#         )
        insert_data(temperature_c, humidity)
        
    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
#         print(error.args[0])
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        raise error

    time.sleep(2.0)
