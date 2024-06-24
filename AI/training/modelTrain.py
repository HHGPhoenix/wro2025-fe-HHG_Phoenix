import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import tensorflow as tf
from tensorflow.keras.models import Sequential # type: ignore
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout, BatchNormalization, LeakyReLU # type: ignore
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, Callback # type: ignore
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
import time
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

global custom_filename, model_filename, model_id, MODEL, EPOCHS, PATIENCE, BATCH_SIZE

train_lidar = None
train_controller = None
val_lidar = None
val_controller = None

custom_filename = None

train_lidar = None
train_controller = None
val_lidar = None
val_controller = None

##############################################################################################

EPOCHS = 300

PATIENCE = 35

BATCH_SIZE = 32

##############################################################################################

def create_model(input_shape):
    model = Sequential([
        Conv2D(128, (3, 2), activation=LeakyReLU(alpha=0.05), input_shape=input_shape),
        BatchNormalization(),
        MaxPooling2D((2, 1)),
        Conv2D(128, (1, 1), activation=LeakyReLU(alpha=0.05)),
        BatchNormalization(),
        MaxPooling2D((2, 1)),
        Flatten(),
        Dense(64, activation=LeakyReLU(alpha=0.05)),
        Dropout(0.3),
        Dense(1, activation='linear')
    ])
    return model


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

