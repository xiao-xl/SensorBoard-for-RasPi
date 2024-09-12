# SensorBoard-for-RasPi
A sensorboard with python driver code designed for Raspberry Pi, include i2c sensors DHT20, MPU6500, BH1750FVI, AGS10, BMP581 and MAX30102

* `Sensorboard.py`
  * include driver code for all the six sensors in Python3, validated on Raspberry Pi 4B.
  * the code for MPU6500 may NOT work well, due to some manufacturing issues, which causes the i2c signal of MPU6500 chip is NOT very stable.

* `dht22.py`
  * an example driver code for a single temperature and humidity sensor DHT22 in Python3, validated on Raspberry Pi 4B.
  * include writing data into sqlite3 database

* `/PCB Folder`
  * include circuit schematic and PCB layout files for Sensorboard
  * software version: AD and JLC EDA (for manufacturing)
  * manufacturing details in folder `/PCB/JLC/Manufacture`
  * Note that since there are no high-speed signals (I2C is currently running at 100kHz), automatic routing was used during the PCB design.
### Hardware

- Raspberry Pi 4B (any model with I2C support)
- Sensorboard
- Jumper wires for connections

### Software

- Raspberry Pi OS 64bit (any version with Python 3 support)
- Python 3
- Required Python libraries:
  - `numpy`
  - `scipy`
  - `smbus` (for I2C communication)
  - `sqlite3`

### Installation

1. **Set up I2C on Raspberry Pi**:
   Enable I2C using `raspi-config`:
   ```bash
   sudo raspi-config
   ```
   --> Navigate to Interfacing Options > I2C > Enable.

2. **Install dependencies**: Install the necessary Python libraries:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-numpy python3-scipy python3-smbus sqlite3
   ```
3. **Clone the repository**: Clone this repository and navigate into the project directory

## Items to be optimized
* Add optocoupler isolation chips to the I2C signal lines (SCL, SDA) of each sensor chip to prevent reverse power supply
* Add voltage regulator and surge protection chips to the power supply (Vcc), and consider whether the ground line (GND) goes through a switch.
* Adjust the AGS10 chip's supply voltage to (3.0±0.1)V, and note that its I2C signal frequency is up to 15kHz. It is currently stable at 100kHz; if a higher frequency is needed, consider selecting a different chip.
* To improve the stability of the MPU6500, consider adjusting the reflow soldering temperature or enhancing the stability of the jumper wires.

## v 0.1.1
* Add lowpass filter for MAX30102 to improve accuracy
* support writing data to sqlite3 and query from database
