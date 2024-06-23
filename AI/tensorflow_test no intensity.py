import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization, LeakyReLU
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import numpy as np
import matplotlib.pyplot as plt
import uuid
import os
import pandas as pd
from scipy.interpolate import interp1d
import random
from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

if __name__ == "__main__":
    # Print all GPU devices
    print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))

    for gpu in tf.config.experimental.list_physical_devices('GPU'):
        tf.config.experimental.set_memory_growth(gpu, True)

def select_data_folder(data):
    path = filedialog.askdirectory()
    data.set(path)

@lru_cache(maxsize=111111)
def parse_data(file_path_lidar, file_path_controller, progress_callback=None, progress_callbacks=None, idx=None):
    lidar_data = []
    controller_data = []
    with open(file_path_lidar, 'r') as lidar_file, open(file_path_controller, 'r') as controller_file:
        lidar_lines = lidar_file.readlines()
        controller_lines = controller_file.readlines()

        total_lines = len(lidar_lines)
        
        for index, (lidar_line, controller_line) in enumerate(zip(lidar_lines, controller_lines)):
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

            # Calculate progress
            if progress_callback:
                progress = (index + 1) / total_lines * 100
                progress_callback(progress, idx, progress_callbacks)

    lidar_data = np.array(lidar_data, dtype=np.float32)
    controller_data = np.array(controller_data, dtype=np.float32)

    return lidar_data, controller_data

def parse_data_with_callback(args):
    file_pair, index, progress_callbacks, progress_callback = args
    # Convert progress_callbacks to a tuple if it's being used in a hash-requiring context
    progress_callbacks_hashable = tuple(progress_callbacks) if progress_callbacks else None
    file_path_lidar, file_path_controller = file_pair
    lidar_data, controller_data = parse_data(file_path_lidar, file_path_controller, progress_callback=progress_callback, progress_callbacks=progress_callbacks_hashable, idx = index)
    return lidar_data, controller_data

def load_data_from_folder(folder_path, progress_callback, progress_callbacks):
    train_lidar_data = []
    train_controller_data = []
    val_lidar_data = []
    val_controller_data = []
    file_pairs = []
    for subdir, _, files in os.walk(folder_path):
        lidar_file = None
        controller_file = None
        for file in files:
            if file.startswith('lidar_'):
                lidar_file = os.path.join(subdir, file)
            elif file.startswith('x_'):
                controller_file = os.path.join(subdir, file)
        if lidar_file and controller_file:
            file_pairs.append((lidar_file, controller_file))
    total_files = len(file_pairs)
    results = []

    with ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
        future_to_file = {
            executor.submit(parse_data_with_callback, (file_pair, i, progress_callbacks, progress_callback)): file_pair
            for i, file_pair in enumerate(file_pairs)
        }
        for future in as_completed(future_to_file):
            lidar_data, controller_data = future.result()
            results.append((lidar_data, controller_data))

    for lidar_data, controller_data in results:
        if len(lidar_data) > 0 and len(controller_data) > 0:
            data_length = len(lidar_data)
            indices = list(range(data_length))
            random.shuffle(indices)
            split_idx = int(0.8 * data_length)
            train_indices = indices[:split_idx]
            val_indices = indices[split_idx:]
            train_lidar_data.append(lidar_data[train_indices])
            train_controller_data.append(controller_data[train_indices])
            val_lidar_data.append(lidar_data[val_indices])
            val_controller_data.append(controller_data[val_indices])

    if len(train_lidar_data) > 0:
        train_lidar_data = np.concatenate(train_lidar_data, axis=0)
        train_controller_data = np.concatenate(train_controller_data, axis=0)
    else:
        train_lidar_data = np.array([])
        train_controller_data = np.array([])

    if len(val_lidar_data) > 0:
        val_lidar_data = np.concatenate(val_lidar_data, axis=0)
        val_controller_data = np.concatenate(val_controller_data, axis=0)
    else:
        val_lidar_data = np.array([])
        val_controller_data = np.array([])

    return train_lidar_data, train_controller_data, val_lidar_data, val_controller_data

