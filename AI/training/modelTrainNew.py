import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import signal
import threading
from sklearn.model_selection import train_test_split
import uuid
import threading
from tensorflow.keras.callbacks import Callback # type: ignore
from PIL import Image
import json
import importlib.util
import inspect

############################################################################################################

def create_model(lidar_input_shape, frame_input_shape, counter_input_shape):
    model = None
    return model

############################################################################################################

class modelTrainUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Model Training")
        
        self.tensorflow_imported = False
        self.select_training_data_path = None
        self.selected_training_data_path_basename = None
        self.selected_model_configuration_path = None
        self.settings_window = None
        self.queue = []
        
        self.model_name = tk.StringVar()
        
        self.epochs_default = 10
        self.batch_size_default = 32
        self.patience_default = 5
        
        self.epochs = tk.StringVar(value=self.epochs_default)
        self.batch_size = tk.StringVar(value=self.batch_size_default)
        self.patience = tk.StringVar(value=self.patience_default)
        
        self.handle_settings()
        
        self.SAVE_WAITTIME = 5
        
        self.protocol("WM_DELETE_WINDOW", self.close)
        signal.signal(signal.SIGINT, self.close)
        
        self.data_visualizer = VisualizeData()
        
        self.init_window()
        
        self.lazy_import_thread = threading.Thread(target=self.import_lazy_imports, daemon=True)
        self.lazy_import_thread.start()
        
        self.data_processor = DataProcessor(self)
        
        self.mainloop()

############################################################################################################

    def close(self, *args):
        self.stopped = True
        self.quit()  # Stop the main loop
        os._exit(0)
        
    def import_lazy_imports(self):
        global tf, EarlyStopping, ModelCheckpoint
        import tensorflow as tf
        from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint # type: ignore
        self.tensorflow_imported = True
        
    def handle_settings(self):
        if not os.path.exists("settings.json"):
            self.create_settings_file()
        else:
            self.load_settings()
            
    def create_settings_file(self):
        # if the settings file does not exist, create it
        with open("settings.json", "w") as f:
            file_content = {
                "epochs": self.epochs_default,
                "batch_size": self.batch_size_default,
                "patience": self.patience_default
            }
            json.dump(file_content, f)

    def load_settings(self):
        if os.path.exists("settings.json"):
            with open("settings.json", "r") as f:
                file_content = json.load(f)
                self.epochs.set(file_content["epochs"])
                self.batch_size.set(file_content["batch_size"])
                self.patience.set(file_content["patience"])
                
