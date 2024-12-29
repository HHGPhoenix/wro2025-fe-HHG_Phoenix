import threading
from mpu6050 import mpu6050
import busio
import board
import time
# Need to copy files from old repo and enhance them to work nicely. 
# It would be nice to use the DMP for accurate positioning and connect the interrupt pin for 
# better performance.

class GyroSensor():
    def __init__(self):
        self.sensor = mpu6050(0x68, bus=1)
        print(type(0x68))
        time.sleep(1)
        
        self.angle = 0.0  # Initial angle
        self.last_time = time.time()
        self._running = False
        self._thread = None

    def _get_angle_loop(self):
        offset_x = -0.6287
        offset_y = 0.0
        offset_z = 0.0

        while self._running:
            time.sleep(0.03)
            
            # Read gyroscope data and apply offsets
            gyro_data = self.sensor.get_gyro_data()
            # print(f"Gyro data: {gyro_data}")
            gyro_data = [gyro_data['x'] + offset_x, gyro_data['y'] + offset_y, gyro_data['z'] + offset_z]
            
            # Get the current time
            current_time = time.time()

            # Calculate the time elapsed since the last measurement
            delta_time = current_time - self.last_time

            # Ensure delta_time is within a reasonable range to avoid large jumps
            if delta_time >= 0.5:
                delta_time = 0.003

            # Integrate the gyroscope readings to get the change in angle
            if -0.02 < gyro_data[2] < 0.02:
                delta_angle = 0
            else:
                delta_angle = gyro_data[2] * delta_time

            # Update the angle
            self.angle += delta_angle

            # Update the last time for the next iteration
            self.last_time = current_time
            
            # print(f"Angle: {self.angle}")

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._get_angle_loop)
            self._thread.start()

    def stop(self):
        if self._running:
            self._running = False
            self._thread.join()
            self._thread = None

    def reset_angle(self):
        self.angle = 0.0