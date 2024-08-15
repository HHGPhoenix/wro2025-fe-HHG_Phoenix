import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import matplotlib
matplotlib.use('TkAgg')  # Set the backend for matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from scipy.interpolate import interp1d

def parse_data(file_path_lidar, file_path_controller):
    lidar_data = []
    controller_data = []
    try:
        with open(file_path_lidar, 'r') as lidar_file, open(file_path_controller, 'r') as controller_file:
            lidar_lines = lidar_file.readlines()
            controller_lines = controller_file.readlines()

            if len(lidar_lines) != len(controller_lines):
                raise ValueError("LiDAR and controller files must have the same number of lines.")

            for lidar_line, controller_line in zip(lidar_lines, controller_lines):
                data = eval(lidar_line.strip())
                df = pd.DataFrame(data, columns=["angle", "distance", "intensity"]).drop(columns=["intensity"])
                df = df[(df["distance"] != 0)]
                df["angle"] = (df["angle"] - 90) % 360
                df = df.sort_values("angle")

                desired_angles = np.arange(0, 360, 1)
                interp_distance = interp1d(df["angle"], df["distance"], kind="linear", bounds_error=False, fill_value="extrapolate")
                interpolated_distances = interp_distance(desired_angles)
                df_interpolated = pd.DataFrame(list(zip(desired_angles, interpolated_distances)), columns=["angle", "distance"])
                df_interpolated = df_interpolated[(df_interpolated["angle"] < 110) | (df_interpolated["angle"] > 250)]
                lidar_data.append(df_interpolated.values.tolist())
                controller_data.append(float(controller_line.strip()))

        lidar_data = np.array(lidar_data, dtype=np.float32)
        controller_data = np.array(controller_data, dtype=np.float32)
        lidar_data = np.reshape(lidar_data, (lidar_data.shape[0], lidar_data.shape[1], 2, 1))  
    except Exception as e:
        messagebox.showerror("Error", f"Error parsing data: {e}")
    return lidar_data, controller_data

def select_file(data, filetypes):
    path = filedialog.askopenfilename(filetypes=filetypes)
    if path:
        data.set(path)

def display_data(lidar_data, controller_data, start_idx, end_idx):
    global ax1, canvas, text_output, fig
    
    fig.clf()
    ax1 = fig.add_subplot(111, polar=True)

    for idx in range(start_idx, end_idx):
        raw_data = lidar_data[idx]
        processed_data = pd.DataFrame(raw_data[:, :, 0], columns=["angle", "distance"])
        ax1.scatter(np.deg2rad(processed_data["angle"]), processed_data["distance"], s=3)

    ax1.set_title('LIDAR Data (Polar Plot)')
    ax1.grid(True)
    canvas.draw()

def update_display():
    global lidar_data, controller_data, start_idx, end_idx
    try:
        start_idx = int(start_entry.get())
        end_idx = int(end_entry.get())

        if start_idx < 0 or end_idx >= len(lidar_data) or start_idx >= end_idx:
            raise ValueError("Invalid range for display.")
        
        display_data(lidar_data, controller_data, start_idx, end_idx)
    except Exception as e:
        messagebox.showerror("Error", f"Error updating display: {e}")

def cut_data():
    global lidar_data, controller_data, start_idx, end_idx
    try:
        start_idx = int(start_entry.get())
        end_idx = int(end_entry.get())

        if start_idx < 0 or end_idx >= len(lidar_data) or start_idx >= end_idx:
            raise ValueError("Invalid range for cutting.")

        lidar_data = np.delete(lidar_data, slice(start_idx, end_idx+1), axis=0)
        controller_data = np.delete(controller_data, slice(start_idx, end_idx+1), axis=0)
        messagebox.showinfo("Info", "Data cut successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Error cutting data: {e}")

# Tkinter GUI setup
root = tk.Tk()
root.title("LiDAR Data Editor")

model_file_path_var = tk.StringVar()
controller_file_path_var = tk.StringVar()
lidar_file_path_var = tk.StringVar()

tk.Label(root, text="LiDAR File Path:").grid(row=0, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=lidar_file_path_var, width=50).grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse LiDAR File", command=lambda: select_file(lidar_file_path_var, [("Text files", "*.txt")])).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="Controller File Path:").grid(row=1, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=controller_file_path_var, width=50).grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Browse Controller File", command=lambda: select_file(controller_file_path_var, [("Text files", "*.txt")])).grid(row=1, column=2, padx=10, pady=10)

tk.Button(root, text="Load Data", command=lambda: parse_data(lidar_file_path_var.get(), controller_file_path_var.get())).grid(row=2, column=0, columnspan=3, pady=20)

tk.Label(root, text="Display Range (start:end):").grid(row=3, column=0, padx=10, pady=10)
start_entry = tk.Entry(root, width=10)
start_entry.grid(row=3, column=1, padx=5, pady=10, sticky='w')
tk.Label(root, text=":").grid(row=3, column=1, padx=0, pady=10)
end_entry = tk.Entry(root, width=10)
end_entry.grid(row=3, column=1, padx=5, pady=10, sticky='e')
tk.Button(root, text="Update Display", command=update_display).grid(row=3, column=2, padx=10, pady=10)

tk.Button(root, text="Cut Data", command=cut_data).grid(row=4, column=0, columnspan=3, pady=20)

# Plot setup
fig = plt.figure(figsize=(8, 6))
ax1 = fig.add_subplot(111, polar=True)
canvas = FigureCanvasTkAgg(fig, master=root)  
canvas.get_tk_widget().grid(row=5, column=0, columnspan=3)
plt.ion()

root.mainloop()