############################################################################################################

    def init_window(self):
        self.iconbitmap(r"AI\assets\phoenix_logo.ico")
        
        # Configure the grid of the main window to expand
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        
        # Create a frame for the information section
        self.information_frame = ctk.CTkFrame(self, fg_color="#222222", bg_color="#222222")
        self.information_frame.grid(row=0, column=0, sticky='nsew')
        
        # Create a frame for the configuration section
        self.configuration_frame = ctk.CTkFrame(self, fg_color="#1b1b1b", bg_color="#1b1b1b")
        self.configuration_frame.grid(row=0, column=1, sticky='nsew')
        
        self.create_configuration_frame()
        self.create_information_frame()
        
    def create_configuration_frame(self):
        
        self.queue_item_frame = ctk.CTkFrame(self.configuration_frame)
        self.queue_item_frame.pack(padx=15, pady=(15, 0), anchor='n', expand=False, fill='x')
        
        self.select_training_data_frame = ctk.CTkFrame(self.queue_item_frame)
        self.select_training_data_frame.pack(padx=15, pady=(15, 0), anchor='n', expand=False, fill='x')
        
        self.selected_training_data_path_label = ctk.CTkLabel(self.select_training_data_frame, text="Selected Training Data: \nNone", font=("Arial", 15))
        self.selected_training_data_path_label.pack(padx=15, pady=10, anchor='n', expand=True, fill='both')
        
        self.select_training_data_button = ctk.CTkButton(self.select_training_data_frame, text="Select Training Data", command=self.select_training_data)
        self.select_training_data_button.pack(padx=15, pady=(5, 15), anchor='n', expand=True, fill='both')
        
        ############################################################################################################
        
        self.select_model_configuration_frame = ctk.CTkFrame(self.queue_item_frame)
        self.select_model_configuration_frame.pack(padx=15, pady=(15, 0), anchor='n', expand=False, fill='x')
        
        self.select_model_configuration_label = ctk.CTkLabel(self.select_model_configuration_frame, text="Model Configuration File: \nNone", font=("Arial", 15))
        self.select_model_configuration_label.pack(padx=15, pady=(15, 0), anchor='n', expand=True, fill='both')
        
        self.select_model_configuration_button = ctk.CTkButton(self.select_model_configuration_frame, text="Select Model Configuration", command=self.select_model_configuration)
        self.select_model_configuration_button.pack(padx=15, pady=(15, 15), anchor='n', expand=True, fill='both')
        
        ############################################################################################################
        
        self.select_model_name_frame = ctk.CTkFrame(self.queue_item_frame)
        self.select_model_name_frame.pack(padx=15, pady=(15, 0), anchor='n', expand=False, fill='x')
        
        self.select_model_name_label = ctk.CTkLabel(self.select_model_name_frame, text="Model Name (Optional)", font=("Arial", 15))
        self.select_model_name_label.pack(padx=15, pady=(15, 0), anchor='n', expand=True, fill='both')
        
        self.select_model_name_entry = ctk.CTkEntry(self.select_model_name_frame, font=("Arial", 15), textvariable=self.model_name)
        self.select_model_name_entry.pack(padx=15, pady=(15, 15), anchor='n', expand=True, fill='both')
        
        ############################################################################################################
        
        self.add_to_queue_button = ctk.CTkButton(self.queue_item_frame, text="Add to Queue", command=self.add_to_queue)
        self.add_to_queue_button.pack(padx=15, pady=(20, 15), anchor='n', expand=True, fill='both')
        
        ############################################################################################################
        
        self.start_queue_button = ctk.CTkButton(self.configuration_frame, text="Start Queue", command=self.start_queue)
        self.start_queue_button.pack(padx=15, pady=20, anchor='n', expand=True, fill='x')
        
        ############################################################################################################
        
        settings_image = Image.open(r"AI\assets\settings.png")
        settings_image = ctk.CTkImage(settings_image, settings_image, (25, 25))
        
        self.settings_button = ctk.CTkButton(self, image=settings_image, command=self.open_settings, text="", width=25, height=25, corner_radius=5,  bg_color='transparent')
        
        # Place the button at the top right corner
        self.update_idletasks()  # Ensure the widget sizes are updated
        parent_width = self.winfo_width()
        button_width = self.settings_button.winfo_reqwidth()
        self.settings_button.place(x=parent_width - button_width - 10, y=10)
        
        self.bind("<Configure>", self.on_resize)
        
    def create_information_frame(self):
        self.information_frame.grid_rowconfigure(0, weight=1)
        self.information_frame.grid_columnconfigure(0, weight=1)
        
        self.loss_plot_frame = ctk.CTkFrame(self.information_frame, height=1000, width=1000)
        self.loss_plot_frame.grid(row=0, column=0, padx=15, pady=15, sticky='nsew')
        self.data_visualizer.create_loss_plot(self.loss_plot_frame)
        
        self.mae_plot_frame = ctk.CTkFrame(self.information_frame, height=1000, width=1000)
        self.mae_plot_frame.grid(row=1, column=0, padx=15, pady=15, sticky='nsew')
        self.data_visualizer.create_mae_plot(self.mae_plot_frame)
        
        self.information_frame.grid_rowconfigure(1, weight=1)