class ConsoleAndGUIProgressCallback(Callback):
    def __init__(self):
        super().__init__()
        self.progress_window = None
        self.progress_bars = []
        self.text_display = None
        self.figure = None
        self.canvas = None
        
        self.loss_values = []  # Track latest 150 loss values
        self.val_loss_values = []  # Track latest 150 validation loss values
        self.mae_values = []  # Track latest 150 mae values for each epoch
        self.val_mae_values = []  # Track latest 150 validation mae values for each epoch

        self.full_loss_values = []  # Store complete history of loss values
        self.full_val_loss_values = []  # Store complete history of validation loss values
        self.full_mae_values = []  # Store complete history of mae values
        self.full_val_mae_values = []  # Store complete history of validation mae values
        
        self.lowest_val_mae = float('inf')
        self.lowest_val_mae_epoch = -1
        self.highest_loss = float('-inf')
        self.lowest_loss = float('inf')
        
        self.create_tensorflow_progress_window()
        print("Progress window created.")
        
        
    def create_tensorflow_progress_window(self):
        self.progress_window = tk.Toplevel(root)
        self.progress_window.title("Training Progress")

        # Textual display of progress
        self.text_display = tk.Text(self.progress_window, height=10, width=80)
        self.text_display.pack()

        # Primary Progress Bar
        self.progress_bars = []
        pb = ttk.Progressbar(self.progress_window, orient="horizontal", length=200, mode="determinate")
        pb.pack()
        self.progress_bars.append(pb)

        # Secondary Progress Bar (Red, for remaining patience)
        self.secondary_pb = ttk.Progressbar(self.progress_window, orient="horizontal", length=200, mode="determinate")
        self.secondary_pb.pack()
        self.secondary_pb_style = ttk.Style()
        self.secondary_pb_style.configure("Red.Horizontal.TProgressbar", troughcolor='white', background='red')
        self.secondary_pb.configure(style="Red.Horizontal.TProgressbar")

        # Initialize secondary progress bar (patience countdown)
        self.secondary_pb['maximum'] = PATIENCE
        self.secondary_pb['value'] = PATIENCE

        # Close button
        close_button = tk.Button(self.progress_window, text="Close", command=self.progress_window.destroy)
        close_button.pack()

        # Matplotlib figure for plots
        self.figure = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.progress_window)
        self.canvas.get_tk_widget().pack()

        # Labels for displaying highest and lowest values with larger font
        self.highest_loss_label = tk.Label(self.progress_window, text="Highest Loss: N/A", font=("Helvetica", 14))
        self.highest_loss_label.pack()
        self.lowest_loss_label = tk.Label(self.progress_window, text="Lowest Loss: N/A", font=("Helvetica", 14))
        self.lowest_loss_label.pack()
        self.lowest_val_mae_label = tk.Label(self.progress_window, text="Lowest Validation MAE: N/A", font=("Helvetica", 14))
        self.lowest_val_mae_label.pack()
        self.lowest_val_mae_epoch_label = tk.Label(self.progress_window, text="Epoch for Lowest Validation MAE: N/A", font=("Helvetica", 14))
        self.lowest_val_mae_epoch_label.pack()

        # Track the epoch of the last best validation MAE
        self.last_best_epoch = 0

    def safe_update_gui(self, epoch, logs):
        # Update console message to include new stats
        console_message = f"Epoch {epoch+1}/{self.params['epochs']}: " \
                          f"loss = {logs['loss']:.4f}, mae = {logs['mae']:.4f}, " \
                          f"val_loss = {logs['val_loss']:.4f}, val_mae = {logs['val_mae']:.4f}"
        self.text_display.insert(tk.END, console_message + "\n")
        self.text_display.see(tk.END)  # Scroll to the end of text display

        progress_percentage = (epoch + 1) / self.params['epochs'] * 100
        for pb in self.progress_bars:
            pb['value'] = progress_percentage
        self.progress_window.update_idletasks()

        # Update full history
        self.full_loss_values.append(logs['loss'])
        self.full_val_loss_values.append(logs['val_loss'])
        self.full_mae_values.append(logs['mae'])
        self.full_val_mae_values.append(logs['val_mae'])

        make_weg = 80

        # Maintain the sliding window of 150 entries
        if len(self.loss_values) >= make_weg:
            self.loss_values.pop(0)
        if len(self.val_loss_values) >= make_weg:
            self.val_loss_values.pop(0)
        if len(self.mae_values) >= make_weg:
            self.mae_values.pop(0)
        if len(self.val_mae_values) >= make_weg:
            self.val_mae_values.pop(0)

        self.loss_values.append(logs['loss'])
        self.val_loss_values.append(logs['val_loss'])
        self.mae_values.append(logs['mae'])
        self.val_mae_values.append(logs['val_mae'])

        # Update statistics
        if logs['val_mae'] < self.lowest_val_mae:
            self.lowest_val_mae = logs['val_mae']
            self.lowest_val_mae_epoch = epoch + 1
            self.last_best_epoch = epoch + 1  # Update the epoch of the last best validation MAE
        self.highest_loss = max(self.highest_loss, logs['loss'])
        self.lowest_loss = min(self.lowest_loss, logs['loss'])

        # Update labels for highest and lowest values
        self.highest_loss_label.config(text=f"Highest Loss: {self.highest_loss:.4f}")
        self.lowest_loss_label.config(text=f"Lowest Loss: {self.lowest_loss:.4f}")
        self.lowest_val_mae_label.config(text=f"Lowest Validation MAE: {self.lowest_val_mae:.4f}")
        self.lowest_val_mae_epoch_label.config(text=f"Epoch for Lowest Validation MAE: {self.lowest_val_mae_epoch}")

        # Update the secondary progress bar based on epochs since last improvement
        epochs_since_last_improvement = (epoch + 1) - self.last_best_epoch
        remaining_patience = max(0, PATIENCE - epochs_since_last_improvement)
        self.secondary_pb['value'] = remaining_patience

        # Consolidated Plotting Logic
        self.figure.clear()
        if len(self.loss_values) > 0 and len(self.val_loss_values) > 0:
            ax1 = self.figure.add_subplot(121)  # For loss
            ax1.plot(range(1, len(self.loss_values) + 1), self.loss_values, label='Train Loss')
            ax1.plot(range(1, len(self.val_loss_values) + 1), self.val_loss_values, label='Validation Loss')
            ax1.set_xlabel('Epoch')
            ax1.set_ylabel('Loss')
            ax1.set_title('Loss Progress')
            ax1.legend()

            if len(self.mae_values) > 0 and len(self.val_mae_values) > 0:
                ax2 = self.figure.add_subplot(122)  # For MAE
                ax2.plot(range(1, len(self.mae_values) + 1), self.mae_values, label='MAE')
                ax2.plot(range(1, len(self.val_mae_values) + 1), self.val_mae_values, label='Validation MAE')
                ax2.set_xlabel('Epoch')
                ax2.set_ylabel('MAE')
                ax2.set_title('MAE Progress')
                ax2.legend()
        else:
            print("Insufficient data for plotting.")

        # Disable any interactive mode for the figure to prevent hover actions
        plt.ioff()
        self.canvas.draw()

    def on_epoch_end(self, epoch, logs=None):
        # Schedule the safe_update_gui method to run in the main GUI thread
        self.progress_window.after(0, self.safe_update_gui, epoch, logs)

    def on_train_end(self, logs=None):
        # Display final statistics in the text display
        final_stats_message = f"Training Complete.\n" \
                            f"Lowest Validation MAE: {self.lowest_val_mae:.4f} at Epoch {self.lowest_val_mae_epoch}\n" \
                            f"Highest Loss: {self.highest_loss:.4f}\n" \
                            f"Lowest Loss: {self.lowest_loss:.4f}"
        self.text_display.insert(tk.END, final_stats_message + "\n")
        self.text_display.see(tk.END)  # Scroll to the end of text display

        # Optionally, display a message box or similar to alert the user that training is complete
        tk.messagebox.showinfo("Training Complete", "The model training session has completed.")

        # Save the final plot
        # self.figure.savefig("final_training_plot.png")
        if custom_filename:
            self.figure.savefig(f'final_training_plot_{custom_filename}.png')
        else:
            self.figure.savefig(f'final_training_plot_{model_id}.png')


def parse_data_with_callback(args):
    file_pair, index, progress_callbacks, progress_callback = args

    # Convert progress_callbacks to a tuple if it's being used in a hash-requiring context
    # print(f"Processing file pair {index + 1}: {file_pair}")
    progress_callbacks_hashable = tuple(progress_callbacks) if progress_callbacks else None
    file_path_lidar, file_path_controller = file_pair

    print(f"Starting to parse lidar data from {file_path_lidar}")
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

