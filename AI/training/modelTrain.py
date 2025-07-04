print("Importing necessary modules...")
import customtkinter as ctk
from CTkListbox import *
import tkinter as tk
from tkinter import messagebox, filedialog
# import numpy as np
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('agg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
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
import time
import types
import re
from pygments import lex
from pygments.lexers.python import PythonLexer
from pygments.styles import get_style_by_name
import platform
import chime
print("Done.")

############################################################################################################

global DEBUG, TRAIN_VAL_SPLIT_RANDOM_STATE, USE_FEATURE_SELECTION, NUM_FEATURES

DEBUG = True
# USE_FEATURE_SELECTION = True
# NUM_FEATURES = 50

############################################################################################################

class modelTrainUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Model Training")
        self.geometry("+50+50")
        self.minsize(height=1050, width=1500)
        
        # set to always dark mode
        ctk.set_appearance_mode("dark")
        
        self.selected_training_data_path = None
        self.selected_training_data_path_basename = None
        self.selected_model_configuration_path = None
        self.selected_model_configuration_path_basename = None
        self.settings_window = None
        self.found_training_data = None
        
        self.lazy_imports_imported = False
        
        self.model_name_counter = 0
        
        self.queue = []
        
        self.open_details_windows = {}
        
        self.data_processor = None
        self.current_queue_item = None
        self.stop_training = False
        self.model_dir = None
        
        self.model_name = tk.StringVar()
        self.keep_config_var = tk.BooleanVar()
        self.keep_config_var_global = tk.BooleanVar()
        
        self.save_as_h5 = tk.BooleanVar(value=True)
        self.save_as_tflite = tk.BooleanVar(value=False)
        self.save_with_model_config = tk.BooleanVar(value=True)
        
        
        # SETTINGS
        self.epochs_default = 50
        self.batch_size_default = 32
        self.patience_default = 20
        self.epochs_graphed_default = 50
        self.data_shift_default = 0
        self.split_random_state_default = 42
        self.use_visual_data_default = False
        self.use_feature_selection_default = False
        self.num_features_default = 50
        
        self.epochs = tk.StringVar(value=self.epochs_default)
        self.batch_size = tk.StringVar(value=self.batch_size_default)
        self.patience = tk.StringVar(value=self.patience_default)
        self.epochs_graphed = tk.StringVar(value=self.epochs_graphed_default)
        self.data_shift = tk.StringVar(value=self.data_shift_default)
        self.split_random_state = tk.StringVar(value=self.split_random_state_default)
        self.use_visual_data = tk.BooleanVar(value=self.use_visual_data_default)
        self.use_feature_selection = tk.BooleanVar(value=self.use_feature_selection_default)
        self.num_features = tk.StringVar(value=self.num_features_default)
        
        self.settings = {
            "epochs": (self.epochs, self.epochs_default, "int"),
            "batch_size": (self.batch_size, self.batch_size_default, "int"),
            "patience": (self.patience, self.patience_default, "int"),
            "epochs_graphed": (self.epochs_graphed, self.epochs_graphed_default, "int"),
            "data_shift": (self.data_shift, self.data_shift_default, "int"),
            "split_random_state": (self.split_random_state, self.split_random_state_default, "int"),
            "use_visual_data": (self.use_visual_data, self.use_visual_data_default, "bool"),
            "use_feature_selection": (self.use_feature_selection, self.use_feature_selection_default, "bool"),
            "num_features": (self.num_features, self.num_features_default, "int")
        }
        
        self.load_training_data_lock = threading.Lock()
        self.reload_training_data_lock = threading.Lock()
        self.reload_training_data_waiting = False
        self.last_data_change = {"data_shift": [self.data_shift_default, self.reload_training_data_wrapper],
                                 "split_random_state": [self.split_random_state_default, self.reload_training_data_wrapper]}
        
        self.configuration_path_global = "model_preset_configuration.json"
        
        self.handle_settings()
        
        self.protocol("WM_DELETE_WINDOW", self.close)
        signal.signal(signal.SIGINT, self.close)
        
        chime.theme("big-sur")
        
        self.data_visualizer = VisualizeData()
        
        self.init_window()
        
        self.lazy_import_thread = threading.Thread(target=self.import_lazy_imports, daemon=True)
        self.lazy_import_thread.start()
        
        self.data_processor = DataProcessor(self)
        
        if os.path.exists(self.configuration_path_global):
            self.load_model_configuration_file()
            self.keep_config_var_global.set(True)
            self.keep_config_var.set(True)
            
        # toggle button states
        self.toggle_button_state(self.skip_queue_item_button, False)
        self.toggle_button_state(self.stop_queue_button, False)
        
        self.mainloop()

############################################################################################################

    def close(self, *args):
        self.handle_save_model_configuration()
        self.stopped = True
        self.quit()  # Stop the main loop
        os._exit(0)
        
    def import_lazy_imports(self):
        global tf, EarlyStopping, ModelCheckpoint, np, FigureCanvasTkAgg, train_test_split, ReduceLROnPlateau, SelectKBest, f_regression, f_classif
        import tensorflow as tf
        from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau # type: ignore
        import numpy as np
        from sklearn.model_selection import train_test_split
        from sklearn.feature_selection import SelectKBest, f_regression, f_classif
        
        self.lazy_imports_imported = True
        
    def handle_settings(self):
        if not os.path.exists(".config/settingsModelTrain.json"):
            self.create_settings_file()
        else:
            self.load_settings()
        
    def create_settings_file(self):
        settings = self.settings
        
        if not os.path.exists(".config"):
            os.mkdir(".config")
        
        with open(".config/settingsModelTrain.json", "w") as f:
            file_content = {}
            for key, (_, default, _) in settings.items():
                file_content[key] = default
            json.dump(file_content, f)

    def load_settings(self):
        settings = self.settings
        
        if os.path.exists(".config/settingsModelTrain.json"):
            try:
                with open(".config/settingsModelTrain.json", "r") as f:
                    file_content = json.load(f)
                    for key, (value, _, _) in settings.items():
                        if key in file_content:
                            value.set(file_content[key])
            except (KeyError, json.decoder.JSONDecodeError):
                delete_or_not = messagebox.askyesno("Error", "The settings file is corrupted. Do you want to delete it? Or exit!")
                if delete_or_not:
                    os.remove(".config/settingsModelTrain.json")
                    self.create_settings_file()
                    self.load_settings()
                else:
                    self.close()
                    
    def save_model_configuration_file(self):
        if not self.keep_config_var_global.get():
            return
        
        if self.selected_training_data_path is None or self.selected_model_configuration_path is None:
            return
        
        self.configuration_to_save = {
            "selected_training_data_path": self.selected_training_data_path,
            "selected_training_data_path_basename": self.selected_training_data_path_basename,
            "selected_model_configuration_path": self.selected_model_configuration_path,
            "selected_model_configuration_path_basename": self.selected_model_configuration_path_basename,
            "model_name": self.model_name.get(),
            "save_as_h5": self.save_as_h5.get(),
            "save_as_tflite": self.save_as_tflite.get(),
            "save_with_model_config": self.save_with_model_config.get(),
            "model_dir": self.model_dir
        }
        
        with open(self.configuration_path_global, "w") as f:
            json.dump(self.configuration_to_save, f)
            
    def load_model_configuration_file(self):
        if not os.path.exists(self.configuration_path_global):
            return
        try:
            with open(self.configuration_path_global, "r") as f:
                file_content = json.load(f)
                self.selected_training_data_path = file_content.get("selected_training_data_path")
                self.selected_training_data_path_basename = file_content.get("selected_training_data_path_basename")
                self.selected_model_configuration_path = file_content.get("selected_model_configuration_path")
                self.selected_model_configuration_path_basename = file_content.get("selected_model_configuration_path_basename")
                self.model_name.set(file_content.get("model_name"))
                self.save_as_h5.set(file_content.get("save_as_h5"))
                self.save_as_tflite.set(file_content.get("save_as_tflite"))
                self.save_with_model_config.set(file_content.get("save_with_model_config"))
                self.model_dir = file_content.get("model_dir")
        except:
            answer = messagebox.askyesno("Error", "The necessary files are not found. Do you want to delete the configuration file (yes) or exit (no) ?")
            if answer:
                os.remove(self.configuration_path_global)
                return
            else:
                self.close()
                return

        # Ensure paths are not None before checking their existence
        if (self.selected_training_data_path is None or 
            self.selected_model_configuration_path is None or 
            not os.path.exists(self.selected_training_data_path) or 
            not os.path.exists(self.selected_model_configuration_path)):
            
            # print which file is missing
            if self.selected_training_data_path is None or not os.path.exists(self.selected_training_data_path):
                print("Training data is missing")
            if self.selected_model_configuration_path is None or not os.path.exists(self.selected_model_configuration_path):
                print("Model configuration is missing")
            
            answer = messagebox.askyesno("Error", "The necessary files are not found. Do you want to delete the configuration file (yes) or exit (no) ?")
            if answer:
                os.remove(self.configuration_path_global)
                return
            else:
                self.close()
                return
        
        if self.selected_training_data_path_basename:
            self.selected_training_data_path_label.configure(text=f"Selected Training Data: \n{self.selected_training_data_path_basename}")
        if self.selected_model_configuration_path_basename:
            self.select_model_configuration_label.configure(text=f"Model Configuration File: \n{self.selected_model_configuration_path_basename}")
        
        if self.selected_training_data_path:
            self.data_processor.load_training_data_wrapper(self.selected_training_data_path, self.data_shift.get(), self.split_random_state.get())
        if self.selected_model_configuration_path:
            self.data_processor.load_model_configuration(self.selected_model_configuration_path)
            
        if self.model_dir:
            self.select_output_directory_button.configure(fg_color="#1F6AA5")
            self.select_output_directory_button.configure(text=f"{os.path.basename(self.model_dir)}")

    def handle_save_model_configuration(self, advanced=False):
        if self.keep_config_var_global.get():
            if advanced:
                self.keep_config_var.set(True)
            self.save_model_configuration_file()
        elif advanced:
            if os.path.exists(self.configuration_path_global):
                os.remove(self.configuration_path_global)
    
    def toggle_button_state(self, button, state=True):
        if state:
            button.configure(state=tk.NORMAL)
            button.configure(fg_color='#1F6AA5')
        else:
            button.configure(state=tk.DISABLED)
            button.configure(fg_color='#0d2b42')

        self.update()
        self.update_idletasks()
                
############################################################################################################

    def init_window(self):
        if platform.system() == "Windows":
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
        self.queue_item_frame.pack(padx=15, pady=(10, 0), anchor='n', expand=False, fill='x')
        
        ############################################################################################################
        
        self.in_config_settings_frame = ctk.CTkFrame(self.queue_item_frame)
        self.in_config_settings_frame.pack(padx=15, pady=(10, 0), anchor='n', expand=False, fill='x')
        
        self.in_config_settings_frame.grid_rowconfigure(0, weight=1)
        self.in_config_settings_frame.grid_columnconfigure(0, weight=1, uniform='settings')
        self.in_config_settings_frame.grid_columnconfigure(1, weight=1, uniform='settings')
        
        settings_image = Image.open(r"AI/assets/settings.png")
        settings_image = ctk.CTkImage(settings_image, settings_image, (25, 25))
        
        self.in_config_settings_button = ctk.CTkButton(self.in_config_settings_frame, image=settings_image, command=self.open_settings, text="Settings", width=25, height=25, corner_radius=5,  bg_color='transparent')
        self.in_config_settings_button.grid(row=0, column=0, padx=(5, 2), pady=(5, 5), sticky='we')
        
        open_directory_image = Image.open(r"AI/assets/folder_open.png")
        open_directory_image = ctk.CTkImage(open_directory_image, open_directory_image, (25, 25))
        
        self.select_output_directory_button = ctk.CTkButton(self.in_config_settings_frame, text="Select Output Directory", command=self.select_output_directory, corner_radius=5, image=open_directory_image, width=25, height=25, bg_color='transparent')
        self.select_output_directory_button.grid(row=0, column=1, padx=(2, 5), pady=(5, 5), sticky='we')
        self.select_output_directory_button.configure(fg_color='#0c5743')
        
        ############################################################################################################
        
        self.select_training_data_frame = ctk.CTkFrame(self.queue_item_frame)
        self.select_training_data_frame.pack(padx=15, pady=(12, 0), anchor='n', expand=False, fill='x')
        
        self.selected_training_data_path_label = ctk.CTkLabel(self.select_training_data_frame, text="Selected Training Data: \nNone", font=("Arial", 15))
        self.selected_training_data_path_label.pack(padx=15, pady=(7, 10), anchor='n', expand=True, fill='both')
        
        self.select_training_data_button = ctk.CTkButton(self.select_training_data_frame, text="Select Training Data", command=self.select_training_data)
        self.select_training_data_button.pack(padx=15, pady=(0, 12), anchor='n', expand=True, fill='both')
        
        ############################################################################################################
        
        self.select_model_configuration_frame = ctk.CTkFrame(self.queue_item_frame)
        self.select_model_configuration_frame.pack(padx=15, pady=(12, 0), anchor='n', expand=False, fill='x')
        
        self.select_model_configuration_label = ctk.CTkLabel(self.select_model_configuration_frame, text="Model Configuration File: \nNone", font=("Arial", 15))
        self.select_model_configuration_label.pack(padx=15, pady=(7, 10), anchor='n', expand=True, fill='both')
        
        self.select_model_configuration_button = ctk.CTkButton(self.select_model_configuration_frame, text="Select Model Configuration", command=self.select_model_configuration)
        self.select_model_configuration_button.pack(padx=15, pady=(0, 12), anchor='n', expand=True, fill='both')
        
        ############################################################################################################
        
        self.select_model_name_frame = ctk.CTkFrame(self.queue_item_frame)
        self.select_model_name_frame.pack(padx=15, pady=(12, 0), anchor='n', expand=False, fill='x')
        
        self.select_model_name_label = ctk.CTkLabel(self.select_model_name_frame, text="Model Name (Optional)", font=("Arial", 15))
        self.select_model_name_label.pack(padx=15, pady=(7, 2), anchor='n', expand=True, fill='both')
        
        self.select_model_name_entry = ctk.CTkEntry(self.select_model_name_frame, font=("Arial", 15), textvariable=self.model_name)
        self.select_model_name_entry.pack(padx=15, pady=(0, 12), anchor='n', expand=True, fill='both')
        
        self.select_model_name_frame.bind("<FocusOut>", lambda e: self.handle_save_model_configuration())
        self.select_model_name_entry.bind("<FocusOut>", lambda e: self.handle_save_model_configuration())
        
        ############################################################################################################
        
        self.format_settings_frame = ctk.CTkFrame(self.queue_item_frame)
        self.format_settings_frame.pack(padx=15, pady=(12, 0), anchor='n', expand=False, fill='x')
        
        self.format_settings_frame.grid_rowconfigure(0, weight=1)
        self.format_settings_frame.grid_rowconfigure(1, weight=1)
        self.format_settings_frame.grid_columnconfigure(0, weight=1)
        self.format_settings_frame.grid_columnconfigure(1, weight=1)
        self.format_settings_frame.grid_columnconfigure(2, weight=1)
        
        self.save_as_label = ctk.CTkLabel(self.format_settings_frame, text="Save the:", font=("Arial", 15))
        self.save_as_label.grid(row=0, column=0, padx=(15, 15), pady=(5, 0), sticky='we', columnspan=3)
        
        self.save_as_h5_switch = ctk.CTkSwitch(self.format_settings_frame, text=".h5 Model", variable=self.save_as_h5, font=("Arial", 13), command=self.handle_save_model_configuration)
        self.save_as_h5_switch.grid(row=1, column=0, padx=(5, 5), pady=(5, 5), sticky='we')
        
        self.save_as_tflite_switch = ctk.CTkSwitch(self.format_settings_frame, text=".tflite Model", variable=self.save_as_tflite, font=("Arial", 13), command=self.handle_save_model_configuration)
        self.save_as_tflite_switch.grid(row=1, column=1, padx=(5, 5), pady=(5, 5), sticky='we')
        
        self.save_with_model_config_switch = ctk.CTkSwitch(self.format_settings_frame, text="Model Configuration", variable=self.save_with_model_config, font=("Arial", 13), command=self.handle_save_model_configuration)
        self.save_with_model_config_switch.grid(row=1, column=2, padx=(5, 5), pady=(5, 5), sticky='we')
        
        ############################################################################################################
        
        self.keep_config_frame = ctk.CTkFrame(self.queue_item_frame)
        self.keep_config_frame.pack(padx=15, pady=(12, 0), anchor='n', expand=False, fill='x')
        
        self.keep_config_checkbox = ctk.CTkCheckBox(self.keep_config_frame, text="Keep Configuration", font=("Arial", 13), variable=self.keep_config_var)
        self.keep_config_checkbox.pack(padx=(20, 10), pady=(5, 5), side='left', expand=True, fill='both')
        
        self.keep_config_global_checkbox = ctk.CTkCheckBox(self.keep_config_frame, text="Keep Configuration Globally", font=("Arial", 13), variable=self.keep_config_var_global, command=lambda: self.handle_save_model_configuration(True))
        self.keep_config_global_checkbox.pack(padx=(10, 20), pady=(5, 5), side='right', expand=False, fill='both')
        
        ############################################################################################################
        
        self.add_to_queue_button = ctk.CTkButton(self.queue_item_frame, text="Add to Queue", command=self.add_to_queue)
        self.add_to_queue_button.pack(padx=15, pady=(15, 15), anchor='n', expand=True, fill='both')
        
        ############################################################################################################
        
        self.queue_frame = ctk.CTkFrame(self.configuration_frame)
        self.queue_frame.pack(padx=10, pady=(15, 0), anchor='n', expand=True, fill='both')
        
        self.queue_top_frame = ctk.CTkFrame(self.queue_frame)
        self.queue_top_frame.pack(padx=15, pady=(5, 5), anchor='n', expand=True, fill='both')
        
        self.queue_top_frame.grid_rowconfigure(0, weight=1, uniform='queue')
        self.queue_top_frame.grid_columnconfigure(0, weight=1, uniform='queue')
        self.queue_top_frame.grid_columnconfigure(1, weight=1, uniform='queue')
        self.queue_top_frame.grid_columnconfigure(2, weight=1, uniform='queue')
        
        self.queue_label = ctk.CTkLabel(self.queue_top_frame, text="Queue", font=("Arial", 15), width=0, height=0)
        self.queue_label.grid(row=0, column=1, padx=0, pady=(0, 0))
        
        self.queue_clear_button = ctk.CTkButton(self.queue_top_frame, text="Clear", command=self.clear_queue, width=30, height=10, corner_radius=5)
        self.queue_clear_button.grid(row=0, column=2, padx=5, pady=(0, 0), sticky='e')
        
        self.queue_listbox = CTkListbox(self.queue_frame, font=("Arial", 15), height=110) # type: ignore
        self.queue_listbox.pack(padx=15, pady=(0, 5), anchor='n', expand=True, fill='both')
        
        self.queue_config_frame = ctk.CTkFrame(self.queue_frame)
        self.queue_config_frame.pack(padx=15, pady=5, fill='x', expand=True)
        
        delete_image = Image.open(r"AI/assets/delete.png")
        delete_image = ctk.CTkImage(delete_image, delete_image, (35, 35))
        
        details_image = Image.open(r"AI/assets/open_in_new.png")
        details_image = ctk.CTkImage(details_image, details_image, (35, 35))
        
        self.queue_delete_button = ctk.CTkButton(self.queue_config_frame, text="", image=delete_image, command=self.delete_queue_item)
        self.queue_delete_button.pack(padx=5, pady=5, side=tk.LEFT, expand=True, fill='x')
        
        self.queue_details_button = ctk.CTkButton(self.queue_config_frame, text="", image=details_image, command=self.show_queue_item_details)
        self.queue_details_button.pack(padx=5, pady=5, side=tk.RIGHT, expand=True, fill='x')
        
        ############################################################################################################
        
        self.start_queue_button_frame = ctk.CTkFrame(self.configuration_frame)
        self.start_queue_button_frame.pack(padx=15, pady=(15, 0), anchor='n', expand=False, fill='x')
        
        self.start_queue_button_frame.grid_rowconfigure(0, weight=1)
        self.start_queue_button_frame.grid_columnconfigure(0, weight=4)
        self.start_queue_button_frame.grid_columnconfigure(1, weight=1)
        self.start_queue_button_frame.grid_columnconfigure(2, weight=1)
        
        start_queue_image = Image.open(r"AI/assets/play_icon.png")
        start_queue_image = ctk.CTkImage(start_queue_image, start_queue_image, (35, 35))
        
        self.start_queue_button = ctk.CTkButton(self.start_queue_button_frame, text="Start Queue", image=start_queue_image, command=self.start_queue, width=30, height=20, corner_radius=5)
        self.start_queue_button.grid(row=0, column=0, padx=5, pady=(5, 5), sticky='we')
        
        skip_queue_image = Image.open(r"AI/assets/skip_next.png")
        skip_queue_image = ctk.CTkImage(skip_queue_image, skip_queue_image, (35, 35))
        
        self.skip_queue_item_button = ctk.CTkButton(self.start_queue_button_frame, text="", image=skip_queue_image, command=self.skip_queue_item, width=30, height=20, corner_radius=5)
        self.skip_queue_item_button.grid(row=0, column=1, padx=0, pady=(5, 5), sticky='we')
        self.skip_queue_item_button.configure(state=tk.DISABLED)
        
        stop_queue_image = Image.open(r"AI/assets/stop_icon.png")
        stop_queue_image = ctk.CTkImage(stop_queue_image, stop_queue_image, (35, 35))
        
        self.stop_queue_button = ctk.CTkButton(self.start_queue_button_frame, text="", image=stop_queue_image, command=self.stop_queue, width=30, height=20, corner_radius=5)
        self.stop_queue_button.grid(row=0, column=2, padx=5, pady=(5, 5), sticky='we')
        self.stop_queue_button.configure(state=tk.DISABLED)
        
        ############################################################################################################
        
        self.credit_frame = ctk.CTkFrame(self.configuration_frame)
        self.credit_frame.pack(padx=15, pady=(15, 15), anchor='s', expand=False, fill='x', side='bottom')
        
        self.credit_label = ctk.CTkLabel(self.credit_frame, text="Developed by HHG_Phoenix", font=("Arial", 18, "bold"), corner_radius=5, padx=10, pady=10)
        self.credit_label.pack(padx=15, pady=10, side='left')
        
        light_image = Image.open(r"AI/assets/phoenix_logo.png")
        
        dark_image = Image.open(r"AI/assets/phoenix_logo.png")
        
        self.credit_logo = ctk.CTkImage(light_image, dark_image, size=(90, 90))
        self.credit_logo_label = ctk.CTkLabel(self.credit_frame, image=self.credit_logo, text="", corner_radius=5, padx=10, pady=10)
        self.credit_logo_label.pack(padx=15, pady=10, side='right')
        
    def create_information_frame(self):
        self.information_frame.grid_rowconfigure(0, weight=1)
        self.information_frame.grid_columnconfigure(0, weight=3)
        self.information_frame.grid_columnconfigure(1, weight=1)
        
        ############################################################################################################
        
        self.plot_frame = ctk.CTkFrame(self.information_frame)
        self.plot_frame.grid(row=0, column=0, padx=15, pady=15, sticky='nsew')
        
        self.plot_frame.grid_rowconfigure(0, weight=1, uniform='plot')
        self.plot_frame.grid_rowconfigure(1, weight=1, uniform='plot')
        self.plot_frame.grid_columnconfigure(0, weight=1)
        
        self.loss_plot_frame = ctk.CTkFrame(self.plot_frame, height=1000, width=1000, corner_radius=5)
        self.loss_plot_frame.grid(row=1, column=0, padx=15, pady=15, sticky='nsew')
        self.data_visualizer.create_loss_plot(self.loss_plot_frame)
        
        self.mae_plot_frame = ctk.CTkFrame(self.plot_frame, height=1000, width=1000, corner_radius=5)
        self.mae_plot_frame.grid(row=0, column=0, padx=15, pady=15, sticky='nsew')
        self.data_visualizer.create_mae_plot(self.mae_plot_frame)
        
        ############################################################################################################
        
        self.stats_frame = ctk.CTkFrame(self.information_frame, fg_color="#2b2b2b")
        self.stats_frame.grid(row=0, column=1, padx=15, pady=15, sticky='nsew')
        
        self.text_stats_frame = ctk.CTkFrame(self.stats_frame, fg_color="#2b2b2b")
        self.text_stats_frame.pack(padx=0, pady=(0, 0), fill='both', expand=True, side='left')
        
        
        self.mae_frame = ctk.CTkFrame(self.text_stats_frame, fg_color="#333333")
        self.mae_frame.pack(padx=15, pady=(15, 0), fill='both', expand=True)
        
        
        # self.lowest_val_mae_frame = ctk.CTkFrame(self.mae_frame, fg_color='#077a6f')
        self.lowest_val_mae_frame = ctk.CTkFrame(self.mae_frame, fg_color='#6b0669')
        self.lowest_val_mae_frame.pack(padx=15, pady=(15, 0), fill='both', expand=True)
        
        self.lowest_val_mae_desc_label = ctk.CTkLabel(self.lowest_val_mae_frame, text="Lowest Validation MAE:", font=("Arial", 17, 'bold'))
        self.lowest_val_mae_desc_label.pack(padx=15, pady=(15, 0), expand=True, fill='y')
        
        self.lowest_val_mae_label = ctk.CTkLabel(self.lowest_val_mae_frame, text="N/A", font=("Arial", 20, 'bold'))
        self.lowest_val_mae_label.pack(padx=15, pady=(0, 15), expand=True, fill='y')
        
        self.lowest_val_mae_epoch_desc_label = ctk.CTkLabel(self.lowest_val_mae_frame, text="Epoch:", font=("Arial", 17, 'bold'))
        self.lowest_val_mae_epoch_desc_label.pack(padx=15, pady=(0, 0), expand=True, fill='y')
        
        self.lowest_val_mae_epoch_label = ctk.CTkLabel(self.lowest_val_mae_frame, text="N/A", font=("Arial", 20, 'bold'))
        self.lowest_val_mae_epoch_label.pack(padx=15, pady=(0, 15), expand=True, fill='y')
        
        
        # self.lowest_mae_frame = ctk.CTkFrame(self.mae_frame, fg_color='#6b0669')
        self.lowest_mae_frame = ctk.CTkFrame(self.mae_frame, fg_color='#077a6f')
        self.lowest_mae_frame.pack(padx=15, pady=(15, 15), fill='both', expand=True)
        
        self.lowest_mae_desc_label = ctk.CTkLabel(self.lowest_mae_frame, text="Lowest MAE:", font=("Arial", 17, 'bold'))
        self.lowest_mae_desc_label.pack(padx=15, pady=(15, 0), expand=True, fill='y')
        
        self.lowest_mae_label = ctk.CTkLabel(self.lowest_mae_frame, text="N/A", font=("Arial", 20, 'bold'))
        self.lowest_mae_label.pack(padx=15, pady=(0, 15), expand=True, fill='y')
        
        self.lowest_mae_epoch_desc_label = ctk.CTkLabel(self.lowest_mae_frame, text="Epoch:", font=("Arial", 17, 'bold'))
        self.lowest_mae_epoch_desc_label.pack(padx=15, pady=(0, 0), expand=True, fill='y')
        
        self.lowest_mae_epoch_label = ctk.CTkLabel(self.lowest_mae_frame, text="N/A", font=("Arial", 20, 'bold'))
        self.lowest_mae_epoch_label.pack(padx=15, pady=(0, 15), expand=True, fill='y')
        
        
        self.loss_frame = ctk.CTkFrame(self.text_stats_frame, fg_color="#333333")
        self.loss_frame.pack(padx=15, pady=(15, 0), fill='both', expand=True, side='bottom')
        
        
        # self.lowest_val_loss_frame = ctk.CTkFrame(self.loss_frame, fg_color='#077a6f')
        self.lowest_val_loss_frame = ctk.CTkFrame(self.loss_frame, fg_color='#6b0669')
        self.lowest_val_loss_frame.pack(padx=15, pady=(15, 0), fill='both', expand=True)
        
        self.lowest_val_loss_desc_label = ctk.CTkLabel(self.lowest_val_loss_frame, text="Lowest Validation Loss:", font=("Arial", 17, 'bold'))
        self.lowest_val_loss_desc_label.pack(padx=15, pady=(15, 0), expand=True, fill='y')
        
        self.lowest_val_loss_label = ctk.CTkLabel(self.lowest_val_loss_frame, text="N/A", font=("Arial", 20, 'bold'))
        self.lowest_val_loss_label.pack(padx=15, pady=(0, 15), expand=True, fill='y')
        
        self.lowest_val_loss_epoch_desc_label = ctk.CTkLabel(self.lowest_val_loss_frame, text="Epoch:", font=("Arial", 17, 'bold'))
        self.lowest_val_loss_epoch_desc_label.pack(padx=15, pady=(0, 0), expand=True, fill='y')
        
        self.lowest_val_loss_epoch_label = ctk.CTkLabel(self.lowest_val_loss_frame, text="N/A", font=("Arial", 20, 'bold'))
        self.lowest_val_loss_epoch_label.pack(padx=15, pady=(0, 15), expand=True, fill='y')
        
        
        # self.lowest_loss_frame = ctk.CTkFrame(self.loss_frame, fg_color='#6b0669')
        self.lowest_loss_frame = ctk.CTkFrame(self.loss_frame, fg_color='#077a6f')
        self.lowest_loss_frame.pack(padx=15, pady=(15, 15), fill='both', expand=True)
        
        self.lowest_loss_desc_label = ctk.CTkLabel(self.lowest_loss_frame, text="Lowest Loss:", font=("Arial", 17, 'bold'))
        self.lowest_loss_desc_label.pack(padx=15, pady=(15, 0), expand=True, fill='y')
        
        self.lowest_loss_label = ctk.CTkLabel(self.lowest_loss_frame, text="N/A", font=("Arial", 20, 'bold'))
        self.lowest_loss_label.pack(padx=15, pady=(0, 15), expand=True, fill='y')
        
        self.lowest_loss_epoch_desc_label = ctk.CTkLabel(self.lowest_loss_frame, text="Epoch:", font=("Arial", 17, 'bold'))
        self.lowest_loss_epoch_desc_label.pack(padx=15, pady=(0, 0), expand=True, fill='y')
        
        self.lowest_loss_epoch_label = ctk.CTkLabel(self.lowest_loss_frame, text="N/A", font=("Arial", 20, 'bold'))
        self.lowest_loss_epoch_label.pack(padx=15, pady=(0, 15), expand=True, fill='y')
        
        self.stats_value_labels = [self.lowest_val_mae_label, self.lowest_mae_label, self.lowest_val_loss_label, self.lowest_loss_label]
        self.stats_epoch_labels = [self.lowest_val_mae_epoch_label, self.lowest_mae_epoch_label, self.lowest_val_loss_epoch_label, self.lowest_loss_epoch_label]
        self.stats_frames = [self.lowest_val_mae_frame, self.lowest_mae_frame, self.lowest_val_loss_frame, self.lowest_loss_frame]
        
        self.patience_frame = ctk.CTkFrame(self.stats_frame, fg_color="#333333")
        self.patience_frame.pack(padx=15, pady=(15, 0), fill='both', expand=True, side='right')
        
        self.patience_desc_label = ctk.CTkLabel(self.patience_frame, text="Patience:", font=("Arial", 20, 'bold'))
        self.patience_desc_label.pack(padx=15, pady=(15, 0), expand=False, fill='x', side='top')
        
        self.patience_progressbar = ctk.CTkProgressBar(self.patience_frame, corner_radius=10, orientation='vertical')
        self.patience_progressbar.pack(padx=35, pady=(10, 10), expand=True, fill='both', side='top')
        self.patience_progressbar.set(100)
        
        self.patience_stats_frame = ctk.CTkFrame(self.patience_frame)
        self.patience_stats_frame.pack(padx=15, pady=(0, 15), expand=False, fill='x', side='top')
        
        self.patience_value_desc_label = ctk.CTkLabel(self.patience_stats_frame, text="Patience Remaining:", font=("Arial", 14, 'bold'))
        self.patience_value_desc_label.pack(padx=15, pady=(15, 0), expand=True, fill='x', side='top')
        
        self.patience_value_label = ctk.CTkLabel(self.patience_stats_frame, text="N/A", font=("Arial", 25, 'bold'), width=100)
        self.patience_value_label.pack(padx=15, pady=(0, 10), expand=True, fill='x', side='top')
        
        self.patience_epoch_desc_label = ctk.CTkLabel(self.patience_stats_frame, text="Epoch:", font=("Arial", 18, 'bold'))
        self.patience_epoch_desc_label.pack(padx=15, pady=(0, 0), expand=True, fill='x', side='top')
        
        self.patience_epoch_label = ctk.CTkLabel(self.patience_stats_frame, text="N/A", font=("Arial", 25, 'bold'))
        self.patience_epoch_label.pack(padx=15, pady=(0, 15), expand=True, fill='x', side='top')
        
############################################################################################################

    def select_training_data(self):
        path = filedialog.askdirectory()
        
        if path == "" or not path:
            return
        
        self.selected_training_data_path = path
        self.selected_training_data_path_basename = os.path.basename(path)
        
        self.selected_training_data_path_label.configure(text=f"Selected Training Data: \n{self.selected_training_data_path_basename}")
        
        self.found_training_data = None
        
        self.data_processor.load_training_data_wrapper(path, self.data_shift.get(), self.split_random_state.get())
        
        while self.found_training_data is None:
            self.update()
            time.sleep(0.1)
        
        if self.found_training_data == False:
            self.selected_training_data_path_label.configure(text="Selected Training Data: \nNone")
            self.selected_training_data_path = None
            self.selected_training_data_path_basename = None
            self.found_training_data = None
            return
        else:
            self.handle_save_model_configuration()
        
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
        self.handle_save_model_configuration()

    def add_to_queue(self):
        if self.selected_training_data_path is None:
            messagebox.showerror("Error", "No training data selected")
            return
        if self.selected_model_configuration_path is None:
            messagebox.showerror("Error", "No model configuration selected")
            return
        
        if self.data_processor.data_loading is True:
            messagebox.showerror("Error", "Data is still loading. Please wait.")
            return
        
        model_name_entry_content = self.model_name.get()
        
        if model_name_entry_content and model_name_entry_content != "":
            # name = model_name_entry_content
            alredy_exists_counter = 0
            for item in self.queue:
                if item.custom_model_name == model_name_entry_content:
                    alredy_exists_counter += 1
                elif re.match(rf'^{re.escape(model_name_entry_content)} \(\d+\)$', item.custom_model_name):
                    alredy_exists_counter += 1
            
            if alredy_exists_counter > 0:
                name = f"{model_name_entry_content} ({alredy_exists_counter + 1})"
            else:
                name = model_name_entry_content
            
        else:
            name = f"Model {self.model_name_counter}"
        
        self.model_name_counter += 1
        
        self.data_processor.selected_training_data_path = self.selected_training_data_path
        self.data_processor.selected_model_configuration_path = self.selected_model_configuration_path
        
        epochs = int(self.epochs.get())
        batch_size = int(self.batch_size.get())
        patience = int(self.patience.get())
        epochs_graphed = int(self.epochs_graphed.get())
        data_shift = int(self.data_shift.get())
        use_visual_data = self.use_visual_data.get()
        use_feature_selection = self.use_feature_selection.get()
        feature_selection_num_features = int(self.num_features.get())
        
        save_a_h5_model = self.save_as_h5.get()
        save_a_tflite_model = self.save_as_tflite.get()
        save_with_model_config = self.save_with_model_config.get()
        
        model_dir = self.model_dir
        
        self.data_processor.pass_training_options(self.data_visualizer, 
                                                    model_name_entry_content, 
                                                    epochs, batch_size, patience, 
                                                    epochs_graphed, data_shift, name, model_dir, 
                                                    save_a_h5_model, save_a_tflite_model, 
                                                    save_with_model_config, use_visual_data,
                                                    use_feature_selection, feature_selection_num_features)
        
        if not self.keep_config_var.get():
            self.queue.append(self.data_processor)
            
            self.data_processor = DataProcessor(self)
            self.selected_training_data_path_label.configure(text="Selected Training Data: \nNone")
            self.selected_training_data_path = None
            self.selected_training_data_path_basename = None
            
            self.select_model_configuration_label.configure(text="Model Configuration File: \nNone")
            self.selected_model_configuration_path = None
            self.selected_model_configuration_path_basename = None
            
            self.model_name.set("")
        else:
            # Manually clone attributes
            cloned_processor = DataProcessor(self)
            for attr, value in self.data_processor.__dict__.items():
                # print("attr", attr, "value", value)
                if not isinstance(value, (tk.Button, tk.Label, tk.Entry)):
                    setattr(cloned_processor, attr, value)
            
            self.queue.append(cloned_processor)
        
        self.handle_save_model_configuration()
        
        if DEBUG:
            print("###############################")
            print("Queue length", len(self.queue))
            for item in self.queue:
                print(item.custom_model_name)
            print("###############################")
        
        self.queue_listbox.insert(tk.END, name)
        
        ############################################################################################################
        
    def start_queue(self):
        if self.data_processor.data_loading is True:
            messagebox.showerror("Error", "Data is still loading. Please wait.")
            return
        self.queue_thread = threading.Thread(target=self.process_queue, daemon=True)
        self.queue_thread.start()
        
        
    def process_queue(self):
        queue = self.queue
        
        if not queue:
            messagebox.showerror("Error", "Queue is empty")
            return
        
        if self.stop_training:
            self.stop_training = False
            return
        
        self.pre_training()
        
        for i, item in enumerate(queue):
            
            self.current_queue_item = item

            if self.stop_training:
                break
            
            for value, epoch in zip(self.stats_value_labels, self.stats_epoch_labels):
                value.configure(text="N/A")
                epoch.configure(text="N/A")
                
            self.data_visualizer.clear_plots()
            
            self.patience_progressbar.set(100)
            self.patience_value_label.configure(text="N/A")
            self.patience_epoch_label.configure(text="N/A")
            
            if i != 0:
                # self.queue_listbox.delete(i-1, True)
                self.queue_listbox.insert(i-1, queue[i-1].custom_model_name, update=True)
                
            print(f"Processing {i} - {item.custom_model_name}")
            
            # self.queue_listbox.delete(i, True)
            self.queue_listbox.insert(i, f"{item.custom_model_name} - Processing", update=True)
            
            item.start_training()
            
            time.sleep(4)
            
        self.post_training(queue)
    
    def pre_training(self):
        while True:
            try:
                self.update()
                self.update_idletasks()
            
                time.sleep(0.1)
                
                self.toggle_button_state(self.start_queue_button, False)
                self.toggle_button_state(self.queue_clear_button, False)
                self.toggle_button_state(self.queue_delete_button, False)
                self.toggle_button_state(self.queue_details_button, False)
                
                self.toggle_button_state(self.skip_queue_item_button, True)
                self.toggle_button_state(self.stop_queue_button, True)
                
                break
                
            except tk.TclError:
                self.update()
                pass
            
    
    def post_training(self, queue):
        self.stop_training = False
        self.current_queue_item = None
        
        # self.queue_listbox.delete(len(queue)-1, True)
        self.queue_listbox.insert(len(queue)-1, f"{queue[-1].custom_model_name}", update=True)
        
        messagebox.showinfo("Success", "Queue processed successfully")
        
        while True:
            try:
                self.update()
                self.update_idletasks()
            
                time.sleep(0.1)
                
                self.toggle_button_state(self.start_queue_button, True)
                self.toggle_button_state(self.queue_clear_button, True)
                self.toggle_button_state(self.queue_delete_button, True)
                self.toggle_button_state(self.queue_details_button, True)
                
                self.toggle_button_state(self.skip_queue_item_button, False)
                self.toggle_button_state(self.stop_queue_button, False)
                
                break
                
            except tk.TclError:
                self.update()
                pass
            
        self.update_idletasks()
        self.update()
        time.sleep(2)
        self.update_idletasks()
        self.update()
        
        #fix listbox having double the items after training
        self.queue_listbox.delete(0, tk.END)
        
        for item in self.queue:
            self.queue_listbox.insert(tk.END, item.custom_model_name)
            
        
    def skip_queue_item(self):
        if self.current_queue_item is None:
            return
        
        self.current_queue_item.stop_training = True
        
        # self.
    
    def stop_queue(self):
        self.stop_training = True
        self.skip_queue_item()
    
    ############################################################################################################
    
    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.focus_window(self.settings_window)
            return
    
        # Define the settings parameters
        settings = self.settings
        num_settings = len(settings)
    
        # Create the settings window
        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.title("Settings")
    
        self.individual_settings_frame = ctk.CTkFrame(self.settings_window)
        self.individual_settings_frame.grid(padx=15, pady=(15, 0), sticky="nsew")
    
        # Configure grid weights for equal sizing
        for i in range(num_settings):
            self.individual_settings_frame.grid_columnconfigure(i, weight=1, uniform="settings")
        self.individual_settings_frame.grid_rowconfigure(0, weight=1)
    
        # Iterate over the settings to create frames, labels, and entries
        col = 0
        for key, (value, _, type) in settings.items():
            frame = ctk.CTkFrame(self.individual_settings_frame)
            frame.grid(row=0, column=col, padx=15, pady=15, sticky="nsew")
            frame.grid_columnconfigure(0, weight=1)
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_rowconfigure(1, weight=1)
    
            modified_key = key.replace("_", " ").title()
    
            label = ctk.CTkLabel(frame, text=modified_key, font=("Arial", 15))
            label.grid(row=0, column=0, padx=15, pady=(15, 0), sticky="nsew")
    
            if type == "int":
                entry = ctk.CTkEntry(frame, font=("Arial", 15), textvariable=value)
                entry.grid(row=1, column=0, padx=15, pady=(15, 15), sticky="nsew")
                entry.bind("<FocusOut>", lambda e: self.save_settings())
                entry.bind("<Return>", lambda e: self.save_settings())
            elif type == "bool":
                switch = ctk.CTkSwitch(frame, text="", variable=value, font=("Arial", 15), command=self.save_settings)
                switch.grid(row=1, column=0, padx=15, pady=(15, 15), sticky="nsew")
                switch.bind("<FocusOut>", lambda e: self.save_settings())
                switch.bind("<Return>", lambda e: self.save_settings())
    
            col += 1
    
        # Save settings on window close
        self.settings_window.protocol("WM_DELETE_WINDOW", lambda: self.save_settings(True))
    
        self.settings_save_button = ctk.CTkButton(
            self.settings_window,
            text="Save",
            command=lambda: self.save_settings(True),
            height=40,
            font=("Arial", 15)
        )
        self.settings_save_button.grid(row=1, column=0, columnspan=num_settings, padx=15, pady=15, sticky="nsew")
    
        self.focus_window(self.settings_window)
        
    def select_output_directory(self):
        path = filedialog.askdirectory()
        
        if path == "" or not path:
            return
        
        self.model_dir = path
        self.select_output_directory_button.configure(text=f"{os.path.basename(path)}")
        self.select_output_directory_button.configure(fg_color="#1F6AA5")
        
        self.handle_save_model_configuration()
        
    def save_settings(self, exit=False):
        settings = self.settings
        data_shift_changed = False
        if DEBUG:
            print("Saving settings")
        
        for key, (value, default, type) in settings.items():
            if type == "int":
                try:
                    numeric_value = ''.join(filter(str.isdigit, value.get()))
                    if numeric_value == '' or numeric_value == '0' or numeric_value == None:
                        int_value = default
                    else:
                        int_value = int(numeric_value)
                        if int_value <= 0:
                            int_value = default
                    
                    settings[key][0].set(int_value)
                except ValueError:
                    settings[key][0].set(default)
                    messagebox.showerror("Error", f"Invalid value for {key}. Reverting to {default}.")
                except Exception as e:
                    print(f"Error setting {key} to {value}")
                    settings[key][0].set(default)
                    
        for changed_key, (changed_value, changed_function) in self.last_data_change.items():
            current_value = int(settings[changed_key][0].get())
            if DEBUG:
                print(f"changed_key: {changed_key}, changed_value: {changed_value}, changed_function: {changed_function}; settings[changed_key][0].get(): {settings[changed_key][0].get()}, changed_value: {changed_value}")
            if current_value != int(changed_value):
                self.last_data_change[changed_key] = (current_value, changed_function)
                changed_function()
            
        with open(".config/settingsModelTrain.json", "w") as f:
            file_content = {}
            for key, (value, default, type) in settings.items():
                if type == "int":
                    file_content[key] = int(value.get())
                else:
                    file_content[key] = value.get()
            json.dump(file_content, f)
        
        if data_shift_changed:
            self.reload_training_data_wrapper()
        
        if exit:
            self.settings_window.destroy()
        
    def reload_training_data_wrapper(self):
        if DEBUG:
            print("Reloading training data")
        
        with self.reload_training_data_lock:
            if self.reload_training_data_waiting == True:
                if DEBUG:
                    print("Already waiting for data to reload")
                return
            
            self.reload_training_data_waiting = True
        
        self.reload_training_data_thread = threading.Thread(target=self.reload_training_data, daemon=True)
        self.reload_training_data_thread.start()
            
    def reload_training_data(self):
        # print("Starting while loop")
        while self.data_processor.data_loading is True:
            self.update()
            time.sleep(0.1)
        # print("Data loaded")
        
        with self.reload_training_data_lock:
            self.reload_training_data_waiting = False
        
        self.data_processor.load_training_data_wrapper(self.selected_training_data_path, self.data_shift.get(), self.split_random_state.get())
    
    def delete_queue_item(self):
        selected_index = self.queue_listbox.curselection()
        
        if not selected_index and selected_index != 0:
            messagebox.showerror("Error", "No item selected")
            return
        
        if not self.queue:
            return
        
        if DEBUG:
            try:
                print("Selected index", selected_index)
                #print the listbox content
                for i in range(self.queue_listbox.size()):
                    print(self.queue_listbox.get(i))
            except Exception as e:
                print(e)
        
        index = selected_index
        self.queue.pop(index)
        self.queue_listbox.delete(index)
    
    def show_queue_item_details(self):
        selected_index = self.queue_listbox.curselection()
        # print(selected_index)
        
        if not selected_index and selected_index != 0:
            messagebox.showerror("Error", "No item selected")
            return
        
        model_name = self.queue_listbox.get(selected_index)
        
        if selected_index in self.open_details_windows:
            self.focus_window(self.open_details_windows[selected_index])
            
        else:
            details_view = ModelDetailsWindow(self, model_name, self.queue[selected_index].model_file_content, selected_index)
            self.focus_window(details_view)
        
    def clear_queue(self):
        self.queue = []
        self.queue_listbox.delete(0, tk.END)
        
    def focus_window(self, window):
        self.update()
        self.update_idletasks()
        window.focus_force()
        window.lift()
        self.update()
        window.focus_force()
        window.lift()
        self.update()
        window.focus_force()
        

class DataProcessor:
    def __init__(self, modelTrainUI):
        self.modelTrainUI = modelTrainUI
        self.lidar_train = None
        self.image_train = None
        self.controller_train = None
        self.counter_train = None
        self.green_blocks_train = None
        self.red_blocks_train = None
        self.lidar_val = None
        self.image_val = None
        self.controller_val = None
        self.counter_val = None
        self.green_blocks_val = None
        self.red_blocks_val = None
        self.model_name = ""
        self.epochs = None
        self.batch_size = None
        self.patience = None
        self.data_shift = int(self.modelTrainUI.data_shift.get())
        self.split_random_state = int(self.modelTrainUI.split_random_state.get())
        
        self.model = None
        self.model_train_thread = None
        self.data_loading = False
        
        self.stop_training = False
        
        self.model_file_content = None
        self.model_function = None
        
        self.model_base_filename = None
        self.model_dir = None
        
        self.selected_training_data_path = None
        self.selected_model_configuration_path = None

    def pass_training_options(self, data_visualizer, model_name, epochs, batch_size, patience, epochs_graphed, data_shift, custom_model_name, model_dir, save_a_h5_model, save_a_tflite_model, save_with_model_config, use_visual_data, use_feature_selection, feature_selection_num_features):
        self.data_visualizer = data_visualizer
        self.model_name = model_name
        self.epochs = epochs
        self.batch_size = batch_size
        self.patience = patience
        self.epochs_graphed = epochs_graphed
        self.data_shift = data_shift
        self.custom_model_name = custom_model_name
        
        if self.model_name == "":
            self.model_name = str(uuid.uuid4())
        else:
            self.model_name = self.model_name.replace(" ", "_")
            
        self.model_dir = model_dir
            
        self.save_a_h5_model = save_a_h5_model
        self.save_a_tflite_model = save_a_tflite_model
        self.save_with_model_config = save_with_model_config
        self.use_visual_data = use_visual_data
        self.use_feature_selection = use_feature_selection
        self.num_features = feature_selection_num_features

    def start_training(self):
        if not self.modelTrainUI.lazy_imports_imported:
            #wait with an while loop until the imports are done, if they dont come in 10 seconds, show an error
            start_time = time.time()
            while not self.modelTrainUI.lazy_imports_imported and time.time() - start_time < 10:
                time.sleep(0.1)
                
            if not self.modelTrainUI.lazy_imports_imported:
                messagebox.showerror("Error", "Could not import necessary libraries")
                return
        
        
        if self.lidar_train is None or self.controller_train is None:
            messagebox.showerror("Error", "Probably No training data loaded?")
            if DEBUG:
                print("At least one of the training data is None")
                print(f"Lidar Train: {self.lidar_train}")
                print(f"Image Train: {self.image_train}")
                print(f"Controller Train: {self.controller_train}")
                print(f"Counter Train: {self.counter_train}")
            return
        
        
        self.train_model(self.epochs, self.batch_size, self.patience)

    def train_model(self, epochs, batch_size, patience):
        if DEBUG:
            print(f"Train LIDAR data shape: {self.lidar_train.shape}")
            print(f"Train Controller data shape: {self.controller_train.shape}")
            print(f"Train red blocks data shape: {self.red_blocks_train.shape}")
            print(f"Train green blocks data shape: {self.green_blocks_train.shape}")
            print(f"Validation LIDAR data shape: {self.lidar_val.shape}")
            print(f"Validation Controller data shape: {self.controller_val.shape}")
            print(f"Validation red blocks data shape: {self.red_blocks_val.shape}")
            print(f"Validation green blocks data shape: {self.green_blocks_val.shape}")
            
        self.generate_checkpoint_filename()
        self.check_dir_preparedness()
        
        self.red_blocks_val, self.red_blocks_val_2 = np.split(self.red_blocks_val, 2, axis=1)
        self.green_blocks_val, self.green_blocks_val_2 = np.split(self.green_blocks_val, 2, axis=1)
        
        self.red_blocks_val = np.squeeze(self.red_blocks_val, axis=1)
        self.red_blocks_val_2 = np.squeeze(self.red_blocks_val_2, axis=1)
        self.green_blocks_val = np.squeeze(self.green_blocks_val, axis=1)
        self.green_blocks_val_2 = np.squeeze(self.green_blocks_val_2, axis=1)
        
        self.red_blocks_train, self.red_blocks_train_2 = np.split(self.red_blocks_train, 2, axis=1)
        self.green_blocks_train, self.green_blocks_train_2 = np.split(self.green_blocks_train, 2, axis=1)
        self.red_blocks_train = np.squeeze(self.red_blocks_train, axis=1)
        self.red_blocks_train_2 = np.squeeze(self.red_blocks_train_2, axis=1)
        self.green_blocks_train = np.squeeze(self.green_blocks_train, axis=1)
        self.green_blocks_train_2 = np.squeeze(self.green_blocks_train_2, axis=1)
        
        # save the block arrays to txt files
        np.savetxt(f"{self.model_base_filename}_red_blocks_val.txt", self.red_blocks_val)
        np.savetxt(f"{self.model_base_filename}_green_blocks_val.txt", self.green_blocks_val)
        np.savetxt(f"{self.model_base_filename}_red_blocks_val_2.txt", self.red_blocks_val_2)
        np.savetxt(f"{self.model_base_filename}_green_blocks_val_2.txt", self.green_blocks_val_2)
        
        np.savetxt(f"{self.model_base_filename}_red_blocks_train.txt", self.red_blocks_train)
        np.savetxt(f"{self.model_base_filename}_green_blocks_train.txt", self.green_blocks_train)
        np.savetxt(f"{self.model_base_filename}_red_blocks_train_2.txt", self.red_blocks_train_2)
        np.savetxt(f"{self.model_base_filename}_green_blocks_train_2.txt", self.green_blocks_train_2)
            
        try:
            # Remove the second entry in the last dimension
            self.lidar_train = self.lidar_train[:, :, 1:]
            self.lidar_val = self.lidar_val[:, :, 1:]
            
            # Reshape to 2D
            lidar_train_flat = self.lidar_train.reshape(self.lidar_train.shape[0], -1)
            lidar_val_flat = self.lidar_val.reshape(self.lidar_val.shape[0], -1)
            if DEBUG:
                print(f"Training LIDAR data shape: {lidar_train_flat.shape}")
            
            if self.use_feature_selection:
                k = min(self.num_features, lidar_train_flat.shape[1])
                selector = SelectKBest(score_func=f_classif, k=k)
                
                self.lidar_train_selected = selector.fit_transform(lidar_train_flat, self.controller_train)
                self.lidar_val_selected = selector.transform(lidar_val_flat)
                
                # Save selected feature indices
                feature_indices = selector.get_support(indices=True)
                if DEBUG:
                    print(f"Selected features: {feature_indices}, path: {self.model_base_filename}_features.txt")
                with open(f"{self.model_base_filename}_features.txt", "w") as f:
                    for idx in feature_indices:
                        f.write(f"{idx}\n")
                lidar_input_shape = self.lidar_train_selected.shape[1]
            else:
                lidar_input_shape = lidar_train_flat.shape[1]
                self.lidar_train_selected = lidar_train_flat
                self.lidar_val_selected = lidar_val_flat
            
            # Initialize the model
            if self.use_visual_data:
                self.model = self.model_function(lidar_input_shape=(lidar_input_shape, 1),
                                                 red_blocks_input_shape=(self.red_blocks_train.shape[1], 1),
                                                 green_blocks_input_shape=(self.green_blocks_train.shape[1], 1),
                                                 red_blocks_input_shape_2=(self.red_blocks_train_2.shape[1], 1),
                                                 green_blocks_input_shape_2=(self.green_blocks_train_2.shape[1], 1))
            else:
                self.model = self.model_function(lidar_input_shape=(lidar_input_shape, 1))
        except TypeError as e:
            messagebox.showerror("Model Function Error", f"Error while initializing model functions: {e}")
            return

        self.model.compile(optimizer='adam', loss='mean_squared_error', metrics=['mae'])
        
        early_stopping = EarlyStopping(monitor='val_loss', patience=patience)
        
        self.h5_model_path = f"{self.model_base_filename}.h5"
        
        model_checkpoint = ModelCheckpoint(self.h5_model_path, monitor='val_loss', save_best_only=True)
        
        data_callback = TrainingDataCallback(self.modelTrainUI, self.data_visualizer, self, epochs_graphed=self.epochs_graphed)
        
        stop_training_callback = StopTrainingCallback(self)
        
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.2,  # Reduce by 80%
            patience=5,   # Wait 5 epochs with no improvement
            min_lr=1e-6,  # Don't go below this learning rate
            verbose=1     # Print message when reducing learning rate
        )
        

        
        if self.use_visual_data:
            history = self.model.fit(
                [self.lidar_train_selected, self.red_blocks_train, self.green_blocks_train, self.red_blocks_train_2, self.green_blocks_train_2],
                self.controller_train,
                validation_data=(
                    [self.lidar_val_selected, self.red_blocks_val, self.green_blocks_val, self.red_blocks_val_2, self.green_blocks_val_2], 
                    self.controller_val
                ),
                epochs=epochs,
                callbacks=[early_stopping, model_checkpoint, data_callback, stop_training_callback, reduce_lr],
                batch_size=batch_size
            )
        else:
            history = self.model.fit(
                self.lidar_train_selected, self.controller_train,
                validation_data=(self.lidar_val_selected, self.controller_val),
                epochs=epochs,
                callbacks=[early_stopping, model_checkpoint, data_callback, stop_training_callback],
                batch_size=batch_size
            )
        
        
        if self.save_a_tflite_model:
            print(f"Converting model {self.model_name} to tflite")
            self.tflite_model_path = f"{self.model_base_filename}.tflite"
            
            self.convert_to_tflite_model(f"{self.model_base_filename}.h5", self.tflite_model_path)
        
        if not self.save_a_h5_model:
            os.remove(self.h5_model_path)
            
        if self.save_with_model_config:
            model_config_path = f"{self.model_base_filename}_config.py"
            
            with open(model_config_path, "w") as f:
                f.write(self.model_file_content)
        
        print(f"Model {self.model_name} trained successfully")
        
    def check_dir_preparedness(self):
        while self.model_base_path and os.path.exists(self.model_base_path):
            if os.path.exists(f"{self.model_base_filename}.h5") or os.path.exists(f"{self.model_base_filename}.tflite") or os.path.exists(f"{self.model_base_filename}_config.py") or os.path.exists(f"{self.model_base_filename}_features.txt"):
                answer = messagebox.askyesno("Warning", "The model directory already exists in the main folder. The contents are going to be replaced, otherwise a reselection of the main folder is needed")
            else:
                answer = True
                
            if answer:
                if os.path.exists(f"{self.model_base_filename}.h5"):
                    os.remove(f"{self.model_base_filename}.h5")
                if os.path.exists(f"{self.model_base_filename}.tflite"):
                    os.remove(f"{self.model_base_filename}.tflite")
                if os.path.exists(f"{self.model_base_filename}_config.py"):
                    os.remove(f"{self.model_base_filename}_config.py")
                if os.path.exists(f"{self.model_base_filename}_features.txt"):
                    os.remove(f"{self.model_base_filename}_features.txt")
                break
            else:
                new_dir = None
                while not new_dir:
                    new_dir = filedialog.askdirectory()
                if new_dir and new_dir != "":
                    self.model_dir = new_dir
                    self.generate_checkpoint_filename()
        
        if self.model_base_path and not os.path.exists(self.model_base_path):
            os.makedirs(self.model_base_path)
            
    def generate_checkpoint_filename(self):
        if self.model_dir:
            self.model_base_path = os.path.join(self.model_dir, f"best_model_{self.model_name}")
            self.model_base_filename = os.path.join(self.model_base_path, f"best_model_{self.model_name}")
        else:
            self.model_base_path = f"best_model_{self.model_name}"
            self.model_base_filename = os.path.join(self.model_base_path, f"best_model_{self.model_name}")
        
    def convert_to_tflite_model(self, model_path, output_path):
        model = tf.keras.models.load_model(model_path)
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        # Set the converter settings to handle TensorList ops
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS, tf.lite.OpsSet.SELECT_TF_OPS]
        converter._experimental_lower_tensor_list_ops = False
        
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        tflite_model = converter.convert()
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
    def load_training_data_wrapper(self, folder_path, data_shift, split_random_state):
        with self.modelTrainUI.load_training_data_lock:
            if self.data_loading:
                return
            
            if DEBUG:
                print("Starting data loading thread")
            
            self.data_loading_started()
            
        self.load_training_data_thread = threading.Thread(target=self.load_training_data, args=(folder_path, data_shift, split_random_state), daemon=True)
        self.load_training_data_thread.start()

        # Python
    def load_training_data(self, folder_path, data_shift, split_random_state):
        if not folder_path or folder_path == "" or not os.path.exists(folder_path):
            messagebox.showerror("Error", "No data folder selected")
            self.data_loading_completed()
            return
        if not data_shift or data_shift == "" or not split_random_state or split_random_state == "":
            messagebox.showerror("Error", "Data shift or split random state not set")
            self.data_loading_completed()
            return
        self.data_shift = int(data_shift)
        self.split_random_state = int(split_random_state)
    
        file_count = 0
    
        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith('.npz'):
                        file_path = os.path.join(root, file)
                        np_arrays = np.load(file_path, allow_pickle=True)
                        print(np_arrays)
                        if 'lidar_data' in np_arrays and 'controller_data' in np_arrays and 'bounding_boxes_red' in np_arrays and 'bounding_boxes_green' in np_arrays and 'raw_frames' in np_arrays:
                            current_lidar_data = np_arrays['lidar_data'].astype(np.float32)
                            
                            # Remove intensity column if it exists (keep only first 2 columns: angle, distance, and one other)
                            if current_lidar_data.shape[-1] > 2:
                                current_lidar_data = current_lidar_data[:, :, :2]
                            
                            if file_count == 0:
                                lidar_data = current_lidar_data
                                controller_data = np_arrays['controller_data']
                                red_blocks = np_arrays['bounding_boxes_red']
                                green_blocks = np_arrays['bounding_boxes_green']
                                raw_frames = np_arrays['raw_frames']
                            else:
                                lidar_data = np.concatenate((lidar_data, current_lidar_data), axis=0)
                                controller_data = np.concatenate((controller_data, np_arrays['controller_data']), axis=0)
                                red_blocks = np.concatenate((red_blocks, np_arrays['bounding_boxes_red']), axis=0)
                                green_blocks = np.concatenate((green_blocks, np_arrays['bounding_boxes_green']), axis=0)
                                raw_frames = np.concatenate((raw_frames, np_arrays['raw_frames']), axis=0)
                                
                            file_count += 1
                        np_arrays = None
        except KeyError as e:
            messagebox.showerror("Error", f"Error loading data from {file_path}. {e}")
            self.modelTrainUI.found_training_data = False
            self.modelTrainUI.selected_training_data_path = None
            self.modelTrainUI.selected_training_data_path_basename = None
            self.modelTrainUI.selected_training_data_path_label.configure(text="Selected Training Data: \nNone")
            self.data_loading_completed()
            return
    
        if file_count == 0:
            messagebox.showerror("Error", "No data files found in the selected folder")
            self.modelTrainUI.found_training_data = False
            self.data_loading_completed()
            return
        else:
            self.modelTrainUI.found_training_data = True
            print(f"Successfully found and loaded {file_count} data files")
    
        # Normalize and process data
        lidar_data = lidar_data[:, :, :2] / np.array([360, 5000], dtype=np.float32)
        
        new_red_blocks = []
        for two_red_blocks in red_blocks:
            new_two_red_blocks = []
            for red_block in two_red_blocks:
                red_block = np.array(red_block, dtype=float)
                red_block[0] = float(red_block[0]) / 213.0
                red_block[1] = float(red_block[1]) / 100.0
                red_block[2] = float(red_block[2]) / 213.0
                red_block[3] = float(red_block[3]) / 100.0
                new_two_red_blocks.append(red_block)
            new_red_blocks.append(new_two_red_blocks)
                
        new_green_blocks = []
        for two_green_blocks in green_blocks:
            new_two_green_blocks = []
            for green_block in two_green_blocks:
                green_block = np.array(green_block, dtype=float)
                green_block[0] = float(green_block[0]) / 213.0
                green_block[1] = float(green_block[1]) / 100.0
                green_block[2] = float(green_block[2]) / 213.0
                green_block[3] = float(green_block[3]) / 100.0
                new_two_green_blocks.append(green_block)
            new_green_blocks.append(new_two_green_blocks)
        
        red_blocks = np.array(new_red_blocks)
        green_blocks = np.array(new_green_blocks)
        
        data_shift = int(self.data_shift)
        if data_shift != 0:
            controller_data = controller_data[data_shift:]
            lidar_data = lidar_data[:-data_shift]
            red_blocks = red_blocks[:-data_shift]
            green_blocks = green_blocks[:-data_shift]
    
        # Train-validation split
        self.lidar_train, self.lidar_val = train_test_split(lidar_data, test_size=0.2, random_state=self.split_random_state)
        self.controller_train, self.controller_val = train_test_split(controller_data, test_size=0.2, random_state=self.split_random_state)
        self.red_blocks_train, self.red_blocks_val = train_test_split(red_blocks, test_size=0.2, random_state=self.split_random_state)
        self.green_blocks_train, self.green_blocks_val = train_test_split(green_blocks, test_size=0.2, random_state=self.split_random_state)
    
        self.data_loading_completed()
        print("Data loaded successfully")
        if not self.modelTrainUI.reload_training_data_waiting:
            chime.success()
    
    def data_loading_started(self):
        self.data_loading = True
        
        self.modelTrainUI.add_to_queue_button.configure(state='disabled')
        self.modelTrainUI.add_to_queue_button.configure(text="Please wait, loading data...")
        self.modelTrainUI.add_to_queue_button.configure(fg_color='#D3031C')
        self.modelTrainUI.update_idletasks()
        
    def data_loading_completed(self):
        self.data_loading = False
        
        self.modelTrainUI.add_to_queue_button.configure(state='normal')
        self.modelTrainUI.add_to_queue_button.configure(text="Add to Queue")
        self.modelTrainUI.add_to_queue_button.configure(fg_color='#1f6aa5')
        self.modelTrainUI.update_idletasks()

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
            messagebox.showerror("Error", "The model configuration file must contain exactly one function")
            return
        
        self.model_function = functions[0]
        
    def load_model_from_content(self, content):
        try:
            # Create a new module
            module = types.ModuleType("model")
            
            # Execute the content in the new module's namespace
            exec(content, module.__dict__)
            
            # Find the only function in the module
            functions = [obj for name, obj in inspect.getmembers(module) if inspect.isfunction(obj)]
            if len(functions) != 1:
                messagebox.showerror("Error", "The model configuration content must contain exactly one function")
                return
            
            self.model_function = functions[0]
        except SyntaxError as e:
            messagebox.showerror("Error", f"Syntax error in the model configuration content! Check the console for more information.")
            print(f"Syntax error in the model configuration content: {e}")
            return
        
