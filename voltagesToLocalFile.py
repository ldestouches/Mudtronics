# voltagesToLocalFile.py code for CAE logging device 14-07-2025, logs to local file only

import time
from datetime import datetime
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Initialize I2C and ADS1115 ADC
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)

# Init Analog Input Channels
channel0 = AnalogIn(ads, ADS.P0)
channel1 = AnalogIn(ads, ADS.P1)
channel2 = AnalogIn(ads, ADS.P2)
channel3 = AnalogIn(ads, ADS.P3)

def read_sensors():
    # Return a dictionary with the sensor readings, *1000 for millivolts readings
    return {
        'voltage0': (channel0.voltage)*1000,
        'voltage1': (channel1.voltage)*1000,
        'voltage2': (channel2.voltage)*1000,
        'voltage3': (channel3.voltage)*1000
    }

try:
    # Post the data
    print("starting...")
    while True:
        data = read_sensors()  # Get sensor data without using a global variable
        print("v0 = " + str((channel0.voltage)*1000)) # prints to raspberry pi console
        print("v1 = " + str((channel1.voltage)*1000))
        print("v2 = " + str((channel2.voltage)*1000))
        print("v3 = " + str((channel3.voltage)*1000))
        print("- - - - - - - - - -")
        
        file = open("20260805_soil_log.txt", "a") # write all voltages to local text file log.txt
        file.write("voltage0 = " + str((channel0.voltage)*1000) + "\n")
        file.write("voltage1 = " + str((channel1.voltage)*1000) + "\n") 
        file.write("voltage2 = " + str((channel2.voltage)*1000) + "\n")
        file.write("voltage3 = " + str((channel3.voltage)*1000) + "\n")
        file.write(datetime.today().strftime('%d-%m-%Y %H:%M:%S') + "\n")
        
        time.sleep(300)  # sleeps 0 minutes

except KeyboardInterrupt:
    print("Exiting...")
