import sqlite3
import json

DB_NAME = '/config/SensorDB/SensorBoard.db'
# DB_NAME = '/home/xxlxxl/DockerConf/HomeAssistant/SensorDB/SensorBoard.db'

def get_latest_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DHT20_temperature, DHT20_humidity, AGS10_TVOC, AL, BMP581_Temperature, BMP581_Pressure,
        MPU6500_accel_x, MPU6500_accel_y, MPU6500_accel_z, MPU6500_gyro_x, MPU6500_gyro_y, MPU6500_gyro_z, MPU6500_temp,
        heart_rate, spo2, MAX30102_temp FROM SensorBoard ORDER BY time DESC LIMIT 1
    ''')
    result = cursor.fetchone()

    conn.close()

    if result:
        return result
    else:
        return None


if __name__ == '__main__':
    latest_data = get_latest_data()
    SensorBoardinfo = {}
    SensorBoardinfo['DHT20_T'] = latest_data[0]
    SensorBoardinfo['DHT20_H'] = latest_data[1]
    SensorBoardinfo['TVOC'] = latest_data[2]
    SensorBoardinfo['AL'] = latest_data[3]
    SensorBoardinfo['BMP581_T'] = latest_data[4]
    SensorBoardinfo['BMP581_P'] = latest_data[5]
    SensorBoardinfo['Accel_X'] = latest_data[6]
    SensorBoardinfo['Accel_Y'] = latest_data[7]
    SensorBoardinfo['Accel_Z'] = latest_data[8]
    SensorBoardinfo['Gyro_X'] = latest_data[9]
    SensorBoardinfo['Gyro_Y'] = latest_data[10]
    SensorBoardinfo['Gyro_Z'] = latest_data[11]
    SensorBoardinfo['MPU6500_T'] = latest_data[12]
    SensorBoardinfo['Heart_Rate'] = latest_data[13]
    SensorBoardinfo['Spo2'] = latest_data[14]
    SensorBoardinfo['MAX30102_T'] = latest_data[15]
    
    print(json.dumps(SensorBoardinfo))
