#!/usr/bin/python3

import time
from datetime import datetime, timedelta
import smbus
import RPi.GPIO as GPIO
import numpy as np
from scipy.signal import find_peaks, butter, filtfilt
import sqlite3
import matplotlib.pyplot as plt

DHT20_ADDRESS = 0x38
AGS10_ADDRESS = 0x1A
BH1750FVI_ADDRESS = 0x23 # ADDR_HIGH 0x5C
BMP581_ADDRESS = 0x46 # SDO_HIGH 0x47
MPU6500_ADDRESS = 0x68 # SDO_HIGH 0x69 ?
MAX30102_ADDRESS = 0x57

BH1750FVI_ADDR_PIN = 29
BH1750FVI_DVI_PIN = 31
BMP581_SDO_PIN = 33
BMP581_INT_PIN = 35
MPU6500_SDO_PIN = 7
MPU6500_INT_PIN = 11
MPU6500_FSYNC_PIN = 13
MPU6500_nCS_PIN = 15
MAX30102_INT_PIN = 37

GPIO.setmode(GPIO.BOARD)
i2c = smbus.SMBus(1)

def DHT20_getdata():
    if((i2c.read_byte(DHT20_ADDRESS) & 0x18) != 0x18):
        raise ValueError("DHT20 Init Error")
    
    i2c.write_i2c_block_data(DHT20_ADDRESS, 0xAC, [0x33, 0x00])
    time.sleep(0.1)
    
    if((i2c.read_byte(0x38)& 0x80)==0x80):
        raise ValueError("DHT20 Busy")
    data = i2c.read_i2c_block_data(DHT20_ADDRESS, 0xAC, 7)
    
    humidity = ((data[1] << 12) | data[2] << 4 | (data[3] & 0xF0) >> 4) *100 / (1 << 20)
    temperature = ((data[3] & 0x0F) << 16 | data[4] << 8 | data[5]) / (1 << 20) * 200 - 50.0

    crc = 0xFF
    for byte in data[:6]:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x31
            else:
                crc <<= 1
        crc &= 0xFF
    
    if crc != data[6]:
        raise ValueError("DHT20 CRC Check Error")
    
    return temperature, humidity

def AGS10_getdata():
    data = i2c.read_i2c_block_data(AGS10_ADDRESS, 0x00, 5)
    if((data[0]& 0x01) != 0x00):
        raise ValueError("AGS10 warming or data not update")
    TVOC = (data[1] << 16 | data[2] << 8 | data[3]) / 1000
    crc = 0xFF
    for byte in data[:4]:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x31
            else:
                crc <<= 1
        crc &= 0xFF
    
    if crc != data[4]:
        raise ValueError("AGS10 CRC Check Error")
    return TVOC
    
def BH1750FVI_init():
    GPIO.setup(BH1750FVI_ADDR_PIN, GPIO.OUT, initial = GPIO.LOW)
    GPIO.setup(BH1750FVI_DVI_PIN, GPIO.OUT, initial = GPIO.LOW)
    time.sleep(0.1)
    GPIO.output(BH1750FVI_ADDR_PIN, GPIO.LOW)
    GPIO.output(BH1750FVI_DVI_PIN, GPIO.HIGH)
    time.sleep(0.1)
    i2c.write_byte(BH1750FVI_ADDRESS, 0x01)
    time.sleep(0.1)
    i2c.write_byte(BH1750FVI_ADDRESS, 0x07)
    time.sleep(0.1)
    #set CONTINUOUS_HIGH_RES_MODE
    i2c.write_byte(BH1750FVI_ADDRESS, 0x10)
    time.sleep(0.2)

def BH1750FVI_getdata():
    data = i2c.read_i2c_block_data(BH1750FVI_ADDRESS, 0x10,2)
    
    AL = (data[0] << 8 | data[1])/ 1.2
    
    return AL

