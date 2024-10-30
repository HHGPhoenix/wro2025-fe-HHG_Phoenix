print("Importing nessesary modules...")
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

global DEBUG, TRAIN_VAL_SPLIT_RANDOM_STATE

DEBUG = True

TRAIN_VAL_SPLIT_RANDOM_STATE = 42

############################################################################################################

class modelTrainUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Model Training")
        self.geometry("+50+50")
        self.minsize(height=1050, width=1500)
        
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
        self.epochs_default = 10
        self.batch_size_default = 32
        self.patience_default = 5
        self.epochs_graphed_default = 50
        self.data_shift_default = 0
        
        self.epochs = tk.StringVar(value=self.epochs_default)
        self.batch_size = tk.StringVar(value=self.batch_size_default)
        self.patience = tk.StringVar(value=self.patience_default)
        self.epochs_graphed = tk.StringVar(value=self.epochs_graphed_default)
        self.data_shift = tk.StringVar(value=self.data_shift_default)
        
        self.settings = {
            "epochs": (self.epochs, self.epochs_default),
            "batch_size": (self.batch_size, self.batch_size_default),
            "patience": (self.patience, self.patience_default),
            "epochs_graphed": (self.epochs_graphed, self.epochs_graphed_default),
            "data_shift": (self.data_shift, self.data_shift_default),
        }
        
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
        global tf, EarlyStopping, ModelCheckpoint, np, FigureCanvasTkAgg, train_test_split
        import tensorflow as tf
        from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint # type: ignore
        import numpy as np
        from sklearn.model_selection import train_test_split
        
        self.lazy_imports_imported = True
        
    def handle_settings(self):
        if not os.path.exists("settings.json"):
            self.create_settings_file()
        else:
            self.load_settings()
        
    def create_settings_file(self):
        settings = self.settings
        
        with open("settings.json", "w") as f:
            file_content = {}
            for key, (value, default) in settings.items():
                file_content[key] = default
            json.dump(file_content, f)

    def load_settings(self):
        settings = self.settings
        
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f:
                    file_content = json.load(f)
                    for key, (value, default) in settings.items():
                        if key in file_content:
                            value.set(file_content[key])
            except (KeyError, json.decoder.JSONDecodeError):
                delete_or_not = messagebox.askyesno("Error", "The settings file is corrupted. Do you want to delete it? Or exit!")
                if delete_or_not:
                    os.remove("settings.json")
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
            self.data_processor.load_training_data_wrapper(self.selected_training_data_path)
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
        
        self.data_processor.load_training_data_wrapper(path)
        
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
        
        save_a_h5_model = self.save_as_h5.get()
        save_a_tflite_model = self.save_as_tflite.get()
        save_with_model_config = self.save_with_model_config.get()
        
        model_dir = self.model_dir
        
        self.data_processor.pass_training_options(self.data_visualizer, 
                                                  model_name_entry_content, 
                                                  epochs, batch_size, patience, 
                                                  epochs_graphed, name, model_dir, 
                                                  save_a_h5_model, 
                                                  save_a_tflite_model, 
                                                  save_with_model_config)
        
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
        
        self.toggle_button_state(self.start_queue_button, True)
        self.toggle_button_state(self.queue_clear_button, True)
        self.toggle_button_state(self.queue_delete_button, True)
        self.toggle_button_state(self.queue_details_button, True)
        
        self.toggle_button_state(self.skip_queue_item_button, False)
        self.toggle_button_state(self.stop_queue_button, False)
        
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
            # self.update()
            # self.settings_window.focus_force()
            self.focus_window(self.settings_window)
            return
        
        # Define the settings parameters
        settings = self.settings
        # Create the settings window
        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.title("Settings")
        
        # Iterate over the settings parameters to create frames, labels, and entries
        for key, (value, default) in settings.items():
            frame = ctk.CTkFrame(self.settings_window)
            frame.pack(side=tk.LEFT, padx=15, pady=15, anchor='n', expand=True, fill='both')
            
            modified_key = key.replace("_", " ").title()
            
            label = ctk.CTkLabel(frame, text=modified_key, font=("Arial", 15))
            label.pack(padx=15, pady=(15, 0), anchor='n', expand=True, fill='both')
            
            entry = ctk.CTkEntry(frame, font=("Arial", 15), textvariable=value)
            entry.pack(padx=15, pady=(15, 15), anchor='n', expand=True, fill='both')
            
            entry.bind("<FocusOut>", lambda e: self.save_settings())
            # bind enter key to save settings
            entry.bind("<Return>", lambda e: self.save_settings())
        
        # Bind the settings window to save settings on focus out and on close
        self.settings_window.bind("<FocusOut>", lambda e: self.save_settings())
        self.settings_window.protocol("WM_DELETE_WINDOW", lambda: self.save_settings(True))
        
        # self.update()
        # self.settings_window.focus_force()
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
        
        for key, (value, default) in settings.items():
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
        
        with open("settings.json", "w") as f:
            file_content = {}
            for key, (value, default) in settings.items():
                file_content[key] = int(value.get())
            json.dump(file_content, f)
        
        if exit:
            self.settings_window.destroy()
    
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
        self.data_loading = False
        
        self.stop_training = False
        
        self.model_file_content = None
        self.model_function = None
        
        self.model_base_filename = None
        self.model_dir = None
        
        self.selected_training_data_path = None
        self.selected_model_configuration_path = None

    def pass_training_options(self, data_visualizer, model_name, epochs, batch_size, patience, epochs_graphed, custom_model_name, model_dir, save_a_h5_model, save_a_tflite_model, save_with_model_config):
        self.data_visualizer = data_visualizer
        self.model_name = model_name
        self.epochs = epochs
        self.batch_size = batch_size
        self.patience = patience
        self.epochs_graphed = epochs_graphed
        self.custom_model_name = custom_model_name
        
        if self.model_name == "":
            self.model_name = str(uuid.uuid4())
        else:
            self.model_name = self.model_name.replace(" ", "_")
            
        self.model_dir = model_dir
            
        self.save_a_h5_model = save_a_h5_model
        self.save_a_tflite_model = save_a_tflite_model
        self.save_with_model_config = save_with_model_config

    def start_training(self):
        if not self.modelTrainUI.lazy_imports_imported:
            #wait with an while loop until the imports are done, if they dont come in 10 seconds, show an error
            start_time = time.time()
            while not self.modelTrainUI.lazy_imports_imported and time.time() - start_time < 10:
                time.sleep(0.1)
                
            if not self.modelTrainUI.lazy_imports_imported:
                messagebox.showerror("Error", "Could not import necessary libraries")
                return
        
        
        if self.lidar_train is None or self.image_train is None or self.controller_train is None or self.counter_train is None:
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
            print(f"Train Frame data shape: {self.image_train.shape}")
            print(f"Train Counter data shape: {self.counter_train.shape}")
            print(f"Validation LIDAR data shape: {self.lidar_val.shape}")
            print(f"Validation Controller data shape: {self.controller_val.shape}")
            print(f"Validation Frame data shape: {self.image_val.shape}")
            print(f"Validation Counter data shape: {self.counter_val.shape}")
        
        self.model = self.model_function(lidar_input_shape=(self.lidar_train.shape[1], self.lidar_train.shape[2], 1),
                                         frame_input_shape=(self.image_train.shape[1], self.image_train.shape[2], self.image_train.shape[3]), 
                                         counter_input_shape=(self.counter_train.shape[1], ))

        self.model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        early_stopping = EarlyStopping(monitor='val_loss', patience=patience)
        
        
        self.generate_checkpoint_filename()
        
        self.check_dir_preparedness()
            
        self.h5_model_path = f"{self.model_base_filename}.h5"
        
        model_checkpoint = ModelCheckpoint(self.h5_model_path, monitor='val_loss', save_best_only=True)
        
        data_callback = TrainingDataCallback(self.modelTrainUI, self.data_visualizer, self, epochs_graphed=self.epochs_graphed)
        
        stop_training_callback = StopTrainingCallback(self)
        
        
        history = self.model.fit(
            [self.lidar_train, self.image_train, self.counter_train], self.controller_train,
            validation_data=([self.lidar_val, self.image_val, self.counter_val], self.controller_val),
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
            if os.path.exists(f"{self.model_base_filename}.h5") or os.path.exists(f"{self.model_base_filename}.tflite") or os.path.exists(f"{self.model_base_filename}_config.py"):
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
        tflite_model = converter.convert()
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
    def load_training_data_wrapper(self, folder_path):
        if self.data_loading:
            return
        
        if DEBUG:
            print("Starting data loading thread")
        
        self.data_loading_started()
        self.load_training_data_thread = threading.Thread(target=self.load_training_data, args=(folder_path,), daemon=True)
        self.load_training_data_thread.start()

    def load_training_data(self, folder_path):
        if not folder_path:
            messagebox.showerror("Error", "No data folder selected")
            self.data_loading_completed()
            return
        
        # print(f"Loading data from {folder_path}")

        lidar_data_list = []
        image_data_list = []
        controller_data_list = []
        counter_data_list = []
        file_count = 0

        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.startswith("run_data_"):
                        file_path = os.path.join(root, file)
                        np_arrays = np.load(file_path, allow_pickle=True)
                        lidar_data_list.append(np_arrays['lidar_data'])
                        image_data_list.append(np_arrays['simplified_frames'])
                        controller_data_list.append(np_arrays['controller_data'])
                        counter_data_list.append(np_arrays['counters'])
                        file_count += 1
        except KeyError as e:
            messagebox.showerror("Error", f"Error loading data from {file_path}. {e}")
            self.modelTrainUI.found_training_data = False
            self.modelTrainUI.selected_training_data_path = None
            self.modelTrainUI.selected_training_data_path_basename = None
            self.modelTrainUI.selected_training_data_path_label.configure(text="Selected Training Data: \nNone")
            self.data_loading_completed()
            return

        
        np_arrays = None

        if not lidar_data_list or not image_data_list or not controller_data_list or not counter_data_list:
            messagebox.showerror("Error", "No data files found in the selected folder")
            self.modelTrainUI.found_training_data = False
            self.data_loading_completed()
            return
        else:
            self.modelTrainUI.found_training_data = True

        # Assuming lidar_data_list is already defined
        lidar_data = np.concatenate(lidar_data_list, axis=0)
        lidar_data_list = None

        # Extract angles and distances
        angles = lidar_data[:, :, 0]
        distances = lidar_data[:, :, 1]

        # Normalize angles and distances
        normalized_angles = angles / 360
        normalized_distances = distances / 5000

        # Combine normalized angles and distances
        new_lidar_data = np.stack((normalized_angles, normalized_distances), axis=-1)
        normalized_angles = None
        normalized_distances = None

        # If you need to keep the original shape
        lidar_data = new_lidar_data
        new_lidar_data = None
        
        simplified_image_data = np.concatenate(image_data_list, axis=0)
        
        image_data_list = None
        
        # print(f"Loaded {file_count} files")
        # print(f"Starting resizing")
        # start_time = time.time()
        # resized_frames = []
        # for frame in simplified_image_data:
        #     if len(frame.shape) == 3:  # Ensure frame has at least 3 dimensions
        #         resized_frame = np.concatenate
        #         resized_frame = np.resize(frame, (128, 128, frame.shape[2]))
        #         resized_frames.append(resized_frame)
        # print(f"Resizing took {time.time() - start_time} seconds")
        # print("Ferddig Resizing!!!!!!!!!!!!!!")
        # simplified_image_data = np.array(resized_frames)
        simplified_image_data = simplified_image_data / 255.0
        
        controller_data = np.concatenate(controller_data_list, axis=0)
        counter_data = np.concatenate(counter_data_list, axis=0)
        
        controller_data_list = None
        counter_data_list = None
        
        # print(f"Data loaded successfully. {file_count} files were loaded.")
        # while True:
        #     pass

        data_shift = int(self.modelTrainUI.data_shift.get())
        if data_shift != 0:
            controller_data = controller_data[data_shift:]
            lidar_data = lidar_data[:-data_shift]
            simplified_image_data = simplified_image_data[:-data_shift]
            counter_data = counter_data[:-data_shift]
            

        # Perform the train-validation split
        self.lidar_train, self.lidar_val = train_test_split(lidar_data, test_size=0.2, random_state=TRAIN_VAL_SPLIT_RANDOM_STATE)
        lidar_data = None
        
        self.image_train, self.image_val = train_test_split(simplified_image_data, test_size=0.2, random_state=TRAIN_VAL_SPLIT_RANDOM_STATE)
        simplified_image_data = None
        
        self.controller_train, self.controller_val = train_test_split(controller_data, test_size=0.2, random_state=TRAIN_VAL_SPLIT_RANDOM_STATE)
        
        self.counter_train, self.counter_val = train_test_split(counter_data, test_size=0.2, random_state=TRAIN_VAL_SPLIT_RANDOM_STATE)
        
        self.data_loading_completed()

        # messagebox.showinfo("Success", f"Data loaded successfully. {file_count} files were loaded.")
        print("Data loaded successfully")
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
        self.data_visualizer.create_plots_after_training(self.full_loss_values, self.full_val_loss_values, self.full_mae_values, self.full_val_mae_values, f"plots_{self.data_processor.model_name}.png")

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
    
    def create_plots_after_training(self, loss_values, val_loss_values, mae_values, val_mae_values, save_path):
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
        
        # Adjust layout
        plt.tight_layout()
        
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