def load_data():
    global train_lidar, train_controller, val_lidar, val_controller, custom_filename, model_filename, progress_window
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

    print(f"Loading data from folder: {folder_path}")

    # Load and parse data
    train_lidar, train_controller, val_lidar, val_controller = load_data_from_folder(folder_path, progress_callback, progress_callbacks)
    print("Data loaded successfully!")

    # Wait one second
    time.sleep(1)

    # Clear the content of the progress window
    for widget in progress_window.winfo_children():
        widget.destroy()

    # Write "finished" to the window as text
    finished_label = tk.Label(progress_window, text="Finished")
    finished_label.pack()

    # Update the window to show the "Finished" text
    progress_window.update()

    # Wait another second
    time.sleep(1)

    # Close the progress window
    progress_window.destroy()

def load_data_from_file():
    global train_lidar, train_controller, val_lidar, val_controller
    file_path = filedialog.askopenfilename(title="Select Data File", filetypes=(("NPZ Files", "*.npz"),))
    if file_path:
        print(f"Loading data from file: {file_path}")
        with np.load(file_path, allow_pickle=True) as data:
            train_lidar = data['train_lidar']
            train_controller = data['train_controller']
            val_lidar = data['val_lidar']
            val_controller = data['val_controller']
        print("Data loaded successfully!")

def save_data_in_file():
    global train_lidar, train_controller, val_lidar, val_controller
    if train_lidar.size > 0 and train_controller.size > 0 and val_lidar.size > 0 and val_controller.size > 0:
        file_path = filedialog.asksaveasfilename(title="Save Data File", filetypes=(("NPZ Files", "*.npz"),))
        if file_path:
            print(f"Saving data to file: {file_path}")
            np.savez(file_path, train_lidar=train_lidar, train_controller=train_controller, val_lidar=val_lidar, val_controller=val_controller)
            print("Data saved to file successfully!")
    else:
        print("No data to save!")

def plot_training_history(history, model_id, best_val_mae, epochs_trained, custom_filename=None):
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

    # Add text for final statistics and best validation MAE
    plt.figtext(0.5, 0.01, f'Final MAE: {final_mae:.4f}, Final Val MAE: {final_val_mae:.4f}, '
                           f'Best Val MAE: {best_val_mae:.4f}, Epochs Trained: {epochs_trained}, '
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
    # print(f"Evaluating progress for index {index}")
    if 0 <= index < len(progress_callbacks):
        progress_callbacks[index](progress)  # Update the progress bar in the GUI
        # print(f"Progress: {progress:.2f}% for index {index}")
    else:
        print(f"Error: Index {index} is out of range for progress_callbacks with length {len(progress_callbacks)}")
    root.update()
    root.update_idletasks()
    # print(f"Progress callback for index {index} completed.")

def start_training_thread():
    Thread(target=start_training).start()

def start_training():
    global train_lidar, train_controller, val_lidar, val_controller, custom_filename, model_filename, model_id
    if train_lidar is not None and train_controller is not None and val_lidar is not None and val_controller is not None:
        try:

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

            MODEL = create_model((train_lidar.shape[1], train_lidar.shape[2], 1))
            
            MODEL.compile(optimizer='adam', loss='mse', metrics=['mae'])

            # Generate a unique ID for the model
            model_id = str(uuid.uuid4())

            # Early stopping and model checkpoint
            early_stopping = EarlyStopping(monitor='val_loss', patience=PATIENCE)  # Reduced patience

            console_and_gui_callback = ConsoleAndGUIProgressCallback()
            checkpoint_filename = f"best_model_{custom_filename}.h5" if custom_filename else f'best_model_{model_id}.h5'
            model_checkpoint = ModelCheckpoint(checkpoint_filename, monitor='val_loss', save_best_only=True)

            # Train the model
            history = MODEL.fit(
                train_lidar, train_controller,
                validation_data=(val_lidar, val_controller),
                epochs=EPOCHS,
                callbacks=[early_stopping, model_checkpoint, console_and_gui_callback],
                batch_size=BATCH_SIZE
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
            plot_training_history(history, model_id, epochs_trained=len(history.history['loss']), best_val_mae=mae, custom_filename=custom_filename)

        except StopIteration:
            print("Training stopped by user.")
    
    else:
        print("No data loaded. Please load data before training the model.")
    
def load_data_thread():
    Thread(target=load_data).start()


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

    tk.Button(root, text="Load Data", command=load_data_thread).grid(row=2, column=0, columnspan=3, pady=10)
    tk.Button(root, text="Load Data from File", command=load_data_from_file).grid(row=3, column=0, columnspan=3, pady=10)
    tk.Button(root, text="Save Data in File", command=save_data_in_file).grid(row=4, column=0, columnspan=3, pady=10)
    tk.Button(root, text="Train Model", command=start_training_thread).grid(row=5, column=0, columnspan=3, pady=20)

    root.mainloop()