def BMP581_init():
    GPIO.setup(BMP581_SDO_PIN, GPIO.OUT, initial = GPIO.LOW)
    GPIO.setup(BMP581_INT_PIN, GPIO.IN)
    time.sleep(0.1)
    GPIO.output(BMP581_SDO_PIN, GPIO.LOW)
    time.sleep(0.1)
    
    if(i2c.read_byte_data(BMP581_ADDRESS,0x01) == 0x00):
        raise ValueError("BMP581 CHIP_ID Check Error")
    if(i2c.read_byte_data(BMP581_ADDRESS, 0x28) & 0x02 != 0x02):
        raise ValueError("BMP581 STATUS_NVM_RDY Check Error")
    if(i2c.read_byte_data(BMP581_ADDRESS, 0x28) & 0x04 != 0x00):
        raise ValueError("BMP581 STATUS_NVM_ERR Check Error")
    if(i2c.read_byte_data(BMP581_ADDRESS, 0x27) != 0x10):
        raise ValueError("BMP581 INT Check Error")
    
    i2c.write_byte_data(BMP581_ADDRESS, 0x36, 0x7F)
    i2c.write_byte_data(BMP581_ADDRESS, 0x31, 0x09)
    i2c.write_byte_data(BMP581_ADDRESS, 0x37, 0xEB)
    
def BMP581_getdata():
    data = i2c.read_i2c_block_data(BMP581_ADDRESS, 0x1D, 6)
    
    temp = (data[2] << 16 | data[1] << 8 | data[0]) / (1 << 16)
    pressure = (data[5] << 16 | data[4] << 8 | data[3]) / (1 << 6)
    
    return temp, pressure

def MPU6500_init():
    GPIO.setup(MPU6500_SDO_PIN, GPIO.OUT, initial = GPIO.LOW)
    GPIO.setup(MPU6500_INT_PIN, GPIO.IN)
    GPIO.setup(MPU6500_FSYNC_PIN, GPIO.OUT, initial = GPIO.LOW) #if unuse, to GND
    GPIO.setup(MPU6500_nCS_PIN, GPIO.OUT, initial = GPIO.HIGH)
    time.sleep(0.1)
    GPIO.output(MPU6500_SDO_PIN, GPIO.LOW)
    GPIO.setup(MPU6500_nCS_PIN, GPIO.HIGH)
    GPIO.output(MPU6500_FSYNC_PIN, GPIO.LOW)
    time.sleep(0.1)
    
    i2c.write_byte_data(MPU6500_ADDRESS, 0x6B, 0x80) #PWR_MGMT_1
    time.sleep(0.2)
    i2c.write_byte_data(MPU6500_ADDRESS, 0x6B, 0x00) #PWR_MGMT_1
    time.sleep(0.2)
    i2c.write_byte_data(MPU6500_ADDRESS, 0x6A, 0x08) #USER_CTRL DMP reset
    time.sleep(0.2)
    i2c.write_byte_data(MPU6500_ADDRESS, 0x6A, 0x00) #USER_CTRL DMP reset
    time.sleep(0.2)
    i2c.write_byte_data(MPU6500_ADDRESS, 0x1A, 0x00)
    i2c.write_byte_data(MPU6500_ADDRESS, 0x1B, 0x10) #1000 degrees pre second (Sensitivity Factor 32.8)
    i2c.write_byte_data(MPU6500_ADDRESS, 0x1C, 0x10) #8g (Sensitivity Factor 4096)
    i2c.write_byte_data(MPU6500_ADDRESS, 0x1D, 0x01) #DLPF1
    i2c.write_byte_data(MPU6500_ADDRESS, 0x1E, 0x08) #62.5Hz
    i2c.write_byte_data(MPU6500_ADDRESS, 0x1F, 0xC8) #Wake on Motion 200mg
    i2c.write_byte_data(MPU6500_ADDRESS, 0x38, 0x40) #INT Wake on Motion
    i2c.write_byte_data(MPU6500_ADDRESS, 0x69, 0xC0) #ACCEL_INTEL_CTRL
    i2c.write_byte_data(MPU6500_ADDRESS, 0x6A, 0x80) #USER_CTRL DMP enable
    i2c.write_byte_data(MPU6500_ADDRESS, 0x6B, 0x01) #PWR_MGMT_1
    i2c.write_byte_data(MPU6500_ADDRESS, 0x6C, 0x00) #PWR_MGMT_2

def MPU6500_sign(value):
    if value > 32768:
            value = value - 65536
    return value
    
def MPU6500_getdata():
    data_accel = i2c.read_i2c_block_data(MPU6500_ADDRESS, 0x3B, 6)
    accel_x = MPU6500_sign(data_accel[0] << 8 | data_accel[1]) / 4096.0 #Sensitivity Factor
    accel_y = MPU6500_sign(data_accel[2] << 8 | data_accel[3]) / 4096.0 
    accel_z = MPU6500_sign(data_accel[4] << 8 | data_accel[5]) / 4096.0 