class StopTrainingCallback(Callback):
    def __init__(self, data_processor):
        super().__init__()
        self.data_processor = data_processor
        
    def on_epoch_end(self, epoch, logs=None):
        if self.data_processor.stop_training:
            self.model.stop_training = True
            print("Training stopped by user.")

class TrainingDataCallback(Callback):
    def __init__(self, model_train_ui, data_visualizer, data_processor, epochs_graphed=50):
        super().__init__()
        self.model_train_ui = model_train_ui
        self.data_visualizer = data_visualizer
        self.data_processor = data_processor
        self.epochs_graphed = epochs_graphed

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
        
        self.color_reset_timers = {}
        self.frame_colors = {}

    def on_epoch_end(self, epoch, logs=None):
        loss = logs['loss']
        val_loss = logs['val_loss']
        mae = logs['mae']
        val_mae = logs['val_mae']
        
        current_stats_array = [
            (val_mae, epoch),
            (mae, epoch),
            (val_loss, epoch),
            (loss, epoch)
        ]
        
        def update_ui():
            for lowest_variable, epoch_number, frame, (current_variable, current_epoch) in zip(self.model_train_ui.stats_value_labels, self.model_train_ui.stats_epoch_labels, self.model_train_ui.stats_frames, current_stats_array):
                
                lowest_variable_text = lowest_variable.cget("text")
                
                current_variable = round(current_variable, 4)
                current_epoch = current_epoch + 1
                
                if lowest_variable_text == "N/A" or current_variable < float(lowest_variable_text):
                    lowest_variable.configure(text=f"{current_variable}")
                    epoch_number.configure(text=f"{current_epoch}")
                    
                    # Store the original color if not already stored
                    if frame not in self.frame_colors:
                        self.frame_colors[frame] = frame.cget('fg_color')
                    
                    old_color = self.frame_colors[frame]
                    
                    # Change the color to red
                    frame.configure(fg_color='#520606')
                    self.model_train_ui.after(300, lambda frame=frame: frame.configure(fg_color='red'))
                    self.model_train_ui.update_idletasks()
                    self.model_train_ui.update()
                    
                    # Reset the timer if it exists
                    if frame in self.color_reset_timers and self.color_reset_timers[frame] is not None:
                        self.color_reset_timers[frame].cancel()
                    
                    # Create a new timer to reset the color after 3.5 seconds
                    self.color_reset_timers[frame] = threading.Timer(3.5, lambda frame=frame, old_color=old_color: frame.configure(fg_color=old_color))
                    self.color_reset_timers[frame].start()
                    
            
            lowest_validation_mae_epoch = self.model_train_ui.lowest_val_mae_epoch_label.cget("text")
            
            epoch_since_last_improvement = epoch + 1 - int(lowest_validation_mae_epoch)
            
            remaining_patience = max(0, self.data_processor.patience - epoch_since_last_improvement)
            
            self.model_train_ui.patience_progressbar.set(remaining_patience / self.data_processor.patience)
            self.model_train_ui.patience_value_label.configure(text=f"{remaining_patience}")
            self.model_train_ui.patience_epoch_label.configure(text=f"{current_epoch}/{self.data_processor.epochs}")
        
        def update_visualization():
            if len(self.loss_values) > self.epochs_graphed:
                self.loss_values.pop(0)
                self.val_loss_values.pop(0)
                self.mae_values.pop(0)
                self.val_mae_values.pop(0)
            
            self.data_visualizer.update_loss_plot(self.loss_values, self.val_loss_values)
            self.data_visualizer.update_mae_plot(self.mae_values, self.val_mae_values)
        
        # Update UI in a separate thread
        threading.Thread(target=update_ui).start()
        
        # Append new values to lists (quick operation)
        self.loss_values.append(loss)
        self.val_loss_values.append(val_loss)
        self.mae_values.append(mae)
        self.val_mae_values.append(val_mae)
        
        # Update visualization in a separate thread
        threading.Thread(target=update_visualization).start()
        
        # Store full values for further use (quick operation)
        self.full_loss_values.append(loss)
        self.full_val_loss_values.append(val_loss)
        self.full_mae_values.append(mae)
        self.full_val_mae_values.append(val_mae)
    
    def on_train_end(self, logs=None):
        self.color_reset_timers = {}
        # self.frame_colors = {}
        
        plots_path = os.path.join(self.data_processor.model_base_path, f"plots_{self.data_processor.model_name}.png")
        
        self.data_visualizer.create_plots_after_training(self.full_loss_values, 
                                                         self.full_val_loss_values, 
                                                         self.full_mae_values, 
                                                         self.full_val_mae_values, 
                                                         plots_path, 
                                                         self.model_train_ui.lowest_val_mae_epoch_label.cget("text"), 
                                                         self.model_train_ui.lowest_val_mae_label.cget("text"),
                                                         self.model_train_ui.lowest_val_loss_label.cget("text"),
                                                         self.data_processor.batch_size,
                                                         self.data_processor.data_shift)
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
        
        self.loss_plot_axis.plot(val_loss_values, label='Validation Loss', color='magenta')
        self.loss_plot_axis.plot(loss_values, label='Training Loss', color='cyan')
        
        self.loss_plot_axis.set_xlabel('Epochs', color='white')
        self.loss_plot_axis.set_ylabel('Loss', color='white')
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
        
        self.mae_plot_axis.plot(val_mae_values, label='Validation MAE', color='magenta')
        self.mae_plot_axis.plot(mae_values, label='Training MAE', color='cyan')
        
        self.mae_plot_axis.set_xlabel('Epochs', color='white')
        self.mae_plot_axis.set_ylabel('MAE', color='white')
        self.mae_plot_axis.legend()
        
        self.mae_plot_canvas.draw()
    
    def clear_mae_plot(self):
        self.mae_plot_axis.clear()
        self.mae_plot_axis.grid(True, color='gray', linestyle='--', linewidth=0.5)
        self.mae_plot_canvas.draw()
        
    ############################################################################################################
    
    def create_plots_after_training(self, loss_values, val_loss_values, mae_values, val_mae_values, save_path, epoch, lowest_mae, lowest_loss, batch_size, shift):
        # Create a figure with two subplots
        fig, (loss_ax, mae_ax) = plt.subplots(2, 1, figsize=(10, 8), facecolor='#222222')
        
        # Customize the loss plot
        loss_ax.plot(val_loss_values, label='Validation Loss', color='red')
        loss_ax.plot(loss_values, label='Training Loss', color='blue')
        loss_ax.set_xlabel('Epochs', color='white')
        loss_ax.set_ylabel('Loss', color='white')
        loss_ax.legend()
        loss_ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
        loss_ax.tick_params(axis='x', colors='white')
        loss_ax.tick_params(axis='y', colors='white')
        for spine in loss_ax.spines.values():
            spine.set_edgecolor('white')
        loss_ax.set_title(f'Loss Plot', color='white')
        
        # Customize the MAE plot
        mae_ax.plot(val_mae_values, label='Validation MAE', color='red')
        mae_ax.plot(mae_values, label='Training MAE', color='blue')
        mae_ax.set_xlabel('Epochs', color='white')
        mae_ax.set_ylabel('MAE', color='white')
        mae_ax.legend()
        mae_ax.grid(True, color='gray', linestyle='--', linewidth=0.5)
        mae_ax.tick_params(axis='x', colors='white')
        mae_ax.tick_params(axis='y', colors='white')
        for spine in mae_ax.spines.values():
            spine.set_edgecolor('white')
        mae_ax.set_title(f'MAE Plot', color='white')
        
        # Add text annotation at the bottom
        fig.text(0.5, 0.01, f'Last Epoch: {epoch} - Batch Size: {batch_size} - Shift: {shift} - Best Validation MAE: {lowest_mae} - Best Validation Loss: {lowest_loss}', ha='center', fontsize=14, color='white')
        
        # Adjust layout
        plt.tight_layout(rect=[0, 0.03, 1, 1])
        
        # Save the figure to a file
        plt.savefig(save_path)
        
        # Close the figure to release memory
        plt.close(fig)
        
    def clear_plots(self):
        self.clear_loss_plot()
        self.clear_mae_plot()

