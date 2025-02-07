import threading
from mpu6050 import mpu6050
import busio
import board
import time

class GyroSensor():
    def __init__(self):
        self.sensor = mpu6050(0x68, bus=1)
        time.sleep(1)
        
        self._set_wake_register()
        self.sensor.set_gyro_range(0)
        self.sensor.set_accel_range(0)
        self.sensor.set_filter_range(6)
        
        self.angle = 0.0  # Initial angle
        self.last_time = time.time()
        self._running = False
        self._thread = None

    def _set_wake_register(self):
        # Write to the PWR_MGMT_1 register to wake up the MPU6050
        self.sensor.bus.write_byte_data(self.sensor.address, 0x6B, 0x00)

    def _get_angle_loop(self):
        offset_x = 3.73
        offset_y = 0.1
        offset_z = -1.51

        while self._running:
            time.sleep(0.05)
            
            try:
                # Read gyroscope data and apply offsets
                gyro_data = self.sensor.get_gyro_data()
                gyro_data = [gyro_data['x'] + offset_x, gyro_data['y'] + offset_y, gyro_data['z'] + offset_z]
                # print(f"Gyro data: {gyro_data}")
                
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
                
                print(f"Angle: {self.angle}")

            except Exception as e:
                print(f"Error reading gyro data: {e}")
                pass

    def start(self):
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._get_angle_loop)
            self._thread.start()

    def stop(self):
        if self._running:
            self._running = False
            self._frequency = 0
            self._thread.join()
            self._thread = None

    def reset_angle(self):
        self.angle = 0.0