#     print(data_accel)
    data_temp = i2c.read_i2c_block_data(MPU6500_ADDRESS, 0x41, 2)
    temp = ((data_temp[0] << 8 | data_temp[1]) - 21.0) / 333.87 + 21.0
#     print(data_temp)
    data_gyro = i2c.read_i2c_block_data(MPU6500_ADDRESS, 0x43, 6)
    gyro_x = MPU6500_sign(data_gyro[0] << 8 | data_gyro[1]) / 32.8 #Sensitivity Factor
    gyro_y = MPU6500_sign(data_gyro[2] << 8 | data_gyro[3]) / 32.8
    gyro_z = MPU6500_sign(data_gyro[4] << 8 | data_gyro[5]) / 32.8
#     print(data_gyro)
    return accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z, temp

def MAX30102_init():
    GPIO.setup(MAX30102_INT_PIN, GPIO.IN)
    time.sleep(0.1)
    
    i2c.write_byte_data(MAX30102_ADDRESS, 0x09, 0x40) #Reset
    time.sleep(0.1)
    i2c.write_byte_data(MAX30102_ADDRESS, 0x09, 0x03) #spO2 Mode
    i2c.write_byte_data(MAX30102_ADDRESS, 0x0A, 0x0F) #400Hz 411us
    i2c.write_byte_data(MAX30102_ADDRESS, 0x0C, 0x0F) #LED Current 3.0mA
    i2c.write_byte_data(MAX30102_ADDRESS, 0x0D, 0x0F) #LED Current 3.0mA
    i2c.write_byte_data(MAX30102_ADDRESS, 0x21, 0x00) #0x01 for one temp sample
    i2c.write_byte_data(MAX30102_ADDRESS, 0x02, 0x00)
    i2c.write_byte_data(MAX30102_ADDRESS, 0x03, 0x00)
    i2c.write_byte_data(MAX30102_ADDRESS, 0x04, 0x00)
    i2c.write_byte_data(MAX30102_ADDRESS, 0x05, 0x00)
    i2c.write_byte_data(MAX30102_ADDRESS, 0x06, 0x00)
    i2c.write_byte_data(MAX30102_ADDRESS, 0x08, 0x90) #16 samples average
    i2c.write_byte_data(MAX30102_ADDRESS, 0x21, 0x01)

def MAX30102_getdata():
    write_ptr = i2c.read_byte_data(MAX30102_ADDRESS, 0x04)
    read_ptr = i2c.read_byte_data(MAX30102_ADDRESS, 0x06)
    overflow_counter = i2c.read_byte_data(MAX30102_ADDRESS, 0x05)
    
    if write_ptr == read_ptr:
        print("No new data to read.")
        return [], []
    elif write_ptr > read_ptr:
        num_samples = write_ptr - read_ptr
    else:
        num_samples = (32 - read_ptr) + write_ptr
    
#     print(f"Number of samples to read: {num_samples}")

    red_data = []
    ir_data = []
    for _ in range(num_samples):
        raw_data = i2c.read_i2c_block_data(MAX30102_ADDRESS, 0x07, 6)
        red = (raw_data[0] << 16) | (raw_data[1] << 8) | raw_data[2]
        ir = (raw_data[3] << 16) | (raw_data[4] << 8) | raw_data[5]
        red_data.append(red)
        ir_data.append(ir)
#         print(f"RED: {red}, IR: {ir}")
    
    temp_int = i2c.read_byte_data(MAX30102_ADDRESS, 0x1F)
    temp_frac = i2c.read_byte_data(MAX30102_ADDRESS, 0x20)
    i2c.write_byte_data(MAX30102_ADDRESS, 0x21, 0x01) #for next
    
    temp = temp_int + (temp_frac * 0.0625)
#     print(temp)
    
    return red_data, ir_data, temp

def MAX30102_manage_size(data_array, max_length = 300):
    if len(data_array) > max_length:
        return data_array[-max_length:]
    else:
        return data_array

