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
from tensorflow.keras.models import load_model # type: ignore

# Set TensorFlow to allow memory growth on GPU
for gpu in tf.config.experimental.list_physical_devices('GPU'):
    tf.config.experimental.set_memory_growth(gpu, True)

COUNTER_ARRAY_NAMES = ["green_counter", "red_counter"]

# Function to parse data from LiDAR and controller files
def parse_data(file_path_lidar, file_path_controller, file_path_frames, file_path_counters):
    lidar_data = []
    controller_data = []
    
    frame_data = np.load(file_path_frames)
    frames = frame_data['simplified_frames']

    counter_data = np.load(file_path_counters, allow_pickle=True)
    
    green_counter = counter_data[COUNTER_ARRAY_NAMES[0]]
    
    red_counter = counter_data[COUNTER_ARRAY_NAMES[1]]
    
    # print(f"length of green counter: {len(green_counter)}, length of red counter: {len(red_counter)}")
    
    for i, _ in enumerate(green_counter):
        _green_counter = green_counter[i]
        _red_counter = red_counter[i]
        counters = [_green_counter, _red_counter]
        counter_array.append(counters)
        
    counter_array = np.array(counter_array, dtype=np.float32)
    
    with open(file_path_lidar, 'r') as lidar_file, open(file_path_controller, 'r') as controller_file:
        lidar_lines = lidar_file.readlines()
        controller_lines = controller_file.readlines()

        total_lines = len(lidar_lines)
        
        for index, (lidar_line, controller_line) in enumerate(zip(lidar_lines, controller_lines)):
            data = eval(lidar_line.strip())
            
            df = pd.DataFrame(data, columns=["angle", "distance", "intensity"])
            df = df.drop(columns=["intensity"])

            df_interpolated_list = df.values.tolist()  
            
            lidar_data.append(df_interpolated_list)
            
            controller_line = controller_line.strip()
            controller_data.append(float(controller_line))

            progress = (index + 1) / total_lines * 100  # Calculate progress percentage
            print(f"\rProgress: {progress:.2f}%", end="")

        print("\nProcessing complete.")
            
    lidar_data = np.array(lidar_data, dtype=np.float32)
    controller_data = np.array(controller_data, dtype=np.float32)
    
    # Reshape for CNN input
    lidar_data = np.reshape(lidar_data, (lidar_data.shape[0], lidar_data.shape[1], 2, 1))  
    
    return lidar_data, controller_data, frames, counter_array

# Initialize queues for data communication
data_queue = queue.Queue()
controller_data_queue = queue.Queue()
frame_queue = queue.Queue()

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

def select_frames_file(data):
    path = filedialog.askopenfilename(filetypes=[("NPZ files", "*.npz")])
    data.set(path)

def select_counter_file(data):
    path = filedialog.askopenfilename(filetypes=[("NPZ files", "*.npz")])
    data.set(path)

# Function to update the display with new data
def update_display(lidar_data, controller_data, frame_data, counter_array):
    global model, ax1, ax2, ax3, fig, canvas, root, text_output  # Assuming these are defined elsewhere
    index = 0
    accuracy_list = []
    model_output_list = []
    expected_output_list = []
    
    while index < len(lidar_data) and index < len(controller_data) and index < len(frame_data) and index < len(counter_array):
        
        expected_output = controller_data[index]

        expected_output_list.append(expected_output)
        
        raw_lidar_data = lidar_data[index]
        
        raw_frame_data = frame_data[index]
        
        raw_frame_data = raw_frame_data / 255.0

        raw_counter_data = counter_array[index]

        
        processed_data = pd.DataFrame(raw_lidar_data[:, :, 0], columns=["angle", "distance"])
        # Reshape raw data for model input (1, 360, 2, 1)
        model_input_lidar = np.expand_dims(raw_lidar_data, axis=0)
        model_input_frames = np.expand_dims(raw_frame_data, axis=0)
        model_input_counters = np.expand_dims(raw_counter_data, axis=0)
        model_input = [model_input_lidar, model_input_frames, model_input_counters]
        
        # Predict the model output
        model_output = model.predict(model_input)
        current_output = model_output[0][0]  # Assuming single output, adjust as needed
        print(f"Model Output: {current_output}, Expected Output: {expected_output}")
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

            ax3.clear()
            ax3.imshow(raw_frame_data, cmap='gray')
            ax3.set_title('Frame Data')
            ax3.axis('off')

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
        # update_plots()
        root.update()
        root.update_idletasks()

        
        index += 1
        time.sleep(0.1)  # Simulate the delay between readings

def process_and_display():
    global model
    model_file_path = model_file_path_var.get()
    controller_file_path = controller_file_path_var.get()
    lidar_file_path = lidar_file_path_var.get()
    frame_file_path = frame_file_path_var.get()
    model = load_model(model_file_path)

    lidar_data, controller_data, frames = parse_data(lidar_file_path, controller_file_path, frame_file_path)
    
    threading.Thread(target=update_display, args=(lidar_data, controller_data, frames)).start()

# Tkinter GUI setup
root = tk.Tk()
root.title("Real-Time LIDAR and Model Output")

model_file_path_var = tk.StringVar()
controller_file_path_var = tk.StringVar()
lidar_file_path_var = tk.StringVar()
frame_file_path_var = tk.StringVar()
counter_file_path_var = tk.StringVar()

tk.Label(root, text="Model File Path:").grid(row=0, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=model_file_path_var, width=50).grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse Model", command=lambda data=model_file_path_var: select_model_file(data)).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="LiDAR File Path:").grid(row=1, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=lidar_file_path_var, width=50).grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Browse LiDAR File", command=lambda data=lidar_file_path_var: select_lidar_file(data)).grid(row=1, column=2, padx=10, pady=10)

tk.Label(root, text="Controller File Path:").grid(row=2, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=controller_file_path_var, width=50).grid(row=2, column=1, padx=10, pady=10)
tk.Button(root, text="Browse Controller File", command=lambda data=controller_file_path_var: select_controller_file(data)).grid(row=2, column=2, padx=10, pady=10)

tk.Label(root, text="Frames File Path:").grid(row=3, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=frame_file_path_var, width=50).grid(row=3, column=1, padx=10, pady=10)
tk.Button(root, text="Browse Frames File", command=lambda data=frame_file_path_var: select_frames_file(data)).grid(row=3, column=2, padx=10, pady=10)

tk.Label(root, text="Counter File Path:").grid(row=4, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=counter_file_path_var, width=50).grid(row=4, column=1, padx=10, pady=10)
tk.Button(root, text="Browse Counter File", command=lambda data=counter_file_path_var: select_counter_file(data)).grid(row=4, column=2, padx=10, pady=10)

tk.Button(root, text="Start Display", command=process_and_display).grid(row=5, column=0, columnspan=3, pady=20)


# Plot setup
fig = plt.figure(figsize=(18, 6))
ax1 = fig.add_subplot(131, polar=True)  # Polar plot for LIDAR data
ax2 = fig.add_subplot(132)  # Regular plot for model vs expected output
ax3 = fig.add_subplot(133)  # Third subplot

# Adjust the spacing between subplots
plt.subplots_adjust(wspace=0.3, hspace=0.3)  # Adjust these values as needed


# Text output for numerical values
text_output = tk.Text(root, height=6, width=80, state=tk.DISABLED)
text_output.grid(row=6, column=0, columnspan=3, padx=10, pady=10)

canvas = FigureCanvasTkAgg(fig, master=root)  # Create a canvas
canvas.get_tk_widget().grid(row=7, column=0, columnspan=3)
plt.ion()

root.mainloop()
