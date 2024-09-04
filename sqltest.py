import sqlite3
from datetime import datetime

# 创建或连接到SQLite数据库
conn = sqlite3.connect('temperature_humidity.db')

# 创建一个游标对象
cursor = conn.cursor()

# 创建温湿度数据表
def create_table():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weather_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL
        )
    ''')
    conn.commit()

# 插入温湿度数据到表中
def insert_data(temperature, humidity):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO weather_data (timestamp, temperature, humidity)
        VALUES (?, ?, ?)
    ''', (timestamp, temperature, humidity))
    conn.commit()

# 示例用法
if __name__ == '__main__':
    create_table()  # 创建数据表

    # 模拟插入一些温湿度数据
    temperature = 22.5  # 例如：22.5摄氏度
    humidity = 60.0     # 例如：60%
    insert_data(temperature, humidity)

    # 查询并显示数据
    cursor.execute('SELECT * FROM weather_data')
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    # 关闭数据库连接
    conn.close()