def MAX30102_cal(red_data, ir_data, sampling_rate):
    #lowpass filter
    #order = 4, cutoff = 3
    b, a = butter(4, 3, btype = 'low', analog = False, fs = sampling_rate)
    ir_data_filtered = filtfilt(b, a, ir_data)
    
    peaks, _ = find_peaks(ir_data_filtered, height = 2000, distance=sampling_rate/3)
    valleys, _ = find_peaks(-ir_data_filtered, distance=sampling_rate/3)
    
    if len(peaks) > 1:
        peak_avg = np.mean(ir_data_filtered[peaks])
        valley_avg = np.mean(ir_data_filtered[valleys])
        print(peak_avg - valley_avg)
        if (peak_avg - valley_avg) > 500 and (peak_avg - valley_avg) < 2000:
            peak_intervals = np.diff(peaks) / sampling_rate
            heart_rate = 60.0 / np.mean(peak_intervals)
        else:
            heart_rate = -1.0
    else:
        heart_rate = -1.0
    
    #plot
#     plt.clf()
#     plt.plot(ir_data_filtered)
#     plt.plot(ir_data)
#     plt.plot(peaks, ir_data_filtered[peaks], "*")
#     plt.axhline(y =np.mean(ir_data_filtered), linestyle = '--', color='g')
#     plt.draw()
#     plt.pause(0.01)
    
    red_ac = np.max(red_data) - np.min(red_data)
    ir_ac = np.max(ir_data) - np.min(ir_data)
    red_dc = np.mean(red_data)
    ir_dc = np.mean(ir_data)
    
    ratio = (red_ac / red_dc) / (ir_ac / ir_dc)
#     spo2 = 104 - 17 * ratio
    spo2 = - 45.060 * ratio * ratio + 30.354 * ratio + 94.845
    
    if spo2 < 90.0 or heart_rate == -1.0:
        spo2 = -1.0
        heart_rate = -1.0
    return heart_rate, spo2

def insert_data(DHT20_temperature, DHT20_humidity, AGS10_TVOC, AL, BMP581_Temperature, BMP581_Pressure,
        MPU6500_accel_x, MPU6500_accel_y, MPU6500_accel_z, MPU6500_gyro_x, MPU6500_gyro_y, MPU6500_gyro_z, MPU6500_temp,
        heart_rate, spo2, MAX30102_temp):
    conn = sqlite3.connect('/home/xxlxxl/DockerConf/HomeAssistant/SensorDB/SensorBoard.db')
    cursor = conn.cursor()
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO SensorBoard (time, DHT20_temperature, DHT20_humidity, AGS10_TVOC, AL, BMP581_Temperature, BMP581_Pressure,
        MPU6500_accel_x, MPU6500_accel_y, MPU6500_accel_z, MPU6500_gyro_x, MPU6500_gyro_y, MPU6500_gyro_z, MPU6500_temp,
        heart_rate, spo2, MAX30102_temp)
        VALUES (?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?,
        ?, ?)
    ''', (current_time, DHT20_temperature, DHT20_humidity, AGS10_TVOC, AL, BMP581_Temperature, BMP581_Pressure,
        MPU6500_accel_x, MPU6500_accel_y, MPU6500_accel_z, MPU6500_gyro_x, MPU6500_gyro_y, MPU6500_gyro_z, MPU6500_temp,
        heart_rate, spo2, MAX30102_temp))
    
    delete_timeline = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        DELETE FROM SensorBoard WHERE time < ?
    ''', (delete_timeline,))
    
    conn.commit()
    conn.close()


if __name__ == '__main__':
    try:
        BH1750FVI_init()
    except OSError as e:
            print("BH1750FVI Init Error: ", e)
    except ValueError as e:
            print(e)
    try:
        BMP581_init()
    except OSError as e:
            print("BMP581 Init Error: ", e)
    except ValueError as e:
            print(e)
    try:
        MPU6500_init()
    except OSError as e:
            print("MPU6500 Init Error: ", e)
    except ValueError as e:
            print(e)
    try:
        MAX30102_init()
        red_data = np.array([])
        ir_data = np.array([])
    except OSError as e:
            print("MAX30102 Init Error: ", e)
    except ValueError as e:
            print(e)
