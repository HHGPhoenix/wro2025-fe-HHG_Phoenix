from LIDAR.LIDARManager import LidarSensor
from PSController.psController import PSController
import time
import threading
import RPi.GPIO as GPIO
import serial
import uuid
import tensorflow as tf
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from multiprocessing import Process, Queue
from queue import Empty
import psutil
import subprocess


lidar = LidarSensor(usb_address="/dev/serial0", LIDAR_commands_path=r"LIDAR/LIDARCommands.json")
lidar.start_sensor()

# pLIDAR = mp.Process(target=lidar.read_data, args=(lidar_data_arrays,))
# pLIDAR.start()

tLIDAR = threading.Thread(target=lidar.read_data)
tLIDAR.start()

# Connect to the available USB via serial
ser = serial.Serial('/dev/ttyUSB0', 921600)
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
        
def predict_servo_angle(lidar_data, steering_model):
    df = pd.DataFrame(lidar_data, columns=["angle", "distance", "intensity"])
    df = df.drop(columns=["intensity"])
    df = df[df["distance"] != 0]  # Filter out invalid points
    df["angle"] = (df["angle"] - 90) % 360
    df = df.sort_values("angle")
    
    print("Predicting angle")

    desired_angles = np.arange(0, 360, 1)
    interp_distance = interp1d(df["angle"], df["distance"], kind="linear", bounds_error=False, fill_value="extrapolate")
    interpolated_distances = interp_distance(desired_angles)

    interpolated_data = list(zip(desired_angles, interpolated_distances))
    
    # Convert to DataFrame for easier manipulation
    df_interpolated = pd.DataFrame(interpolated_data, columns=["angle", "distance"])

    # Remove data from 110 to 250 degrees
    df_interpolated = df_interpolated[(df_interpolated["angle"] < 110) | (df_interpolated["angle"] > 250)]

    df_interpolated_list = df_interpolated.values.tolist()
    
    final_input = np.array(df_interpolated_list, dtype=np.float32)
    final_input = np.expand_dims(final_input, axis=0)
    final_input = np.expand_dims(final_input, axis=-1)

    print("Final input shape:", final_input.shape)
    
    predicted_angle = steering_model.predict(final_input)
    
    print("Predicted angle:", predicted_angle)

    return predicted_angle

def run_model(input_queue, output_queue):
    steering_model = tf.keras.models.load_model('verygoodmovedxmodel3.h5')
    
    while True:
        if not input_queue.empty():
            print("Running model")
            lidar_data = input_queue.get()
            predicted_value = predict_servo_angle(lidar_data, steering_model)
            output_queue.put(predicted_value)
            print("Model finished")
            
def get_cpu_usage():
    return psutil.cpu_percent()

def get_cpu_temp():
    output = subprocess.check_output("vcgencmd measure_temp", shell=True)
    temp_str = output.decode("utf-8")
    temp = float(temp_str.split("=")[1].split("'")[0])
    return temp

            
# Create two queues: one for input lidar data and one for output predicted values
input_queue = Queue()
output_queue = Queue()

# Create a new process for running the AI model
pModel = Process(target=run_model, args=(input_queue, output_queue))

# Start the new process
pModel.start()

try:
    # Create PSController instance
    controller = PSController(servo_middle_angle=6.7, servo_min_angle=5.5, servo_max_angle=8.4)
    controller.calibrate_analog_sticks()

    # Start the file writing thread
    tFileWriter = threading.Thread(target=write_data_to_file)
    tFileWriter.start()
    
    while not lidar.data_arrays:
        pass
    
    while True:
        x, y, rx, ry = controller.get_analog_stick_values()

        # Put the lidar data in the queue
        input_queue.put(lidar.data_arrays[-1])
    
        while output_queue.empty():
            pass
    
        # Get the predicted value from the queue
        predicted_value = output_queue.get()
        # print(predicted_value)
        
        print(predicted_value)

        servo_value = controller.map_servo_angle(predicted_value)

        # cpu_usage = get_cpu_usage()
        # cpu_temp = get_cpu_temp()
        # print("CPU Usage:", cpu_usage, "CPU Temperature:", cpu_temp)
        
        if servo_value < 5.5:
            servo_value = 5.5
            
        if servo_value > 8.4:
            servo_value = 8.4
        
        # Write servo value
        servo_pwm.ChangeDutyCycle(servo_value)
        
        speed_value = controller.map_speed_value(ry)
        ser.write(f'SPEED {speed_value}\n'.encode())

        time.sleep(0.03)
    
finally:
    lidar.stop_sensor()
    pModel.terminate()