############################################################################################################

    def select_training_data(self):
        path = filedialog.askdirectory()
        
        if path == "" or not path:
            return
        
        self.selected_training_data_path = path
        self.selected_training_data_path_basename = os.path.basename(path)
        
        self.selected_training_data_path_label.configure(text=f"Selected Training Data: \n{self.selected_training_data_path_basename}")
        
        self.data_processor.load_training_data_wrapper(path)
        
    def select_model_configuration(self):
        path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        
        if path == "" or not path:
            return
        
        if not path.endswith(".py"):
            messagebox.showerror("Error", "The selected file is not a Python file")
            return
        
        self.selected_model_configuration_path = path
        self.selected_model_configuration_path_basename = os.path.basename(path)
        
        self.select_model_configuration_label.configure(text=f"Model Configuration File: \n{self.selected_model_configuration_path_basename}")
        
        self.data_processor.load_model_configuration(path)
    
    def add_to_queue(self):
        if self.selected_training_data_path is None:
            messagebox.showerror("Error", "No training data selected")
            return
        if self.selected_model_configuration_path is None:
            messagebox.showerror("Error", "No model configuration selected")
            return
        
        self.data_processor.pass_training_options(self.model_name.get(), int(self.epochs.get()), int(self.batch_size.get()), int(self.patience.get()))
        self.queue.append(self.data_processor)
        
        self.data_processor = DataProcessor(self)
        
        self.model_name.set("")
        self.selected_training_data_path_label.configure(text="Selected Training Data: \nNone")
        self.selected_training_data_path = None
        self.selected_training_data_path_basename = None
        
        # messagebox.showinfo("Success", "Added to queue successfully")
    
    def start_queue(self):
        self.queue_thread = threading.Thread(target=self.process_queue, daemon=True)
        self.queue_thread.start()
        
    def process_queue(self):
        for item in self.queue:
            item.start_training()
            while item.model_train_thread.is_alive():
                pass
        messagebox.showinfo("Success", "Queue processed successfully")
        
    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.update()
            self.settings_window.focus_force()
            return
        
        # open top level window
        self.settings_window = ctk.CTkToplevel(self)
        
        self.settings_window.title("Settings")
        
        self.epochs_frame = ctk.CTkFrame(self.settings_window)
        self.epochs_frame.pack(side=tk.LEFT, padx=15, pady=15, anchor='n', expand=True, fill='both')
        
        self.epochs_label = ctk.CTkLabel(self.epochs_frame, text="Epochs", font=("Arial", 15))
        self.epochs_label.pack(padx=15, pady=(15, 0), anchor='n', expand=True, fill='both')
        
        self.epochs_entry = ctk.CTkEntry(self.epochs_frame, font=("Arial", 15), textvariable=self.epochs)
        self.epochs_entry.pack(padx=15, pady=(15, 15), anchor='n', expand=True, fill='both')
        
        self.epochs_entry.bind("<FocusOut>", lambda e: self.save_settings())
        
        
        self.batch_size_frame = ctk.CTkFrame(self.settings_window)
        self.batch_size_frame.pack(side=tk.LEFT, padx=15, pady=15, anchor='n', expand=True, fill='both')
        
        self.batch_size_label = ctk.CTkLabel(self.batch_size_frame, text="Batch Size", font=("Arial", 15))
        self.batch_size_label.pack(padx=15, pady=(15, 0), anchor='n', expand=True, fill='both')
        
        self.batch_size_entry = ctk.CTkEntry(self.batch_size_frame, font=("Arial", 15), textvariable=self.batch_size)
        self.batch_size_entry.pack(padx=15, pady=(15, 15), anchor='n', expand=True, fill='both')
        
        self.batch_size_entry.bind("<FocusOut>", lambda e: self.save_settings())
        
        
        self.patience_frame = ctk.CTkFrame(self.settings_window)
        self.patience_frame.pack(side=tk.LEFT, padx=15, pady=15, anchor='n', expand=True, fill='both')
        
        self.patience_label = ctk.CTkLabel(self.patience_frame, text="Patience", font=("Arial", 15))
        self.patience_label.pack(padx=15, pady=(15, 0), anchor='n', expand=True, fill='both')
        
        self.patience_entry = ctk.CTkEntry(self.patience_frame, font=("Arial", 15), textvariable=self.patience)
        self.patience_entry.pack(padx=15, pady=(15, 15), anchor='n', expand=True, fill='both')
        
        self.patience_entry.bind("<FocusOut>", lambda e: self.save_settings())
        
        self.update()
        self.settings_window.focus_force()
    
    def on_resize(self, event):
        parent_width = self.winfo_width()
        button_width = self.settings_button.winfo_reqwidth()
        self.settings_button.place(x=parent_width - button_width - 10, y=10)
        
    def save_settings(self):
        # check if all values are integers
        try:
            int(self.epochs.get())
            int(self.batch_size.get())
            int(self.patience.get())
        except ValueError:
            messagebox.showerror("Error", "All values must be integers")
            return
        
        with open("settings.json", "w") as f:
            file_content = {
                "epochs": self.epochs.get(),
                "batch_size": self.batch_size.get(),
                "patience": self.patience.get()
            }
            json.dump(file_content, f)


