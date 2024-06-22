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

for gpu in tf.config.experimental.list_physical_devices('GPU'):
    tf.config.experimental.set_memory_growth(gpu, True)

# Function to parse data from LiDAR and controller files
def parse_data(file_path_lidar, file_path_controller):
    lidar_data = []
    controller_data = []
    with open(file_path_lidar, 'r') as lidar_file, open(file_path_controller, 'r') as controller_file:
        lidar_lines = lidar_file.readlines()
        controller_lines = controller_file.readlines()
        
        for lidar_line, controller_line in zip(lidar_lines, controller_lines):
            data = eval(lidar_line.strip())

            print(f"Data: {data[:3]}")
            
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

            # # Convert to DataFrame for easier manipulation
            # df_interpolated = pd.DataFrame(interpolated_data, columns=["angle", "distance"])

            # # Remove data from 110 to 250 degrees
            # df_interpolated = df_interpolated[(df_interpolated["angle"] < 110) | (df_interpolated["angle"] > 250)]
            
            lidar_data.append(interpolated_data)
            
            controller_line = controller_line.strip()
            controller_data.append(float(controller_line))
            
    lidar_data = np.array(lidar_data, dtype=np.float32)
    controller_data = np.array(controller_data, dtype=np.float32)
    
    print(f"LiDAR data1: {lidar_data[:3]}")

    print(f"Lidar data shape1: {lidar_data.shape}")
    
    # lidar_data = lidar_data / np.max(lidar_data) #######################SCHAU DISCORD ICH HAB DIE NOCH GEADDED FÜR NOMA AUS OARSCH
    lidar_data = np.reshape(lidar_data, (lidar_data.shape[0], lidar_data.shape[1], 2, 1))  # Reshape for CNN input
    
    print(f"LiDAR data2: {lidar_data[:3]}")

    print(f"Lidar data shape2: {lidar_data.shape}")
    
    print(f"Controller data: {controller_data[:3]}")

    return lidar_data, controller_data

# Initialize queue for data communication
data_queue = queue.Queue()
controller_data_queue = queue.Queue()

# Function to select a model file using file dialog
def select_model_file(data):
    path = filedialog.askopenfilename()
    data.set(path)

# Function to select a LiDAR data file using file dialog
def select_lidar_file(data):
    path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    data.set(path)

# Function to select controller data file using file dialog
def select_controller_file(data):
    path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    data.set(path)

# Function to update the display with new data
def update_display(lidar_data, controller_data):
    global model, ax1, ax2, fig, root  # Assuming these are defined elsewhere
    index = 0
    while index < len(lidar_data) and index < len(controller_data):
        
        print("Lidar data: ", lidar_data[index][:3])
        
        expected_output = controller_data[index]
        
        raw_data = lidar_data[index]
        
        # raw data shape (360, 2, 1) -> (None, 360, 2, 1)
        
        model_input = np.expand_dims(raw_data, axis=0)
        
        print(f"Model input shape: {model_input.shape}", model_input[0][:3])
        
        processed_data = pd.DataFrame(raw_data[:, :, 0], columns=["angle", "distance"])
        
        model_output = model.predict(model_input)
        
        print(f"Model output: {model_output[0]}")

        # Visualization code (remains unchanged)
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

        index += 1
        time.sleep(2)  # Simulate the delay between readings
# Function to start processing and displaying data
def process_and_display():
    global model
    model_file_path = model_file_path_var.get()
    controller_file_path = controller_file_path_var.get()
    lidar_file_path = lidar_file_path_var.get()
    model = load_model(model_file_path)

    lidar_data, controller_data = parse_data(lidar_file_path, controller_file_path)
    
    threading.Thread(target=update_display, args=(lidar_data, controller_data)).start()

# Tkinter GUI setup
root = tk.Tk()
root.title("Real-Time LIDAR and Model Output")

model_file_path_var = tk.StringVar()
controller_file_path_var = tk.StringVar()
lidar_file_path_var = tk.StringVar()

tk.Label(root, text="Model File Path:").grid(row=0, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=model_file_path_var, width=50).grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse Model", command=lambda data=model_file_path_var: select_model_file(data)).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="LiDAR File Path:").grid(row=1, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=lidar_file_path_var, width=50).grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Browse LiDAR File", command=lambda data=lidar_file_path_var: select_lidar_file(data)).grid(row=1, column=2, padx=10, pady=10)

tk.Label(root, text="Controller File Path:").grid(row=2, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=controller_file_path_var, width=50).grid(row=2, column=1, padx=10, pady=10)
tk.Button(root, text="Browse Controller File", command=lambda data=controller_file_path_var: select_controller_file(data)).grid(row=2, column=2, padx=10, pady=10)

tk.Button(root, text="Start Display", command=process_and_display).grid(row=3, column=0, columnspan=3, pady=20)

# Plot setup
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
plt.ion()

root.mainloop()
