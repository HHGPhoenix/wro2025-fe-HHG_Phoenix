import tkinter as tk
from tkinter import filedialog
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import numpy as np
import matplotlib.pyplot as plt
import uuid
import os
import pandas as pd
from scipy.interpolate import interp1d

# Print all GPU devices
print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))

for gpu in tf.config.experimental.list_physical_devices('GPU'):
    tf.config.experimental.set_memory_growth(gpu, True)

def select_data_file(data):
    path = filedialog.askopenfilename()
    data.set(path)

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
            
            lidar_data.append(interpolated_data)
            
            controller_line = controller_line.strip()
            controller_data.append(float(controller_line))
            
    lidar_data = np.array(lidar_data, dtype=np.float32)
    controller_data = np.array(controller_data, dtype=np.float32)

    print(f"Controller data: {controller_data[:10]}")

    return lidar_data, controller_data

def plot_training_history(history, model_id):
    plt.figure(figsize=(12, 4))
    plt.subplot(1, 2, 1)
    plt.plot(history.history['mae'])
    plt.plot(history.history['val_mae'])
    plt.title('Model MAE')
    plt.ylabel('MAE')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper left')

    plt.subplot(1, 2, 2)
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model Loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper left')

    plt.savefig(f'training_history_{model_id}.png')
    plt.show()

def start_training():
    try:
        LIDAR_file_path = data_file_path_LIDAR.get()
        controller_file_path = data_file_path_controller.get()

        print(f"LIDAR file path: {LIDAR_file_path}")

        print(f"Controller file path: {controller_file_path}")

        # Load and parse data
        lidar_data, controller_data = parse_data(LIDAR_file_path, controller_file_path)

        print(f"LIDAR data shape: {lidar_data.shape}")

        print(f"Controller data shape: {controller_data.shape}")

        # print first ten data points
        print(f"LIDAR data: {lidar_data[:10]}")

        # Preprocess LIDAR data to fit the model input
        # Normalizing and reshaping the data
        lidar_data = lidar_data / np.max(lidar_data)  # Normalize
        lidar_data = np.reshape(lidar_data, (lidar_data.shape[0], lidar_data.shape[1], 2, 1))  # Reshape for CNN input

        # Split data into training and validation sets
        split_idx = int(0.8 * len(lidar_data))
        train_lidar, val_lidar = lidar_data[:split_idx], lidar_data[split_idx:]
        train_controller, val_controller = controller_data[:split_idx], controller_data[split_idx:]

        # Define the model
        model = Sequential([
            Conv2D(64, (3, 2), activation='relu', input_shape=(lidar_data.shape[1], lidar_data.shape[2], 1)),  # Adjusted kernel size
            MaxPooling2D((2, 1)),  # Adjusted pool size
            Conv2D(64, (1, 1), activation='relu'),
            MaxPooling2D((2, 1)),  # Adjusted pool size
            Flatten(),
            Dense(128, activation='relu'),
            Dropout(0.3),
            Dense(1, activation='linear')  # Output for the servo control
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])

        # Generate a unique ID for the model
        model_id = str(uuid.uuid4())

        # Early stopping and model checkpoint
        early_stopping = EarlyStopping(monitor='val_loss', patience=10)
        model_checkpoint = ModelCheckpoint(f'best_model_{model_id}.h5', monitor='val_loss', save_best_only=True)

        # Train the model
        history = model.fit(
            train_lidar, train_controller,
            validation_data=(val_lidar, val_controller),
            epochs=200,
            callbacks=[early_stopping, model_checkpoint],
            batch_size=32
        )

        # Load the best model
        best_model = tf.keras.models.load_model(f'best_model_{model_id}.h5')

        # Evaluate the model
        loss, mae = best_model.evaluate(val_lidar, val_controller)
        print(f'Validation Mean Absolute Error: {mae:.4f}')

        # Save the model with the MAE in the filename
        model_filename = f'cube_classifier_{model_id}_{mae:.2f}.h5'
        best_model.save(model_filename)

        # Plot and save training history
        plot_training_history(history, model_id)

    except Exception as e:
        print(f"An error occurred: {e}")

# Tkinter GUI setup
root = tk.Tk()
root.title("Train Model")

data_file_path_LIDAR = tk.StringVar()
data_file_path_controller = tk.StringVar()

tk.Label(root, text="LIDAR File Path:").grid(row=0, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=data_file_path_LIDAR, width=50).grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse LIDAR", command=lambda data=data_file_path_LIDAR: select_data_file(data)).grid(row=0, column=2, padx=10, pady=10)

tk.Label(root, text="Controller File Path:").grid(row=1, column=0, padx=10, pady=10)
tk.Entry(root, textvariable=data_file_path_controller, width=50).grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Browse Controller", command=lambda data=data_file_path_controller: select_data_file(data)).grid(row=1, column=2, padx=10, pady=10)

tk.Button(root, text="Start Training", command=start_training).grid(row=2, column=0, columnspan=3, pady=20)

root.mainloop()
