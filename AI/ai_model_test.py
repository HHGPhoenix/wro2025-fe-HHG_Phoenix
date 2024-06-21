import tkinter as tk
from tkinter import filedialog
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d
import time
import threading
import queue
from tensorflow.keras.models import load_model
from LIDARManager import LidarSensor  # Import your Lidar sensor class

# Function to select a model file using file dialog
def select_model_file(data):
    path = filedialog.askopenfilename()
    data.set(path)

# Initialize the LiDAR sensor
lidar = LidarSensor(usb_address="COM4")  # Adjust the USB address as necessary
data_queue = queue.Queue()  # Create a queue to hold the data

# Function to start the LiDAR sensor
def start_lidar():
    lidar.start_sensor(mode="normal")
    threading.Thread(target=lidar.read_data).start()
    time.sleep(1)  # Give the sensor a moment to start

# Function to stop the LiDAR sensor
def stop_lidar():
    lidar.stop_sensor()

# Function to interpolate and process LiDAR data
def process_lidar_data(raw_data):
    data = raw_data
    df = pd.DataFrame(data, columns=["angle", "distance", "intensity"])
    
    df = df.drop(columns=["intensity"])

    # Filter out invalid points (distance zero)
    df = df[(df["distance"] != 0)]
    df["angle"] = (df["angle"] - 90) % 360

    # Sort the data by angle
    df = df.sort_values("angle")

    # Define the desired angles (one point per angle from 0 to 359)
    desired_angles = np.arange(0, 360, 1)

    # Interpolate distance for missing angles, use nearest for fill_value
    interp_distance = interp1d(df["angle"], df["distance"], kind="linear", bounds_error=False, fill_value=(df["distance"].iloc[0], df["distance"].iloc[-1]))

    # Generate the interpolated values
    interpolated_distances = interp_distance(desired_angles)

    # Create the new list with interpolated data
    interpolated_data = list(zip(desired_angles, interpolated_distances))

    # Convert to DataFrame for easier manipulation
    df_interpolated = pd.DataFrame(interpolated_data, columns=["angle", "distance"])

    # Remove data from 110 to 250 degrees
    df_interpolated = df_interpolated[(df_interpolated["angle"] < 110) | (df_interpolated["angle"] > 250)]
    
    return df_interpolated

# Function to update the display with new data
def update_display():
    if not data_queue.empty():
        data = data_queue.get()  # Get the latest data array from the queue
        
        # Process the LiDAR data
        processed_data = process_lidar_data(data)

        # Expand dimensions to fit model input shape
        model_input = np.expand_dims(processed_data['distance'].values, axis=0)
        model_input = np.expand_dims(model_input, axis=-1)

        # Predict using the model
        model_output = model.predict(model_input)
        
        # Update the plot with the latest data and model output
        ax1.clear()  # Clear the previous LiDAR plot
        ax1.scatter(processed_data["angle"], processed_data["distance"], s=3)
        ax1.set_title('LIDAR Data')
        ax1.set_xlabel('Angle (degrees)')
        ax1.set_ylabel('Distance')
        ax1.grid(True)

        ax2.clear()  # Clear the previous model output plot
        ax2.plot(model_output[0], label='Model Output')
        ax2.set_title('Model Output')
        ax2.set_xlabel('Sample Index')
        ax2.set_ylabel('Output Value')
        ax2.grid(True)

        fig.canvas.draw()
        
    # Schedule the next update after 2 seconds
    root.after(2000, update_display)

# Function to start processing and displaying data
def process_and_display():
    global model
    model_file_path = model_file_path_var.get()

    print(f"Model file path: {model_file_path}")

    # Load the model
    model = load_model(model_file_path)

    start_lidar()  # Start the LiDAR sensor

    update_display()  # Start updating the display

# Tkinter GUI setup
root = tk.Tk()
root.title("Real-Time LIDAR and Model Output")

model_file_path_var = tk.StringVar()

tk.Label(root, text="Model File Path:").grid(row=0, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=model_file_path_var, width=50).grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse Model", command=lambda data=model_file_path_var:select_model_file(data)).grid(row=0, column=2, padx=10, pady=10)

tk.Button(root, text="Start Display", command=process_and_display).grid(row=1, column=0, columnspan=3, pady=20)
tk.Button(root, text="Stop LIDAR", command=stop_lidar).grid(row=2, column=0, columnspan=3, pady=20)

# Plot setup
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
plt.ion()  # Turn on interactive mode

root.mainloop()