def plot_training_history(history, model_id, custom_filename=None):
    plt.figure(figsize=(12, 8))  # Increased figure size for better readability
    plt.subplot(2, 1, 1)  # Adjusted for additional text space
    plt.plot(history.history['mae'])
    plt.plot(history.history['val_mae'])
    plt.title('Model MAE')
    plt.ylabel('MAE')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper left')

    plt.subplot(2, 1, 2)  # Adjusted for additional text space
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model Loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper left')

    # Calculate final statistics
    final_mae = history.history['mae'][-1]
    final_val_mae = history.history['val_mae'][-1]
    final_loss = history.history['loss'][-1]
    final_val_loss = history.history['val_loss'][-1]

    # Add text for final statistics
    plt.figtext(0.5, 0.01, f'Final MAE: {final_mae:.4f}, Final Val MAE: {final_val_mae:.4f}, '
                           f'Final Loss: {final_loss:.4f}, Final Val Loss: {final_val_loss:.4f}',
                ha="center", fontsize=9, bbox={"facecolor":"orange", "alpha":0.5, "pad":5})

    if custom_filename:
        plt.savefig(f'training_history_{custom_filename}.png')
    else:
        plt.savefig(f'training_history_{model_id}.png')
    plt.show()

def create_progress_window(file_pairs):
    progress_window = tk.Toplevel()
    progress_window.title("Loading Progress")
    progress_bars = []

    for i, (lidar_file, controller_file) in enumerate(file_pairs):
        # Extract the last directory and file name for lidar_file
        lidar_dir, lidar_name = os.path.split(lidar_file)
        _, lidar_last_dir = os.path.split(lidar_dir)
        lidar_display = os.path.join(lidar_last_dir, lidar_name)

        # Extract the last directory and file name for controller_file
        controller_dir, controller_name = os.path.split(controller_file)
        _, controller_last_dir = os.path.split(controller_dir)
        controller_display = os.path.join(controller_last_dir, controller_name)

        frame = ttk.Frame(progress_window)
        frame.pack(pady=5)

        label_text = f"File Pair {i+1}: {lidar_display}, {controller_display}"
        label = ttk.Label(frame, text=label_text)
        label.pack(side=tk.LEFT, padx=10)

        progress_bar = ttk.Progressbar(frame, orient='horizontal', length=300, mode='determinate')
        progress_bar.pack(side=tk.RIGHT, padx=10)
        progress_bars.append(progress_bar)

    return progress_window, progress_bars

def progress_callback(progress, index, progress_callbacks):
    # Check if index is within the range of progress_callbacks
    if 0 <= index < len(progress_callbacks):
        root.after(0, lambda: progress_callbacks[index](progress))  # Update the progress bar in the GUI
    else:
        print(f"Error: Index {index} is out of range for progress_callbacks with length {len(progress_callbacks)}")
        # Handle the error appropriately, e.g., adjust index or skip the update
        # For example, setting index to a default value (like 0) or the last valid index
        # index = max(0, min(index, len(progress_callbacks) - 1))
        # root.after(0, lambda: progress_callbacks[index](progress))
    root.update()
    root.update_idletasks()
    print(f"Progress: {progress:.2f}% for index {index}")

def start_training_thread():
    Thread(target=start_training).start()

