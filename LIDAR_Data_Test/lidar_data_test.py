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

# Load your trained model
steering_model = tf.keras.models.load_model('best_model_605019d7-1080-49b5-ad60-971e86a3fce4.h5')

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
        
def predict_servo_angle(lidar_data):
    # Preprocess your data if necessary
    # For example, if your model expects a certain shape, you might need to reshape your data
    # lidar_data = lidar_data.reshape((1, -1))
    df = pd.DataFrame(lidar_data, columns=["angle", "distance", "intensity"])

    # Filter out invalid points (distance and intensity zero)
    df = df[(df["distance"] != 0)]
    df["angle"] = (df["angle"] - 90) % 360

    # Sort the data by angle
    df = df.sort_values("angle")

    # Define the desired angles (one point per angle from 0 to 359)
    desired_angles = np.arange(0, 360, 1)

    # Interpolate distance and intensity for missing angles, use nearest for fill_value
    interp_distance = interp1d(df["angle"], df["distance"], kind="linear", bounds_error=False, fill_value=(df["distance"].iloc[0], df["distance"].iloc[-1]))
    interp_intensity = interp1d(df["angle"], df["intensity"], kind="linear", bounds_error=False, fill_value=(df["intensity"].iloc[0], df["intensity"].iloc[-1]))

    # Generate the interpolated values
    interpolated_distances = interp_distance(desired_angles)
    interpolated_intensities = interp_intensity(desired_angles)

    # Create the new list with interpolated data
    interpolated_data = list(zip(desired_angles, interpolated_distances, interpolated_intensities))

    # Convert to DataFrame for easier manipulation
    df_interpolated = pd.DataFrame(interpolated_data, columns=["angle", "distance", "intensity"])

    # Reshape the DataFrame to match the input shape of the model
    df_interpolated = df_interpolated.values.reshape(-1, 360, 3, 1)

    # Use the model to predict the servo angle
    predicted_angle = steering_model.predict(df_interpolated)

    return predicted_angle

def run_model(queue):
    while True:
        if not queue.empty():
            lidar_data = queue.get()
            predicted_value = predict_servo_angle(lidar_data)
            queue.put(predicted_value)
            
def get_cpu_usage():
    return psutil.cpu_percent()

def get_cpu_temp():
    output = subprocess.check_output("vcgencmd measure_temp", shell=True)
    temp_str = output.decode("utf-8")
    temp = float(temp_str.split("=")[1].split("'")[0])
    return temp

            
# Create a queue to share data between processes
queue = Queue()

# Create a new process for running the AI model
pModel = Process(target=run_model, args=(queue,))

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
        queue.put(lidar.data_arrays[-1])
    
        try:
            # Get the predicted value from the queue
            predicted_value = queue.get(False)[-1][0]
            # print(predicted_value)
        except Empty:
            continue
        

        servo_value = controller.map_servo_angle(predicted_value)

        cpu_usage = get_cpu_usage()
        cpu_temp = get_cpu_temp()
        print("CPU Usage:", cpu_usage, "CPU Temperature:", cpu_temp)
        
        if servo_value < 5.5:
            servo_value = 5.5
            
        if servo_value > 8.4:
            servo_value = 8.4
        
        # Write servo value
        servo_pwm.ChangeDutyCycle(servo_value)
        
        speed_value = controller.map_speed_value(ry)
        ser.write(f'SPEED {speed_value}\n'.encode())

        time.sleep(0.1)
    
finally:
    lidar.stop_sensor()
    pModel.terminate()