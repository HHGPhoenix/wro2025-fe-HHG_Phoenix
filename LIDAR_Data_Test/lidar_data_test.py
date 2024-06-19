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

# Load your trained model
steering_model = tf.keras.models.load_model('best_model_e9532d96-42f5-49e9-969e-efc6fcbaeb83.h5')

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

    # Remove data from 110 to 250 degrees
    df_interpolated = df_interpolated[(df_interpolated["angle"] < 110) | (df_interpolated["angle"] > 250)]

    # Use the model to predict the servo angle
    predicted_angle = steering_model.predict(df_interpolated)

    return predicted_angle        

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

        predicted_value = predict_servo_angle(lidar.data_arrays[-1])
        
        servo_value = controller.map_servo_angle(predicted_value)
        
        # Write servo value
        servo_pwm.ChangeDutyCycle(servo_value)
        
        speed_value = controller.map_speed_value(ry)
        ser.write(f'SPEED {speed_value}\n'.encode())
        # print(f"Speed value: {speed_value:.2f}")

        time.sleep(0.1)
    
finally:
    lidar.stop_sensor()