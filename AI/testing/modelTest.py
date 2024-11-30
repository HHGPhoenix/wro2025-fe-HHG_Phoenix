print("Importing libraries...")
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading
import time
import platform
import os
from PIL import Image, ImageTk
import signal
import json  
print("\rImported libraries")

USE_VISUALS = True  
NO_PIC = False

############################################################################################################


class ModelTestUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Model Test")
        self.minsize(height=950, width=1500)
        self.tensorflow_imported = False
        self.thread_lazy_imports = threading.Thread(target=self.import_lazy_imports, daemon=True)
        self.thread_lazy_imports.start()
        
        self.data_processor = DataProcessing(self)
    
        # Initialize vars
        self.model_path = None
        self.comparison_file = None
        self.visual_model_path = ""
        self.visual_comparison_files = ""
        self.model_loaded = False
        self.paused = False
        self.stopped = True
        self.frame_rate = tk.IntVar(self, 5)

        self.protocol("WM_DELETE_WINDOW", self.close)
        signal.signal(signal.SIGINT, self.close)

        self.import_assets()

        self.init_window()

        self.load_settings()
        
        self.mainloop()

    def save_settings(self):
        settings = {
            'model_path': self.model_path,
            'comparison_file': self.comparison_file
        }
        
        if not os.path.exists('.config'):
            os.makedirs('.config')
        
        with open('.config/settingsModelTest.json', 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        if os.path.exists('.config/settingsModelTest.json'):
            with open('.config/settingsModelTest.json', 'r') as f:
                settings = json.load(f)
                self.model_path = settings.get('model_path')
                self.comparison_file = settings.get('comparison_file')
                if self.model_path and os.path.exists(self.model_path):
                    self.visual_model_path = os.path.basename(self.model_path)
                    self.selected_model_label.configure(text="Selected Model: \n" + self.visual_model_path)
                    self.data_processor.load_model_wrapper(self.model_path)
                else:
                    self.model_path = None
                if self.comparison_file and os.path.exists(self.comparison_file):
                    self.visual_comparison_files = os.path.basename(self.comparison_file)
                    self.selected_comparison_file_label.configure(text="Selected Comparison File: \n" + self.visual_comparison_files)
                    self.data_processor.load_comparison_file(self.comparison_file)
                else:
                    self.comparison_file = None

    def close(self, *args):
        self.stopped = True
        self.quit()  # Stop the main loop
        os._exit(0)

    def import_lazy_imports(self):
        global tf
        import tensorflow as tf
        self.tensorflow_imported = True

    def import_assets(self):
        pause_icon_image = ctk.CTkImage(Image.open(r"AI/assets/pause_icon.png"), Image.open(r"AI/assets/pause_icon.png"), size=(90, 90))
        self.pause_icon = pause_icon_image

        play_icon_image = ctk.CTkImage(Image.open(r"AI/assets/play_icon.png"), Image.open(r"AI/assets/play_icon.png"), size=(90, 90))
        self.play_icon = play_icon_image

        stop_icon_image = ctk.CTkImage(Image.open(r"AI/assets/stop_icon.png"), Image.open(r"AI/assets/stop_icon.png"), size=(90, 90))
        self.stop_icon = stop_icon_image
        
    def init_window(self):
        if platform.system() == "Windows":
            self.iconbitmap(r"AI/assets/phoenix_logo.ico")
        
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

        self.create_configuration_section()
        
        self.create_information_section()
            
############################################################################################################

    def create_configuration_section(self):
        # Select Model Frame
        self.select_model_frame = ctk.CTkFrame(self.configuration_frame)
        self.select_model_frame.pack(padx=15, pady=(15, 0), anchor='n', expand=False, fill='x')

        self.select_model_button = ctk.CTkButton(self.select_model_frame, text="Select Model", font=("Arial", 15), command=self.get_model_path)
        self.select_model_button.pack(padx=15, pady=10, anchor='n', expand=True, fill='both')

        self.selected_model_label = ctk.CTkLabel(self.select_model_frame, text="Selected Model: \nNone", font=("Arial", 15), fg_color="#6b695f", corner_radius=5, padx=10, pady=10)
        self.selected_model_label.pack(padx=15, pady=10, anchor='n', expand=True, fill='both')

        ############################################################################################

        # Select Comparison File Frame
        self.select_comparison_file_frame = ctk.CTkFrame(self.configuration_frame)
        self.select_comparison_file_frame.pack(padx=15, pady=(15, 0), anchor='n', expand=False, fill='x')

        self.select_comparison_file_button = ctk.CTkButton(self.select_comparison_file_frame, text="Select Comparison File", font=("Arial", 15), command=self.get_comparison_file)
        self.select_comparison_file_button.pack(padx=15, pady=10, anchor='n', expand=True, fill='both')

        self.selected_comparison_file_label = ctk.CTkLabel(self.select_comparison_file_frame, text="Selected Comparison File: \nNone", font=("Arial", 15), fg_color="#6b695f", corner_radius=5, padx=10, pady=10)
        self.selected_comparison_file_label.pack(padx=15, pady=10, anchor='n', expand=True, fill='both')

        ############################################################################################

        self.slider_frame = ctk.CTkFrame(self.configuration_frame)
        self.slider_frame.pack(padx=15, pady=(15, 0), anchor='n', expand=False, fill='x')

        # self.frfg_color="#6b695f"

        self.frame_rate_label_frame = ctk.CTkFrame(self.slider_frame, corner_radius=5, fg_color="#6b695f")
        self.frame_rate_label_frame.pack(padx=15, pady=10, anchor='n', expand=True, fill='both')

        self.frame_rate_label = ctk.CTkLabel(self.frame_rate_label_frame, text=f"Frame Rate: {self.frame_rate.get()} FPS", font=("Arial", 15), fg_color='transparent', bg_color='transparent', padx=10, pady=5)
        self.frame_rate_label.pack(padx=15, pady=10, anchor='n', expand=True, fill='both')

        self.frame_rate_slider = ctk.CTkSlider(self.slider_frame, from_=1, to=30, variable=self.frame_rate, command=self.set_frame_rate)
        self.frame_rate_slider.pack(padx=15, pady=10, anchor='n', expand=True, fill='both')

        ############################################################################################

        self.start_stop_grid = ctk.CTkFrame(self.configuration_frame)
        self.start_stop_grid.pack(padx=15, pady=(15, 0), anchor='n', expand=False, fill='x')

        self.start_stop_grid.grid_rowconfigure(0, weight=1)
        self.start_stop_grid.grid_columnconfigure(0, weight=1)
        self.start_stop_grid.grid_columnconfigure(1, weight=1)

        # Run Test Button
        self.run_comparison_button = ctk.CTkButton(self.start_stop_grid, width=200, height=100, image=self.play_icon, text="", font=("Arial", 80), command=self.play_or_pause)
        self.run_comparison_button.grid(row=0, column=0, padx=15, pady=10)

        self.stop_comparison_button = ctk.CTkButton(self.start_stop_grid, width=200, height=100, image=self.stop_icon, text="", font=("Arial", 65), command=self.stop_comparison, state=tk.DISABLED, fg_color='#0d2b42')
        self.stop_comparison_button.grid(row=0, column=1, padx=15, pady=10)

        ############################################################################################
    
        self.data_processor.data_visualizer.create_text_output(self.configuration_frame)

        ############################################################################################

        self.counter_frame = ctk.CTkFrame(self.configuration_frame)
        self.counter_frame.pack(padx=15, pady=(15, 5), anchor='n', expand=False, fill='x')

        self.counter_frame.grid_rowconfigure(0, weight=1)
        self.counter_frame.grid_columnconfigure(0, weight=1)
        self.counter_frame.grid_columnconfigure(1, weight=1)

        self.counter_1_frame = ctk.CTkFrame(self.counter_frame, corner_radius=25, fg_color="green")
        self.counter_1_frame.grid(row=0, column=0, padx=15, pady=10, sticky='ew')

        # Removed corner_radius from CTkLabel and set fg_color as None to make it transparent
        self.counter_1 = ctk.CTkLabel(self.counter_1_frame, text="0", font=("Arial", 40, "bold"), fg_color='transparent', bg_color='transparent')
        self.counter_1.pack(padx=20, pady=20, expand=True, fill='both')

        self.counter_2_frame = ctk.CTkFrame(self.counter_frame, corner_radius=25, fg_color="red")
        self.counter_2_frame.grid(row=0, column=1, padx=15, pady=10, sticky='ew')

        # Removed corner_radius from CTkLabel and set fg_color as None to make it transparent
        self.counter_2 = ctk.CTkLabel(self.counter_2_frame, text="0", font=("Arial", 40, "bold"), fg_color='transparent', bg_color='transparent')
        self.counter_2.pack(padx=20, pady=20, expand=True, fill='both')

        ############################################################################################
        self.credit_frame = ctk.CTkFrame(self.configuration_frame)
        self.credit_frame.pack(padx=15, pady=(15, 15), anchor='s', expand=False, fill='x', side='bottom')

        self.credit_label = ctk.CTkLabel(self.credit_frame, text="Developed by HHG_Phoenix", font=("Arial", 18, "bold"), corner_radius=5, padx=10, pady=10)
        self.credit_label.pack(padx=15, pady=10, side='left')

        light_image = Image.open(r"AI/assets/phoenix_logo.png")

        dark_image = Image.open(r"AI/assets/phoenix_logo.png")

        self.credit_logo = ctk.CTkImage(light_image, dark_image, size=(90, 90))
        self.credit_logo_label = ctk.CTkLabel(self.credit_frame, image=self.credit_logo, text="", corner_radius=5, padx=10, pady=10)
        self.credit_logo_label.pack(padx=15, pady=10, side='right')


    def create_information_section(self):
        # Configure grid weights for automatic resizing
        self.information_frame.grid_rowconfigure(0, weight=1)
        self.information_frame.grid_rowconfigure(1, weight=1)
        self.information_frame.grid_columnconfigure(0, weight=1)
        self.information_frame.grid_columnconfigure(1, weight=1)

        self.polar_plot_frame = ctk.CTkFrame(self.information_frame, fg_color="#222222", bg_color="#222222")
        self.polar_plot_frame.grid(row=0, column=0, sticky='nsew')
        self.data_processor.data_visualizer.draw_polar_plot_lidar(self.polar_plot_frame)
        
        self.image_frame = ctk.CTkFrame(self.information_frame, fg_color="#222222", bg_color="#222222")
        self.image_frame.grid(row=0, column=1, sticky='nsew')
        self.data_processor.data_visualizer.draw_image_plot(self.image_frame)
        
        self.comparison_frame = ctk.CTkFrame(self.information_frame, fg_color="#222222", bg_color="#222222")
        self.comparison_frame.grid(row=1, column=0, sticky='nsew', columnspan=2)
        self.data_processor.data_visualizer.draw_model_comparison_plot(self.comparison_frame)

############################################################################################################

    def set_frame_rate(self, value):
        self.frame_rate_label.configure(text=f"Frame Rate: {int(value)} FPS")

############################################################################################################

    def get_model_path(self):
        path = filedialog.askopenfilename()

        if path == "" or path is None:
            return

        self.model_path = path
        self.visual_model_path = os.path.basename(path)
        print("Visual Model Path: ", self.visual_model_path)
        self.selected_model_label.configure(text="Selected Model: \n" + self.visual_model_path)
        self.data_processor.load_model_wrapper(self.model_path)

        # Save settings after selecting model
        self.save_settings()

    def get_comparison_file(self):
        path = filedialog.askopenfilename()

        if path == "" or path is None:
            return

        self.comparison_file = path
        self.visual_comparison_files = os.path.basename(path)
        print("Visual Comparison File: ", self.visual_comparison_files)
        self.selected_comparison_file_label.configure(text="Selected Comparison File: \n" + self.visual_comparison_files)
        self.data_processor.load_comparison_file(self.comparison_file)

        # Save settings after selecting comparison file
        self.save_settings()

    def run_comparison(self):
        if self.stopped == False:
            return
        
        if self.data_processor.model is None:
            messagebox.showerror("Error", "No model selected")
            return
        
        if (self.data_processor.lidar_data is None or self.data_processor.simplified_image_data is None or 
            self.data_processor.controller_data is None or self.data_processor.counter_data is None):
            messagebox.showerror("Error", "No comparison file selected")
            return
        
        self.stopped = False
        self.paused = False
        # self.toggle_button_state(self.run_comparison_button, False)
        self.toggle_button_state(self.stop_comparison_button, True)

        self.data_processor.start_comparison_thread()

    def pause_comparison(self):
        self.paused = not self.paused
        self.toggle_play_pause_button()

    def stop_comparison(self):
        self.stopped = True
        self.paused = False
        
        while self.data_processor.processing:
            self.update()
            self.update_idletasks()
            time.sleep(0.05)
        
        # self.toggle_button_state(self.run_comparison_button, True)
        self.toggle_button_state(self.stop_comparison_button, False)

        self.toggle_button_state(self.select_model_button, True)
        self.toggle_button_state(self.select_comparison_file_button, True)

        self.data_processor.data_visualizer.clear_all_plots()
        self.data_processor.controller_values = []
        self.data_processor.model_values = []

        self.toggle_play_pause_button()

    ############################################################################################################

    def toggle_button_state(self, button, state=True):
        if state:
            button.configure(state=tk.NORMAL)
            button.configure(fg_color='#1F6AA5')
        else:
            button.configure(state=tk.DISABLED)
            button.configure(fg_color='#0d2b42')

        self.update()
        self.update_idletasks()

    def toggle_play_pause_button(self):
        if self.paused or self.stopped:
            self.run_comparison_button.configure(image=self.play_icon)
        else:
            self.run_comparison_button.configure(image=self.pause_icon)

        self.update()
        self.update_idletasks()

    def play_or_pause(self):
        if self.stopped:
            self.toggle_button_state(self.select_model_button, False)
            self.toggle_button_state(self.select_comparison_file_button, False)
            self.run_comparison()
            self.toggle_play_pause_button()
        else:
            self.pause_comparison()


############################################################################################################
class DataProcessing:
    def __init__(self, modelTestUI):
        self.model = None
        self.lidar_data = None
        self.simplified_image_data = None
        self.controller_data = None
        self.counter_data = None
        self.model_type = ""
        self.controller_values = []
        self.model_values = []
        self.modelTestUI = modelTestUI

        self.data_visualizer = VisualizeData(self.modelTestUI)
        
    def start_comparison_thread(self):
        self.processing_thread = threading.Thread(target=self.process_data, daemon=True)
        print("Starting processing thread")
        self.processing_thread.start()
        
    
    def process_data(self):
        self.processing = True
        for i in range(self.lidar_data.shape[0]):
            start_time = time.time()
            interval = 1 / self.modelTestUI.frame_rate.get()
            
            while self.modelTestUI.paused:
                time.sleep(0.1)
                
            if self.modelTestUI.stopped:
                break
            
            lidar_array = self.lidar_data[i]
            image_array = self.simplified_image_data[i]
            controller_value = self.controller_data[i]
            counters = self.counter_data[i]
            red_block = self.block_data[0][i]
            green_block = self.block_data[1][i]
            
            # Replace image_array with zeros if NO_PIC is True
            if NO_PIC:
                image_array = np.zeros_like(image_array)
            
            # Convert to NumPy array and reshape
            angles = lidar_array[:, 0]
            distances = lidar_array[:, 1]
            
            normalized_angles = angles / 360
            normalized_distances = distances / 5000
            
            new_lidar_data = np.stack((normalized_angles, normalized_distances), axis=-1)
            
            new_lidar_data = np.expand_dims(new_lidar_data, axis=-1)  # Expand dims to shape (None, 279, 2, 1)
            new_lidar_data = np.expand_dims(new_lidar_data, axis=0)
            
            red_block = red_block / np.array([213, 100, 213, 100])
            green_block = green_block / np.array([213, 100, 213, 100])
            red_block = np.expand_dims(red_block, axis=0)
            green_block = np.expand_dims(green_block, axis=0)
            
            # Ensure new_lidar_data matches the expected input shape
            if self.model_type == "tflite":
                input_details = self.model.get_input_details()
                expected_shape = input_details[0]['shape']
                new_lidar_data = np.resize(new_lidar_data, expected_shape)
            
            if USE_VISUALS:
                model_input = [new_lidar_data, red_block, green_block]
            else:
                model_input = [new_lidar_data]
            
            model_start_time = time.time()
            
            if self.model_type == "h5":
                model_output = self.model.predict(model_input)[0][0]
            elif self.model_type == "tflite":
                self.model.set_tensor(self.model.get_input_details()[0]['index'], model_input[0].astype(np.float32))
                if USE_VISUALS:
                    self.model.set_tensor(self.model.get_input_details()[1]['index'], model_input[1].astype(np.float32))
                    self.model.set_tensor(self.model.get_input_details()[2]['index'], model_input[2].astype(np.float32))
                self.model.invoke()
                model_output = self.model.get_tensor(self.model.get_output_details()[0]['index'])[0][0]
            
            print("Model Output: ", model_output)
            model_stop_time = time.time()
    
            self.data_visualizer.update_polar_plot_lidar(lidar_array)
            if USE_VISUALS:
                self.data_visualizer.update_image_plot(image_array)
            
            self.controller_values.append(controller_value)
            self.model_values.append(model_output)
            self.data_visualizer.update_model_comparison_plot(self.model_values, self.controller_values)
            self.data_visualizer.update_text_output(controller_value, model_output, model_stop_time - model_start_time)
            
            if len(self.controller_values) > 50:
                self.controller_values.pop(0)
                self.model_values.pop(0)
            
            if USE_VISUALS:
                self.modelTestUI.counter_1.configure(text=str(round(float(counters[0]), 2)))
                self.modelTestUI.counter_2.configure(text=str(round(float(counters[1]), 2)))
            
            elapsed_time = time.time() - start_time
            sleep_time = max(0, interval - elapsed_time)
            time.sleep(sleep_time)
            
        self.processing = False
            
    def load_comparison_file(self, comparison_file_path):
        if comparison_file_path is None:
            messagebox.showerror("Error", "No comparison file selected")
            return

        np_arrays = np.load(comparison_file_path, allow_pickle=True)
        self.lidar_data = np_arrays['lidar_data']
        self.simplified_image_data = np_arrays['simplified_frames']
        self.controller_data = np_arrays['controller_data']
        self.counter_data = np_arrays['counters']
        self.block_data = np_arrays['block_data']

    def load_model_wrapper(self, model_path):
        self.load_model_thread = threading.Thread(target=self.load_model, args=(model_path,), daemon=True)
        self.load_model_thread.start()

    def load_model(self, model_path):
        while not self.modelTestUI.tensorflow_imported:
            time.sleep(0.1)
        
        # could be h5 or tflite
        if model_path.endswith(".h5"):
            self.model = tf.keras.models.load_model(model_path)
            self.model_type = "h5"
        elif model_path.endswith(".tflite"):
            self.model = tf.lite.Interpreter(model_path=model_path)
            self.model.allocate_tensors()
            self.model_type = "tflite"
        else:
            print("Model file format not supported")
            return

        self.model_loaded = True
        
############################################################################################################
        
class VisualizeData:
    def __init__(self, modelTestUI):
        self.modelTestUI = modelTestUI
        
    def clear_all_plots(self):
        self.clear_polar_plot_lidar()
        self.clear_image_plot()
        self.clear_model_comparison_plot()
        self.clear_text_output()
    
    def draw_polar_plot_lidar(self, tk_frame):
        # Create a polar plot
        self.lidar_fig, self.lidar_axis = plt.subplots(subplot_kw={'projection': 'polar'})
        
        # Set the facecolor of the figure and the axes
        self.lidar_fig.patch.set_facecolor('#222222')
        self.lidar_axis.set_facecolor('#222222')
        
        # Set the title
        self.lidar_axis.set_title("Polar Plot of LiDAR Data", color='white')
        
        # Set tick parameters to make the numbers white
        self.lidar_axis.tick_params(axis='x', colors='white')
        self.lidar_axis.tick_params(axis='y', colors='white')
        
        # Set spine color to white
        for spine in self.lidar_axis.spines.values():
            spine.set_edgecolor('white')
        
        # Set 0 degrees to be at the top
        self.lidar_axis.set_theta_offset(np.pi / 2)
        self.lidar_axis.set_theta_direction(-1)
        
        # Embed the plot into the Tkinter frame
        self.lidar_canvas = FigureCanvasTkAgg(self.lidar_fig, master=tk_frame)
        self.lidar_canvas.draw()
        self.lidar_canvas.get_tk_widget().pack()
        
        tk_frame.bind("<Configure>", self.on_resize)
        
    def on_resize(self, event):
        # Update the plot size on window resize
        self.lidar_canvas.get_tk_widget().config(width=event.width, height=event.height)
    
    def update_polar_plot_lidar(self, lidar_array):
        # Check if there are any major ticks
        if not self.lidar_axis.xaxis.majorTicks:
            self.lidar_axis.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
        # Clear the axis
        self.lidar_axis.clear()
    
        # Plot the data as individual points with neon green color
        angles, distances, _ = zip(*lidar_array)
        self.lidar_axis.scatter(np.deg2rad(angles), distances, color='#39FF14', s=10)
    
        # Set the background color of the axes
        self.lidar_axis.set_facecolor('#222222')
    
        # Set tick parameters to make the numbers white
        self.lidar_axis.tick_params(axis='x', colors='white')
        self.lidar_axis.tick_params(axis='y', colors='white')
    
        # Set spine color to white
        for spine in self.lidar_axis.spines.values():
            spine.set_edgecolor('white')
    
        # Set 0 degrees to be at the top
        self.lidar_axis.set_theta_offset(np.pi / 2)
        self.lidar_axis.set_theta_direction(-1)
    
        # Draw the plot
        self.lidar_fig.canvas.draw()
        
    def clear_polar_plot_lidar(self):
        self.lidar_axis.clear()
        self.lidar_fig.canvas.draw()

############################################################################################################
    
    def draw_image_plot(self, tk_frame):
        # Create a figure
        self.image_fig = plt.figure(facecolor='#222222', edgecolor='#222222')
    
        # Embed the plot in the Tkinter frame
        self.image_canvas = FigureCanvasTkAgg(self.image_fig, master=tk_frame)
        self.image_canvas.draw()
        self.image_canvas.get_tk_widget().pack()
        tk_frame.bind("<Configure>", self.on_resize)
        
        path = r"AI/assets/hd-bars.jpg"
        image = Image.open(path)
        resized_image = image.resize((213, 110))
        self.update_image_plot(resized_image)
    
    def on_resize(self, event):
        # Update the plot size on window resize
        self.image_canvas.get_tk_widget().config(width=event.width, height=event.height)
    
    def update_image_plot(self, image_array):
        # Clear the plot
        self.image_fig.clear()
    
        # Create a new axis with the desired background color
        self.image_axis = self.image_fig.add_subplot(111, facecolor='#222222')
    
        # Plot the image
        self.image_axis.imshow(image_array)
    
        # Remove the axes
        self.image_axis.axis('off')
    
        # Set spine color to white
        for spine in self.image_axis.spines.values():
            spine.set_edgecolor('white')
    
        # Draw the plot
        self.image_fig.canvas.draw()
        
    def clear_image_plot(self):
        path = r"AI/assets/hd-bars.jpg"
        image = Image.open(path)
        resized_image = image.resize((213, 110))
        self.update_image_plot(resized_image)
        
############################################################################################################

    def draw_model_comparison_plot(self, tk_frame):
        # Create the figure and axis
        self.comparison_fig = plt.figure(facecolor='#222222', edgecolor='#222222')
        self.comparison_axis = self.comparison_fig.add_subplot(111, facecolor='#222222')
        
        # Set tick parameters to make the numbers white
        self.comparison_axis.tick_params(axis='x', colors='white')
        self.comparison_axis.tick_params(axis='y', colors='white')
    
        # Set spine color to white
        for spine in self.comparison_axis.spines.values():
            spine.set_edgecolor('white')
    
        # Add grid to the plot
        self.comparison_axis.grid(True, color='gray', linestyle='--', linewidth=0.5)
    
        # Set y-axis limits
        self.comparison_axis.set_ylim(0, 1)
    
        # Embed the plot in the Tkinter frame
        self.comparison_canvas = FigureCanvasTkAgg(self.comparison_fig, master=tk_frame)
        self.comparison_canvas.get_tk_widget().pack(expand=True, fill='both')
    
        # Bind the resizing event
        tk_frame.bind("<Configure>", self.on_resize)
    
    def on_resize(self, event):
        # Update the plot size on window resize
        self.comparison_canvas.get_tk_widget().config(width=event.width, height=event.height)
    
    def update_model_comparison_plot(self, model_data, controller_data):
        # Clear the plot
        self.comparison_axis.clear()
    
        # Plot the data
        self.comparison_axis.plot(model_data, label='Model Data', color='cyan')
        self.comparison_axis.plot(controller_data, label='Controller Data', color='magenta')
    
        # Set the background color of the axes
        self.comparison_axis.set_facecolor('#222222')
    
        # Set tick parameters to make the numbers white
        self.comparison_axis.tick_params(axis='x', colors='white')
        self.comparison_axis.tick_params(axis='y', colors='white')
    
        # Set spine color to white
        for spine in self.comparison_axis.spines.values():
            spine.set_edgecolor('white')
    
        # Add grid to the plot
        self.comparison_axis.grid(True, color='gray', linestyle='--', linewidth=0.5)
    
        # Set y-axis limits
        self.comparison_axis.set_ylim(0, 1)
    
        # Add legend to the plot
        self.comparison_axis.legend(loc='upper left')
    
        # Draw the plot
        self.comparison_fig.canvas.draw()
        
    def clear_model_comparison_plot(self):
        self.comparison_axis.clear()
        self.comparison_axis.grid(True, color='gray', linestyle='--', linewidth=0.5)
        self.comparison_fig.canvas.draw()
        
############################################################################################################

    def create_text_output(self, tk_frame):
        # Create a text widget
        self.text_output = ctk.CTkTextbox(tk_frame, fg_color='#222222', font=('Arial', 18), corner_radius=5, padx=10, pady=10, width=0, height=0)
        self.text_output.pack(expand=True, fill='both', padx=15, pady=(15, 0))
        self.text_output.insert(tk.END, "Waiting to be started...\n")
        self.text_output.insert(tk.END, "Controller Value: 0\n")
        self.text_output.insert(tk.END, "Model Output: 0\n")
        self.text_output.configure(state=tk.DISABLED)
        
    def update_text_output(self, controller_value, model_value, model_time):
        self.text_output.configure(state=tk.NORMAL)
        self.text_output.delete("1.0", tk.END)
        self.text_output.insert(tk.END, f"1/1 [=========================] - {int(model_time * 1000)}ms/step\n")
        self.text_output.insert(tk.END, f"Controller Value: {controller_value:.2f}\n")
        self.text_output.insert(tk.END, f"Model Output: {model_value:.2f}\n")
        self.text_output.configure(state=tk.DISABLED)
        
    def clear_text_output(self):
        self.text_output.configure(state=tk.NORMAL)
        self.text_output.delete("1.0", tk.END)
        self.text_output.insert(tk.END, "Waiting to be started...\n")
        self.text_output.insert(tk.END, "Controller Value: 0\n")
        self.text_output.insert(tk.END, "Model Output: 0\n")
        self.text_output.configure(state=tk.DISABLED)

############################################################################################################

if __name__ == "__main__":
    app = ModelTestUI()
    