class ModelDetailsWindow(ctk.CTkToplevel):
    def __init__(self, modelTrainUI, model_name, model_file_content, queue_id):
        super().__init__(modelTrainUI)
        self.title(f"Model Details - {model_name}")
        self.geometry("1750x860+50+50")
        self.modelTrainUI = modelTrainUI
        self.model_name = model_name
        self.model_file_content = model_file_content
        self.queue_id = queue_id
        
        self.button_disabled = True
        self.button_pressed = False
        
        self.no_questions_mode = tk.BooleanVar()
        
        self.init_window()
        self.modelTrainUI.open_details_windows[queue_id] = self
    
    def destroy(self):
        # Remove the window from the dictionary of open windows
        if self.queue_id in self.modelTrainUI.open_details_windows:
            del self.modelTrainUI.open_details_windows[self.queue_id]
        super().destroy()
    
    def init_window(self):
        self.iconbitmap(r"AI\assets\phoenix_logo.ico")
        
        # Create a frame to hold the text widget and the scrollbar
        text_frame = ctk.CTkFrame(self)
        text_frame.pack(padx=15, pady=15, fill='both', expand=True)
        
        # Adjust the font settings here
        self.model_text = ctk.CTkTextbox(text_frame, font=("Consolas", 16), wrap='none')
        self.model_text.pack(side='left', fill='both', expand=True)
        
        self.save_frame = ctk.CTkFrame(self)
        self.save_frame.pack(padx=15, pady=15, side='bottom')
        
        self.save_frame.rowconfigure(0, weight=3)
        self.save_frame.rowconfigure(1, weight=1)
        self.save_frame.columnconfigure(0, weight=1)
        self.save_frame.columnconfigure(1, weight=1)
        
        save_image = Image.open(r"AI\assets\save.png")
        save_image = ctk.CTkImage(save_image, save_image, (45, 45))
        
        save_to_file_image = Image.open(r"AI\assets\upload_file.png")
        save_to_file_image = ctk.CTkImage(save_to_file_image, save_to_file_image, (45, 45))
        
        self.save_local_button = ctk.CTkButton(self.save_frame, text="", image=save_image, command=self.save_model_local, width=45, height=45, corner_radius=5)
        self.save_local_button.grid(row=0, column=0, padx=15, pady=15)
        self.modelTrainUI.toggle_button_state(self.save_local_button, False)
        
        self.save_model_to_file_button = ctk.CTkButton(self.save_frame, text="", image=save_to_file_image, command=self.save_model_to_file, width=45, height=45, corner_radius=5)
        self.save_model_to_file_button.grid(row=0, column=1, padx=15, pady=15)
        self.modelTrainUI.toggle_button_state(self.save_model_to_file_button, False)
        
        self.no_questions_mode_checkbox = ctk.CTkCheckBox(self.save_frame, text="No Questions Mode", variable=self.no_questions_mode, font=("Arial", 15))
        self.no_questions_mode_checkbox.grid(row=1, column=0, columnspan=2, padx=15, pady=15)
        
        self.model_text.insert(tk.END, self.model_file_content)
        self.setup_syntax_highlighting()
        self.apply_syntax_highlighting(self.model_file_content)
        
        # Bind the KeyRelease event to apply syntax highlighting on the fly
        self.model_text.bind("<KeyRelease>", self.on_key_release)
        
        self.protocol("WM_DELETE_WINDOW", self.close)
    
    def setup_syntax_highlighting(self):
        # Set up the Pygments style for syntax highlighting
        style = get_style_by_name("lightbulb")
        self.tags = {}
        
        for token, style_data in style:
            foreground_color = style_data['color']
            if foreground_color:
                tag_name = str(token)
                self.model_text.tag_config(tag_name, foreground=f"#{foreground_color}")
                self.tags[token] = tag_name
    
    def on_key_release(self, event=None):
        # Get the current content of the text widget
        code = self.model_text.get("1.0", tk.END)
        self.apply_syntax_highlighting(code)
        
        file_changed = code.replace(" ", "").replace("\n", "") != self.model_file_content.replace(" ", "").replace("\n", "")
        
        if file_changed and self.button_disabled:
            self.modelTrainUI.toggle_button_state(self.save_local_button, True)
            self.modelTrainUI.toggle_button_state(self.save_model_to_file_button, True)
            self.button_disabled = False
        elif not file_changed and not self.button_disabled:
            if not self.button_pressed:
                self.modelTrainUI.toggle_button_state(self.save_local_button, False)
                self.modelTrainUI.toggle_button_state(self.save_model_to_file_button, False)
            self.button_disabled = True
    
    def apply_syntax_highlighting(self, code):
        # Remove previous highlighting
        for tag in self.tags.values():
            self.model_text.tag_remove(tag, "1.0", tk.END)
        
        # Track the position in the text widget
        position = 0
        
        for token, content in lex(code, PythonLexer()):
            start_index = self.model_text.index(f"1.0 + {position} chars")
            position += len(content)
            end_index = self.model_text.index(f"1.0 + {position} chars")
            tag_name = str(token)
            self.model_text.tag_add(tag_name, start_index, end_index)
        
        self.model_text.update_idletasks()
    
    def close(self):
        self.destroy()
    
    def save_model_local(self):
        if not self.no_questions_mode.get():
            answer = messagebox.askyesno("Save Model", "Are you sure you want to overwrite the model configuration for this model?")
        else:
            answer = True
        
        if not answer:
            return
        
        self.button_pressed = True
        
        self.modelTrainUI.queue[self.queue_id].load_model_from_content(self.model_text.get("1.0", tk.END))
        self.modelTrainUI.queue[self.queue_id].model_file_content = self.model_text.get("1.0", tk.END)
    
    def save_model_to_file(self):
        if not self.no_questions_mode.get():
            answer = messagebox.askyesno("Save Model", "Are you sure you want to overwrite the model configuration FILE for this model? This will overwrite the file on disk.")
        else:
            answer = True
        
        if not answer:
            return
        
        self.button_pressed = True
        
        if not self.no_questions_mode.get():
            answer = messagebox.askyesno("Reselect Model Configuration", "Would you like to reselect where to save the model configuration file?")
        else:
            answer = False
        
        if answer:
            path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
            
            if path == "" or not path:
                return
            
            if not path.endswith(".py"):
                answer = messagebox.askyesno("Bad File Extension", "The selected file is not a Python file. Would you like to continue?")
                if not answer:
                    return
            
            with open(path, 'r') as file:
                file_content = file.read()
                if file_content.replace(" ", "").replace("\n", "") != self.model_file_content.replace(" ", "").replace("\n", ""):
                    answer = messagebox.askyesno("Overwrite File", "The selected file already contains data which is different from the current model configuration. Would you like to overwrite it?")
                    if not answer:
                        return
            
            with open(path, 'w') as file:
                file.write(self.model_text.get("1.0", tk.END))
                
        else:
            with open(self.modelTrainUI.queue[self.queue_id].selected_model_configuration_path, 'w') as file:
                file.write(self.model_text.get("1.0", tk.END))

if __name__ == "__main__":
    modelTrainUI()