def start_training():
    try:
        folder_path = data_folder_path.get()
        custom_filename = model_filename.get()

        print(f"Selected folder path: {folder_path}")

        file_pairs = []
        for subdir, _, files in os.walk(folder_path):
            lidar_file = None
            controller_file = None
            for file in files:
                if file.startswith('lidar_'):
                    lidar_file = os.path.join(subdir, file)
                elif file.startswith('x_'):
                    controller_file = os.path.join(subdir, file)
            if lidar_file and controller_file:
                file_pairs.append((lidar_file, controller_file))

        # Create progress window
        progress_window, progress_bars = create_progress_window(file_pairs)
        progress_callbacks = [lambda progress, pb=pb: pb.config(value=progress) for pb in progress_bars]

        root.update()

        # Load and parse data
        train_lidar, train_controller, val_lidar, val_controller = load_data_from_folder(folder_path, progress_callback, progress_callbacks)

        if train_lidar.size == 0 or train_controller.size == 0 or val_lidar.size == 0 or val_controller.size == 0:
            print("No valid data found for training or validation.")
            return

        print(f"Train LIDAR data shape: {train_lidar.shape}")
        print(f"Train Controller data shape: {train_controller.shape}")
        print(f"Validation LIDAR data shape: {val_lidar.shape}")
        print(f"Validation Controller data shape: {val_controller.shape}")

        # Preprocess LIDAR data to fit the model input
        train_lidar = np.reshape(train_lidar, (train_lidar.shape[0], train_lidar.shape[1], 2, 1))  # Reshape for CNN input
        val_lidar = np.reshape(val_lidar, (val_lidar.shape[0], val_lidar.shape[1], 2, 1))  # Reshape for CNN input


        # Define the model
        model = Sequential([
            Conv2D(128, (3, 2), activation='linear', input_shape=(train_lidar.shape[1], train_lidar.shape[2], 1)),
            BatchNormalization(),  # Added batch normalization
            MaxPooling2D((2, 1)),
            Conv2D(128, (1, 1), activation='linear'),
            BatchNormalization(),  # Added batch normalization
            MaxPooling2D((2, 1)),
            Flatten(),
            Dense(64, activation=LeakyReLU(alpha=0.05)),
            Dropout(0.3),
            Dense(1, activation='linear')  # Output for the servo control
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])

        # Generate a unique ID for the model
        model_id = str(uuid.uuid4())

        # Early stopping and model checkpoint
        early_stopping = EarlyStopping(monitor='val_loss', patience=35)  # Reduced patience

        checkpoint_filename = f"best_model_{custom_filename}.h5" if custom_filename else f'best_model_{model_id}.h5'
        model_checkpoint = ModelCheckpoint(checkpoint_filename, monitor='val_loss', save_best_only=True)

        # Train the model
        history = model.fit(
            train_lidar, train_controller,
            validation_data=(val_lidar, val_controller),
            epochs=300,
            callbacks=[early_stopping, model_checkpoint],
            batch_size=32
        )

        # Load the best model
        best_model = tf.keras.models.load_model(checkpoint_filename)

        # Evaluate the model
        loss, mae = best_model.evaluate(val_lidar, val_controller)
        print(f'Validation Mean Absolute Error: {mae:.4f}')
        
        # Save the model with the MAE in the filename
        final_model_filename = f'best_model_{custom_filename}_{mae:.4f}.h5' if custom_filename else f'best_model_{model_id}_{mae:.4f}.h5'
        best_model.save(final_model_filename)

        # delete the temporary best model
        os.remove(checkpoint_filename)

        # Plot and save training history
        plot_training_history(history, model_id, custom_filename)

    except StopIteration:
        print("Training stopped by user.")


if __name__ == "__main__":
    # Tkinter GUI setup
    root = tk.Tk()
    root.title("Train Model")

    data_folder_path = tk.StringVar()
    model_filename = tk.StringVar()

    tk.Label(root, text="Data Folder Path:").grid(row=0, column=0, padx=10, pady=10)
    tk.Entry(root, textvariable=data_folder_path, width=50).grid(row=0, column=1, padx=10, pady=10)
    tk.Button(root, text="Browse Folder", command=lambda data=data_folder_path: select_data_folder(data)).grid(row=0, column=2, padx=10, pady=10)

    tk.Label(root, text="Model Filename (optional):").grid(row=1, column=0, padx=10, pady=10)
    tk.Entry(root, textvariable=model_filename, width=50).grid(row=1, column=1, padx=10, pady=10)

    tk.Button(root, text="Start Training", command=start_training_thread).grid(row=2, column=0, columnspan=3, pady=20)

    root.mainloop()
