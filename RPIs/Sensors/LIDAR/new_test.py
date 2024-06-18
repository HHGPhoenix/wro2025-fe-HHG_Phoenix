from LIDARManager import LidarSensor
import time
import threading

# Initialize the LIDAR sensor
lidar = LidarSensor(usb_address="COM4")

try:
    lidar.start_sensor()
    lidar.set_motor_speed(600)
    
    tLIDAR = threading.Thread(target=lidar.read_data)
    tLIDAR.start()
    
    while True:
        time.sleep(0.1)
    
finally:
    lidar.stop_sensor()