print("Importing libraries...")
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading
import time
import random
import os
from PIL import Image
print("\rImported libraries")

############################################################################################################

class ModelTestUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Model Test")
        # self.geometry("1200x800")
        self.tensorflow_imported = False
        self.thread_lazy_imports = threading.Thread(target=self.import_lazy_imports, daemon=True)
        self.thread_lazy_imports.start()
        
        self.data_processor = DataProcessing(self)

        # Initialize vars
        self.model_path = None
        self.comparison_file = None
        self.visual_model_path = ""
        self.visual_comparison_file = ""
        self.model_loaded = False
        self.paused = False
        self.stopped = False

        self.init_window()

        self.mainloop()

    def import_lazy_imports(self):
        global tf
        import tensorflow as tf
        self.tensorflow_imported = True
        
    def init_window(self):
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

        # Configure the grid of the frames to expand
        # self.information_frame.grid_rowconfigure(0, weight=1)
        # self.information_frame.grid_columnconfigure(0, weight=1)
        # self.configuration_frame.grid_rowconfigure(0, weight=1)
        # self.configuration_frame.grid_columnconfigure(0, weight=1)

        self.create_configuration_section()
        
        self.create_information_section()
            
############################################################################################################

    def create_configuration_section(self):
        # Select Model Frame
        self.select_model_frame = ctk.CTkFrame(self.configuration_frame)
        self.select_model_frame.pack(padx=15, pady=(15, 0), anchor='n', expand=False, fill='x')

        self.select_model_button = ctk.CTkButton(self.select_model_frame, text="Select Model", font=("Arial", 12), command=self.get_model_path)
        self.select_model_button.pack(padx=15, pady=10, anchor='n', expand=True, fill='both')

        self.selected_model_label = ctk.CTkLabel(self.select_model_frame, text="Selected Model: \nNone", font=("Arial", 12), fg_color="#6b695f", corner_radius=5, padx=10, pady=10)
        self.selected_model_label.pack(padx=15, pady=10, anchor='n', expand=True, fill='both')

        # Select Comparison File Frame
        self.select_comparison_file_frame = ctk.CTkFrame(self.configuration_frame)
        self.select_comparison_file_frame.pack(padx=15, pady=(15, 0), anchor='n', expand=False, fill='x')

        self.select_comparison_file_button = ctk.CTkButton(self.select_comparison_file_frame, text="Select Comparison File", font=("Arial", 12), command=self.get_comparison_file)
        self.select_comparison_file_button.pack(padx=15, pady=10, anchor='n', expand=True, fill='both')

        self.selected_comparison_file_label = ctk.CTkLabel(self.select_comparison_file_frame, text="Selected Comparison File: \nNone", font=("Arial", 12), fg_color="#6b695f", corner_radius=5, padx=10, pady=10)
        self.selected_comparison_file_label.pack(padx=15, pady=10, anchor='n', expand=True, fill='both')

        # Run Test Button
        self.run_comparison_button = ctk.CTkButton(self.configuration_frame, text="Run Comparison", font=("Arial", 12), command=self.data_processor.start_comparison_thread)
        self.run_comparison_button.pack(padx=15, pady=(15, 15), anchor='n', expand=False, fill='x')


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

    def get_model_path(self):
        path = filedialog.askopenfilename()
        # path = r"C:/Users/DataV3/models/linear_model.h5"
        self.model_path = path
        self.visual_model_path = os.path.basename(path)
        # print("Model Path: ", self.model_path)
        print("Visual Model Path: ", self.visual_model_path)
        self.selected_model_label.configure(text="Selected Model: \n" + self.visual_model_path)
        self.data_processor.load_model_wrapper(self.model_path)

    def get_comparison_file(self):
        path = filedialog.askopenfilename()
        # path = r"C:/Users/DataV3/models/linear_model.h5"
        self.comparison_file = path
        self.visual_comparison_files = os.path.basename(path)
        # print("Model Path: ", self.model_path)
        print("Visual Comparison File: ", self.visual_comparison_files)
        self.selected_comparison_file_label.configure(text="Selected Comparison File: \n" + self.visual_comparison_files)
        self.data_processor.load_comparison_file(self.comparison_file)

    def run_test(self):
        pass

