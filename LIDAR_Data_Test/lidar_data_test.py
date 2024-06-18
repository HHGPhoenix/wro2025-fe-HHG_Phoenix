from LIDAR.LIDARManager import LidarSensor
from PSController.psController import PSController
import time
import threading
import RPi.GPIO as GPIO
import serial
import uuid

# Initialize the LIDAR sensor
lidar = LidarSensor(usb_address="/dev/ttyUSB0", LIDAR_commands_path=r"LIDAR/LIDARCommands.json")

# Connect to the available USB via serial
ser = serial.Serial('/dev/ttyUSB1', 921600)
ser.write('START\n'.encode())

# Create a lock for thread-safe file writing
lock = threading.Lock()

# Set up GPIO
GPIO.setmode(GPIO.BCM)
servo_pin = 17
GPIO.setup(servo_pin, GPIO.OUT)
servo_pwm = GPIO.PWM(servo_pin, 50)  # 50 Hz frequency
servo_pwm.start(6.7)

def write_data_to_file():
    UUID = uuid.uuid4()
    lidar_data_file = rf'data/lidar_data_{UUID}.txt'
    x_values_file = rf'data/x_values_{UUID}.txt'
    while True:
        with lock:
            with open(lidar_data_file, 'a') as f:
                f.write(str(lidar.data_arrays[-1]) + '\n')
            with open(x_values_file, 'a') as f:
                x, _, _, _ = controller.get_analog_stick_values()
                f.write(str(x) + '\n')
        time.sleep(0.1)  # Sleep for 0.1 seconds to achieve 10Hz frequency

try:
    lidar.start_sensor()
    
    tLIDAR = threading.Thread(target=lidar.read_data)
    tLIDAR.start()
    
    # Create PSController instance
    controller = PSController(servo_middle_angle=6.7, servo_min_angle=5.5, servo_max_angle=8.4)
    controller.calibrate_analog_sticks()

    # Start the file writing thread
    tFileWriter = threading.Thread(target=write_data_to_file)
    tFileWriter.start()
    
    while True:
        x, y, rx, ry = controller.get_analog_stick_values()
        # print(f"x: {x:.2f}, y: {y:.2f}, rx: {rx:.2f}, ry: {ry:.2f}")

        servo_value = controller.map_servo_angle(x)
        # Write servo value
        servo_pwm.ChangeDutyCycle(servo_value)
        
        speed_value = controller.map_speed_value(ry)
        ser.write(f'SPEED {speed_value}\n'.encode())
        # print(f"Speed value: {speed_value:.2f}")

        time.sleep(0.1)
        
    
finally:
    lidar.stop_sensor()