import tkinter as tk
from tkinter import filedialog
import tensorflow as tf
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Set the backend for matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from scipy.interpolate import interp1d
import time
import threading
import queue
from tensorflow.keras.models import load_model

# Set TensorFlow to allow memory growth on GPU
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

            df_interpolated_list = df_interpolated.values.tolist()  
            
            lidar_data.append(df_interpolated_list)
            
            controller_line = controller_line.strip()
            controller_data.append(float(controller_line))
            
    lidar_data = np.array(lidar_data, dtype=np.float32)
    controller_data = np.array(controller_data, dtype=np.float32)
    
    # Reshape for CNN input
    lidar_data = np.reshape(lidar_data, (lidar_data.shape[0], lidar_data.shape[1], 2, 1))  
    
    return lidar_data, controller_data

# Initialize queues for data communication
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
    global model, ax1, ax2, ax3, fig, canvas, root, text_output  # Assuming these are defined elsewhere
    index = 0
    accuracy_list = []
    model_output_list = []
    expected_output_list = []
    
    while index < len(lidar_data) and index < len(controller_data):
        
        expected_output = controller_data[index]

        expected_output_list.append(expected_output)
        
        raw_data = lidar_data[index]
        
        # Reshape raw data for model input (1, 360, 2, 1)
        model_input = np.expand_dims(raw_data, axis=0)
        
        processed_data = pd.DataFrame(raw_data[:, :, 0], columns=["angle", "distance"])
        
        # Predict the model output
        model_output = model.predict(model_input)
        current_output = model_output[0][0]  # Assuming single output, adjust as needed

        model_output_list.append(current_output)
        
        # Calculate the accuracy as the difference percentage
        current_accuracy = 100 * (1 - abs((current_output - expected_output) / expected_output))
        accuracy_list.append(current_accuracy)
        
        # Calculate average accuracy over the last 100 runs
        if len(accuracy_list) > 100:
            accuracy_list.pop(0)
        avg_accuracy = np.mean(accuracy_list)

        if len(model_output_list) > 300:
            model_output_list.pop(0)
            expected_output_list.pop(0)
        
        def update_plots():
            ax1.clear()
            ax1.set_xlim(0, 2 * np.pi)  # Angular limits in radians
            ax1.scatter(np.deg2rad(processed_data["angle"]), processed_data["distance"], s=3)
            ax1.set_title('LIDAR Data (Polar Plot)')
            ax1.grid(True)

            ax2.clear()
            ax2.plot(model_output_list, label='Model Output', color='blue')
            ax2.plot(expected_output_list, label='Expected Output', color='green')
            ax2.set_ylim(0, 1)  # Set y-axis limits from 0 to 1
            ax2.legend()
            ax2.set_title('Model vs Expected Output')
            ax2.grid(True)

            # Update the text output for the controller and model values
            text_output.config(state=tk.NORMAL)
            text_output.delete("1.0", tk.END)
            text_output.insert(tk.END, f"Controller Value: {expected_output}\n")
            text_output.insert(tk.END, f"Model Output: {current_output}\n")
            text_output.insert(tk.END, f"Current Accuracy: {current_accuracy:.2f}%\n")
            text_output.insert(tk.END, f"Average Accuracy (last 100): {avg_accuracy:.2f}%\n")
            text_output.config(state=tk.DISABLED)
            
            canvas.draw()
        
        root.after(0, update_plots)

        
        index += 1
        time.sleep(0.1)  # Simulate the delay between readings

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
fig = plt.figure(figsize=(12, 6))
ax1 = fig.add_subplot(121, polar=True)  # Polar plot for LIDAR data
ax2 = fig.add_subplot(122)  # Regular plot for model vs expected output

# Text output for numerical values
text_output = tk.Text(root, height=5, width=80, state=tk.DISABLED)
text_output.grid(row=4, column=0, columnspan=3, padx=10, pady=10)

canvas = FigureCanvasTkAgg(fig, master=root)  # Create a canvas
canvas.get_tk_widget().grid(row=5, column=0, columnspan=3)
plt.ion()

root.mainloop()