############################################################################################################

class DataProcessing:
    def __init__(self, modelTestUI):
        self.model = None
        self.lidar_data = None
        self.simplified_image_data = None
        self.controller_data = None
        self.counter_data = None
        self.controller_values = []
        self.model_values = []
        self.modelTestUI = modelTestUI

        self.data_visualizer = VisualizeData()
        
    def start_comparison_thread(self):
        self.processing_thread = threading.Thread(target=self.process_data, daemon=True)
        print("Starting processing thread")
        self.processing_thread.start()
        
    def process_data(self):
        if self.model is None:
            print("Model not loaded yet")
            return
        
        if self.lidar_data is None or self.simplified_image_data is None or self.controller_data is None:
            print("Data not loaded yet")
            return

        for i in range(self.lidar_data.shape[0]):
            while self.modelTestUI.paused:
                time.sleep(0.1)
                
            if self.modelTestUI.stopped:
                break
            
            lidar_array = self.lidar_data[i]
            image_array = self.simplified_image_data[i]
            controller_value = self.controller_data[i]
            counters = self.counter_data[i]
            
            model_input_lidar = np.expand_dims(lidar_array, axis=0)
            model_input_image = np.expand_dims(image_array, axis=0)
            model_input_counters = np.expand_dims(counters, axis=0)
            model_input = [model_input_lidar, model_input_image, model_input_counters]
            
            model_output = self.model.predict(model_input)

            self.data_visualizer.update_polar_plot_lidar(lidar_array)
            
            self.data_visualizer.update_image_plot(image_array)
            
            self.controller_values.append(controller_value)
            self.model_values.append(model_output[0][0])
            # print("Controller Values: ", controller_values)
            # print("Model Values: ", model_values)
            self.data_visualizer.update_model_comparison_plot(self.model_values, self.controller_values)
            
            if len(self.controller_values) > 50:
                self.controller_values.pop(0)
                self.model_values.pop(0)
            
            # Sleep for 1 second
            time.sleep(0.1)
            
    def load_comparison_file(self, comparison_file_path):
        if comparison_file_path is None:
            messagebox.showerror("Error", "No comparison file selected")
            return

        np_arrays = np.load(comparison_file_path, allow_pickle=True)
        self.lidar_data = np_arrays['train_lidar']
        self.simplified_image_data = np_arrays['train_frame']
        self.controller_data = np_arrays['train_controller']
        self.counter_data = np_arrays['train_counters']

    def load_model_wrapper(self, model_path):
        self.load_model_thread = threading.Thread(target=self.load_model, args=(model_path,), daemon=True)
        self.load_model_thread.start()

    def load_model(self, model_path):
        while not self.modelTestUI.tensorflow_imported:
            time.sleep(0.1)
        self.model = tf.keras.models.load_model(model_path)
        self.model_loaded = True
        
    def run_model(self):
        pass

############################################################################################################
        
class VisualizeData:
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
        angles, distances = zip(*lidar_array)
        self.lidar_axis.scatter(angles, distances, color='#39FF14', s=10)
    
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

############################################################################################################
    
    def draw_image_plot(self, tk_frame):
        # Create a figure
        self.image_fig = plt.figure(facecolor='#222222', edgecolor='#222222')
    
        # Embed the plot in the Tkinter frame
        self.image_canvas = FigureCanvasTkAgg(self.image_fig, master=tk_frame)
        self.image_canvas.draw()
        self.image_canvas.get_tk_widget().pack()
        tk_frame.bind("<Configure>", self.on_resize)
        
        path = r"AI\modelTest\hd-bars.jpg"
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

        # Draw the plot
        self.comparison_fig.canvas.draw()

        

############################################################################################################
   
        
if __name__ == "__main__":
    app = ModelTestUI()
    