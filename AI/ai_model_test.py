import tkinter as tk
from tkinter import filedialog
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d
import json
import time
import threading
import queue
from tensorflow.keras.models import load_model  # type: ignore

# Initialize queue for data communication
data_queue = queue.Queue()
controller_data_queue = queue.Queue()

# Function to select a model file using file dialog
def select_model_file(data):
    path = filedialog.askopenfilename()
    data.set(path)

# Function to select a LiDAR data file using file dialog
def select_lidar_file(data):
    path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    data.set(path)

# Function to select controller data file using file dialog
def select_controller_file(data):
    path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    data.set(path)

# Function to read LiDAR data from JSON file
def read_lidar_data_from_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        for entry in data:
            data_queue.put(entry)
            time.sleep(2)  # Simulate the delay between readings

# Function to read controller data from JSON file
def read_controller_data(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        for entry in data:
            controller_data_queue.put(entry)
            time.sleep(2)  # Simulate the delay between readings

# Function to interpolate and process LiDAR data
def process_lidar_data(raw_data):
    df = pd.DataFrame(raw_data, columns=["angle", "distance", "intensity"])
    df = df.drop(columns=["intensity"])
    df = df[(df["distance"] != 0)]
    df["angle"] = (df["angle"] - 90) % 360
    df = df.sort_values("angle")
    desired_angles = np.arange(0, 360, 1)
    interp_distance = interp1d(df["angle"], df["distance"], kind="linear", bounds_error=False, fill_value=(df["distance"].iloc[0], df["distance"].iloc[-1]))
    interpolated_distances = interp_distance(desired_angles)
    interpolated_data = list(zip(desired_angles, interpolated_distances))
    df_interpolated = pd.DataFrame(interpolated_data, columns=["angle", "distance"])
    df_interpolated = df_interpolated[(df_interpolated["angle"] < 110) | (df_interpolated["angle"] > 250)]
    return df_interpolated

# Function to update the display with new data
def update_display():
    global model
    while not data_queue.empty() and not controller_data_queue.empty():
        raw_data = data_queue.get()
        expected_output = controller_data_queue.get()
        processed_data = process_lidar_data(raw_data)
        model_input = np.expand_dims(processed_data['distance'].values, axis=0)
        model_input = np.expand_dims(model_input, axis=-1)
        model_output = model.predict(model_input)

        ax1.clear()
        ax1.scatter(processed_data["angle"], processed_data["distance"], s=3)
        ax1.set_title('LIDAR Data')
        ax1.set_xlabel('Angle (degrees)')
        ax1.set_ylabel('Distance')
        ax1.grid(True)

        ax2.clear()
        ax2.plot(model_output[0], label='Model Output', color='blue')
        ax2.plot([expected_output] * len(model_output[0]), label='Expected Output', color='green')
        ax2.legend()
        ax2.set_title('Model vs Expected Output')
        ax2.set_xlabel('Sample Index')
        ax2.set_ylabel('Output Value')
        ax2.grid(True)

        fig.canvas.draw()
        root.update_idletasks()
        root.update()

    root.after(2000, update_display)

# Function to start processing and displaying data
def process_and_display():
    global model
    model_file_path = model_file_path_var.get()
    controller_file_path = controller_file_path_var.get()
    lidar_file_path = lidar_file_path_var.get()
    model = load_model(model_file_path)

    threading.Thread(target=read_controller_data, args=(controller_file_path,)).start()
    threading.Thread(target=read_lidar_data_from_file, args=(lidar_file_path,)).start()
    update_display()

# Tkinter GUI setup
root = tk.Tk()
root.title("Real-Time LIDAR and Model Output")

model_file_path_var = tk.StringVar()
controller_file_path_var = tk.StringVar()
lidar_file_path_var = tk.StringVar()

tk.Label(root, text="Model File Path:").grid(row=0, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=model_file_path_var, width=50).grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse Model", command=lambda data=model_file_path_var: select_model_file(data)).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="Controller File Path:").grid(row=1, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=controller_file_path_var, width=50).grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Browse Controller File", command=lambda data=controller_file_path_var: select_controller_file(data)).grid(row=1, column=2, padx=10, pady=10)

tk.Label(root, text="LiDAR File Path:").grid(row=2, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=lidar_file_path_var, width=50).grid(row=2, column=1, padx=10, pady=10)
tk.Button(root, text="Browse LiDAR File", command=lambda data=lidar_file_path_var: select_lidar_file(data)).grid(row=2, column=2, padx=10, pady=10)

tk.Button(root, text="Start Display", command=process_and_display).grid(row=3, column=0, columnspan=3, pady=20)

# Plot setup
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
plt.ion()

root.mainloop()