#     plt.ion()
    
    while True:
        #DHT20
        try:
            DHT20_temperature, DHT20_humidity = -2.0, -2.0
            DHT20_temperature, DHT20_humidity = DHT20_getdata()
    #         print(
    #             "Temp: {:.2f} C    Humidity: {:.2f}% ".format(
    #                 DHT20_temperature, DHT20_humidity
    #             )
    #         )
    
        except OSError as e:
            print("DHT20 I2C Communication Error: ", e)
        except ValueError as e:
            print(e)
        
        #AGS10
        try:
            AGS10_TVOC = -2.0
            AGS10_TVOC = AGS10_getdata()
    #         print(f"TVOC: {AGS10_TVOC:.3f} ppm")

        except OSError as e:
            print("AGS10 I2C Communication Error: ", e)
        except ValueError as e:
            print(e)
            
        #BH1750FVI
        try:
            AL = -2.0
            AL = BH1750FVI_getdata()
#             print(f"AL: {AL:.1f} lux")
            
        except OSError as e:
            print("BH1750FVI I2C Communication Error: ", e)
        except ValueError as e:
            print(e)
        
        #BMP581
        try:
            BMP581_Temperature, BMP581_Pressure = -2.0, -2.0
            BMP581_Temperature, BMP581_Pressure = BMP581_getdata()
#             print(
#                 "BMP581_Temperature: {:.2f} C    BMP581_Pressure: {:.2f} Pa ".format(
#                 BMP581_Temperature, BMP581_Pressure
#                     )
#              )
            
        except OSError as e:
            print("BMP581 I2C Communication Error: ", e)
        except ValueError as e:
            print(e)
        
        #MPU6500
        try:
            MPU6500_accel_x, MPU6500_accel_y, MPU6500_accel_z = -2.0, -2.0, -2.0
            MPU6500_gyro_x, MPU6500_gyro_y, MPU6500_gyro_z = -2.0, -2.0, -2.0
            MPU6500_temp = -2.0
            MPU6500_accel_x, MPU6500_accel_y, MPU6500_accel_z, MPU6500_gyro_x, MPU6500_gyro_y, MPU6500_gyro_z, MPU6500_temp = MPU6500_getdata()
            print(
                "Accel_X: {:.2f} g  Accel_Y: {:.2f} g  Accel_Z: {:.2f} g".format(
                MPU6500_accel_x, MPU6500_accel_y, MPU6500_accel_z
                    )
             )
            print(
                "Gyro_X: {:.2f} dps  Gyro_Y: {:.2f} dps  Gyro_Z: {:.2f} dps(degrees per second)".format(
                MPU6500_gyro_x, MPU6500_gyro_y, MPU6500_gyro_z
                    )
             )
            print(f"MPU6500_Temperature: {MPU6500_temp:.1f} C")
        except OSError as e:
            print("MPU6500 I2C Communication Error: ", e)
        except ValueError as e:
            print(e)
        
        #MAX30102
        try:
            heart_rate, spo2, MAX30102_temp = -2.0, -2.0, -2.0
            new_red, new_ir, MAX30102_temp = MAX30102_getdata()
            red_data = np.append(red_data, new_red)
            ir_data = np.append(ir_data, new_ir)
            
            red_data = MAX30102_manage_size(red_data)
            ir_data = MAX30102_manage_size(ir_data)
            
            sample_rate = 400 / 16 #raw sample / sample average
            
            heart_rate, spo2 = MAX30102_cal(red_data, ir_data, sample_rate)
#             print(f"Heart Rate: {heart_rate:.2f} bpm, SpO2: {spo2:.2f} %")
#             print(f"MAX30102_Temperature: {MAX30102_temp:.2f} C")
            
        except OSError as e:
            print("MAX30102 I2C Communication Error: ", e)
        except ValueError as e:
            print(e)
        
        #insert data to sqlite3
        try:
            insert_data(DHT20_temperature, DHT20_humidity, AGS10_TVOC, AL, BMP581_Temperature, BMP581_Pressure,
        MPU6500_accel_x, MPU6500_accel_y, MPU6500_accel_z, MPU6500_gyro_x, MPU6500_gyro_y, MPU6500_gyro_z, MPU6500_temp,
        heart_rate, spo2, MAX30102_temp)
#             print(f"AL: {AL:.1f} lux")
            
        except OSError as e:
            print("Sqlite3 Error: ", e)
            
#         if keyboard.is_pressed('q'):
#             print("Q key pressed. Exiting...")
#             break
        time.sleep(0.5)
    
    #cleanup
#     GPIO.cleanup()
#     print("GPIO cleaned up and program exited.")
    