class DataProcessor:
    def __init__(self, modelTrainUI):
        self.modelTrainUI = modelTrainUI
        self.lidar_train = None
        self.image_train = None
        self.controller_train = None
        self.counter_train = None
        self.lidar_val = None
        self.image_val = None
        self.controller_val = None
        self.counter_val = None
        self.model_name = ""
        self.epochs = None
        self.batch_size = None
        self.patience = None
        self.model = None
        self.model_train_thread = None
        
        self.model_file_content = None
        self.model_function = None
        
    def pass_training_options(self, model_name, epochs, batch_size, patience):
        self.model_name = model_name
        self.epochs = epochs
        self.batch_size = batch_size
        self.patience = patience
    
    def start_training(self):
        if not self.modelTrainUI.tensorflow_imported:
            messagebox.showerror("Error", "TensorFlow not imported yet. Please wait for the import to complete.")
            return
        
        if self.lidar_train is None or self.image_train is None or self.controller_train is None or self.counter_train is None:
            messagebox.showerror("Error", "No training data loaded")
            return

        if self.model_name == "":
            if messagebox.askyesno("Warning", "No model name provided. Do you want to continue? A random UUID will be used!"):
                self.model_name = str(uuid.uuid4())
            else:
                return
            
        self.model_train_thread = threading.Thread(target=self.train_model, args=(self.model_name, self.epochs, self.batch_size, self.patience), daemon=True)
        self.model_train_thread.start()

    def train_model(self, model_name, epochs, batch_size, patience):
        print(f"Train LIDAR data shape: {self.lidar_train.shape}")
        print(f"Train Controller data shape: {self.controller_train.shape}")
        print(f"Train Frame data shape: {self.image_train.shape}")
        print(f"Train Counter data shape: {self.counter_train.shape}")
        print(f"Validation LIDAR data shape: {self.lidar_val.shape}")
        print(f"Validation Controller data shape: {self.controller_val.shape}")
        print(f"Validation Frame data shape: {self.image_val.shape}")
        print(f"Validation Counter data shape: {self.counter_val.shape}")
        print(1)
        
        self.model = self.model_function(lidar_input_shape=(self.lidar_train.shape[1], self.lidar_train.shape[2], 1),
                                  frame_input_shape=(self.image_train.shape[1], self.image_train.shape[2], self.image_train.shape[3]),
                                  counter_input_shape=(self.counter_train.shape[1],), tf=tf)
        print(2)
        self.model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        print(3)
        
        early_stopping = EarlyStopping(monitor='val_loss', patience=patience)
        checkpoint_filename = f"best_model_{model_name}.h5"
        model_checkpoint = ModelCheckpoint(checkpoint_filename, monitor='val_loss', save_best_only=True)
        print(4)
        
        history = self.model.fit(
            [self.lidar_train, self.image_train, self.counter_train], self.controller_train,
            validation_data=([self.lidar_val, self.image_val, self.controller_val], self.controller_val),
            epochs=epochs,
            callbacks=[early_stopping, model_checkpoint],
            batch_size=batch_size
        )
        print(5)
        
    def load_training_data_wrapper(self, folder_path):
        self.load_training_data_thread = threading.Thread(target=self.load_training_data, args=(folder_path,), daemon=True)
        self.load_training_data_thread.start()

    def load_training_data(self, folder_path):
        if not folder_path:
            messagebox.showerror("Error", "No data folder selected")
            return

        lidar_data_list = []
        image_data_list = []
        controller_data_list = []
        counter_data_list = []
        file_count = 0

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.startswith("run_data_"):
                    file_path = os.path.join(root, file)
                    np_arrays = np.load(file_path, allow_pickle=True)
                    lidar_data_list.append(np_arrays['train_lidar'])
                    image_data_list.append(np_arrays['train_frame'])
                    controller_data_list.append(np_arrays['train_controller'])
                    counter_data_list.append(np_arrays['train_counters'])
                    file_count += 1

        if not lidar_data_list or not image_data_list or not controller_data_list or not counter_data_list:
            messagebox.showerror("Error", "No data files found in the selected folder")
            return

        # Combine data from all folders
        lidar_data = np.concatenate(lidar_data_list, axis=0)
        simplified_image_data = np.concatenate(image_data_list, axis=0)
        controller_data = np.concatenate(controller_data_list, axis=0)
        counter_data = np.concatenate(counter_data_list, axis=0)

        # Perform the train-validation split
        self.lidar_train, self.lidar_val = train_test_split(lidar_data, test_size=0.2, random_state=42)
        self.image_train, self.image_val = train_test_split(simplified_image_data, test_size=0.2, random_state=42)
        self.controller_train, self.controller_val = train_test_split(controller_data, test_size=0.2, random_state=42)
        self.counter_train, self.counter_val = train_test_split(counter_data, test_size=0.2, random_state=42)
        
        # messagebox.showinfo("Success", f"Data loaded successfully. {file_count} files were loaded.")
        
    def load_model_configuration(self, file_path):
        with open(file_path, 'r') as file:
            self.model_file_content = file.read()
        # Load the module without using the file path for the module name
        spec = importlib.util.spec_from_file_location("model", file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find the only function in the module
        functions = [obj for name, obj in inspect.getmembers(module) if inspect.isfunction(obj)]
        if len(functions) != 1:
            raise ValueError("The module should contain exactly one function.")
        
        self.model_function = functions[0]


class TrainingDataCallback(Callback):
    def __init__(self):
        self.visualize_data = VisualizeData()

        # track latest training values
        self.loss_values = []
        self.val_loss_values = []
        self.mae_values = []
        self.val_mae_values = []

        # complete history of training values
        self.full_loss_values = []
        self.full_val_loss_values = []
        self.full_mae_values = []
        self.full_val_mae_values = []

    def on_epoch_end(self, epoch, logs=None):
        self.loss_values.append(logs['loss'])
        self.val_loss_values.append(logs['val_loss'])
        self.mae_values.append(logs['mae'])
        self.val_mae_values.append(logs['val_mae'])
        
        if len(self.loss_values) > 50:
            self.loss_values.pop(0)
            self.val_loss_values.pop(0)
            self.mae_values.pop(0)
            self.val_mae_values.pop(0)
        
        self.visualize_data.update_loss_plot(self.loss_values, self.val_loss_values)
        self.visualize_data.update_mae_plot(self.mae_values, self.val_mae_values)
        
        self.full_loss_values.append(logs['loss'])
        self.full_val_loss_values.append(logs['val_loss'])
        self.full_mae_values.append(logs['mae'])
        self.full_val_mae_values.append(logs['val_mae'])

    def on_train_end(self, logs=None):
        self.visualize_data.create_plots_after_training(self.full_loss_values, self.full_val_loss_values, self.full_mae_values, self.full_val_mae_values)


class VisualizeData:
    def create_loss_plot(self, tk_frame):
        self.loss_plot_fig = plt.figure(facecolor='#222222', edgecolor='#222222')
        self.loss_plot_axis = self.loss_plot_fig.add_subplot(111)
        
        self.loss_plot_axis.tick_params(axis='x', colors='white')
        self.loss_plot_axis.tick_params(axis='y', colors='white')
        
        for spine in self.loss_plot_axis.spines.values():
            spine.set_edgecolor('white')
        
        self.loss_plot_axis.grid(True, color='gray', linestyle='--', linewidth=0.5)
        self.loss_plot_axis.set_facecolor('#222222')
        
        self.loss_plot_canvas = FigureCanvasTkAgg(self.loss_plot_fig, tk_frame)
        self.loss_plot_canvas.draw()
        self.loss_plot_canvas.get_tk_widget().config(width=700, height=400)
        self.loss_plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        tk_frame.bind("<Configure>", self.on_resize_loss)

    def on_resize_loss(self, event):
        # Update the plot size on window resize
        self.loss_plot_canvas.get_tk_widget().config(width=event.width, height=event.height)

    def update_loss_plot(self, loss_values, val_loss_values):
        self.loss_plot_axis.clear()
        
        self.loss_plot_axis.plot(loss_values, label='Training Loss', color='blue')
        self.loss_plot_axis.plot(val_loss_values, label='Validation Loss', color='red')
        
        self.loss_plot_axis.set_xlabel('Epochs')
        self.loss_plot_axis.set_ylabel('Loss')
        self.loss_plot_axis.legend()
        
        self.loss_plot_canvas.draw()

    def clear_loss_plot(self):
        self.loss_plot_axis.clear()
        self.loss_plot_axis.grid(True, color='gray', linestyle='--', linewidth=0.5)
        self.loss_plot_canvas.draw()

    ############################################################################################################

    def create_mae_plot(self, tk_frame):
        self.mae_plot_fig = plt.figure(facecolor='#222222', edgecolor='#222222')
        self.mae_plot_axis = self.mae_plot_fig.add_subplot(111)
        
        self.mae_plot_axis.tick_params(axis='x', colors='white')
        self.mae_plot_axis.tick_params(axis='y', colors='white')
        
        for spine in self.mae_plot_axis.spines.values():
            spine.set_edgecolor('white')

        self.mae_plot_axis.grid(True, color='gray', linestyle='--', linewidth=0.5)
        self.mae_plot_axis.set_facecolor('#222222')
        
        self.mae_plot_canvas = FigureCanvasTkAgg(self.mae_plot_fig, tk_frame)
        self.mae_plot_canvas.draw()
        
        # Configure the widget
        self.mae_plot_canvas.get_tk_widget().config(width=700, height=400)
        self.mae_plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        tk_frame.bind("<Configure>", self.on_resize_mae)

    def on_resize_mae(self, event):
        # Update the plot size on window resize
        self.mae_plot_canvas.get_tk_widget().config(width=event.width, height=event.height)

    def update_mae_plot(self, mae_values, val_mae_values):
        self.mae_plot_axis.clear()
        
        self.mae_plot_axis.plot(mae_values, label='Training MAE', color='blue')
        self.mae_plot_axis.plot(val_mae_values, label='Validation MAE', color='red')
        
        self.mae_plot_axis.set_xlabel('Epochs')
        self.mae_plot_axis.set_ylabel('MAE')
        self.mae_plot_axis.legend()
        
        self.mae_plot_canvas.draw()

    def clear_mae_plot(self):
        self.mae_plot_axis.clear()
        self.mae_plot_axis.grid(True, color='gray', linestyle='--', linewidth=0.5)
        self.mae_plot_canvas.draw()

    ############################################################################################################

    def create_plots_after_training(self, loss_values, val_loss_values, mae_values, val_mae_values, save_path='training_plots.png'):
        # Create a figure with two subplots
        fig, (loss_ax, mae_ax) = plt.subplots(2, 1, figsize=(10, 8), facecolor='#222222')

        # Customize the loss plot
        loss_ax.plot(loss_values, label='Training Loss', color='blue')
        loss_ax.plot(val_loss_values, label='Validation Loss', color='red')
        loss_ax.set_xlabel('Epochs', color='white')
        loss_ax.set_ylabel('Loss', color='white')
        loss_ax.legend()
        loss_ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
        loss_ax.tick_params(axis='x', colors='white')
        loss_ax.tick_params(axis='y', colors='white')
        for spine in loss_ax.spines.values():
            spine.set_edgecolor('white')

        # Customize the MAE plot
        mae_ax.plot(mae_values, label='Training MAE', color='blue')
        mae_ax.plot(val_mae_values, label='Validation MAE', color='red')
        mae_ax.set_xlabel('Epochs', color='white')
        mae_ax.set_ylabel('MAE', color='white')
        mae_ax.legend()
        mae_ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
        mae_ax.tick_params(axis='x', colors='white')
        mae_ax.tick_params(axis='y', colors='white')
        for spine in mae_ax.spines.values():
            spine.set_edgecolor('white')

        # Adjust layout
        plt.tight_layout()

        # Save the figure to a file
        plt.savefig(save_path)

        # Close the figure to release memory
        plt.close(fig)

if __name__ == "__main__":
    modelTrainUI()