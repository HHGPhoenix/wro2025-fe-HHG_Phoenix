import threading
import adafruit_mpu6050
import busio
import board
import time
# Need to copy files from old repo and enhance them to work nicely. 
# It would be nice to use the DMP for accurate positioning and connect the interrupt pin for 
# better performance.

class GyroSensor():
    def __init__(self):
        i2c = busio.I2C(board.D1, board.D0)
        self.sensor = adafruit_mpu6050.MPU6050(i2c, address=0x68)
        time.sleep(0.1)
        self.sensor.gyro_range = adafruit_mpu6050.GyroRange.RANGE_250_DPS
        time.sleep(0.1)
        
        self.angle = 0.0  # Initial angle
        self.last_time = time.time()
        self._running = False
        self._thread = None

    def _get_angle_loop(self):
        offset_x = 0.29
        offset_y = 0.0
        offset_z = 0.0

        while self._running:
            time.sleep(0.01)
            
            # Read gyroscope data and apply offsets
            gyro_data = self.sensor.gyro
            gyro_data = [gyro_data[0] + offset_x, gyro_data[1] + offset_y, gyro_data[2] + offset_z]
            
            # Get the current time
            current_time = time.time()

            # Calculate the time elapsed since the last measurement
            delta_time = current_time - self.last_time

            # Ensure delta_time is within a reasonable range to avoid large jumps
            if delta_time >= 0.5:
                delta_time = 0.003

            # Integrate the gyroscope readings to get the change in angle
            if -0.02 < gyro_data[0] < 0.02:
                delta_angle = 0
            else:
                delta_angle = gyro_data[0] * delta_time * 60

            # Update the angle
            self.angle += delta_angle

            # Update the last time for the next iteration
            self.last_time = current_time
            
            print(f"Angle: {self.angle}")

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
                




#A class for reading a MPU6050 Gyroscope
# class Gyroscope2():
#     def __init__(self):
#         self.threadStop = 0
#         self.rotation = [0, 0, 0]
        
#         self.mpu = MPU6050.MPU6050(a_bus=0, a_address=0x69)
#         self.mpu.dmp_initialize()
#         self.mpu.set_DMP_enabled(True)
        
        
#         self.mpu.set_x_gyro_offset(int(40))
#         self.mpu.set_y_gyro_offset(int(-17))
#         self.mpu.set_z_gyro_offset(int(0))
        
#         self.mpu.set_x_accel_offset(int(-90))
#         self.mpu.set_y_accel_offset(int(-665))
#         self.mpu.set_z_accel_offset(int(-950))
        
#     def read(self):
#         while self.threadStop == 0:
#             # Assuming you have already initialized and calibrated your MPU6050 as 'mpu'
#             # Get FIFO buffer data
#             fifo_count = self.mpu.get_FIFO_count()
#             if fifo_count < 42:
#                 continue
#             fifo_buffer = self.mpu.get_FIFO_bytes(fifo_count)
            
#             # Now you can get quaternion data
#             quat = self.mpu.DMP_get_quaternion(fifo_buffer)
            
            
#             # Get gravity vector
#             grav = self.mpu.DMP_get_gravity(quat)
            
#             if grav.x == 0 or grav.y == 0 or grav.z == 0:
#                 continue
            
            
#             # Now you can get roll, pitch, yaw
#             self.rotation = self.mpu.DMP_get_euler_roll_pitch_yaw(quat, grav)
            
#             # rotation = mpu.get_rotation()
#             # print("X: {0:.2f}, Y: {1:.2f}, Z: {2:.2f}".format(rotation[0], rotation[1], rotation[2]))
#             # acceleration = mpu.get_acceleration()
#             # print("X: {0:.2f}, Y: {1:.2f}, Z: {2:.2f}".format(acceleration[0], acceleration[1], acceleration[2]))
            
#             # Adjust axes for upright robot
            
#             # print("Roll: {0:.2f}, Pitch: {1:.2f}, Yaw: {2:.2f}".format(rotation.x, rotation.y, rotation.z))
   