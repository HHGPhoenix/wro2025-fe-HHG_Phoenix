import tensorflow as tf
import numpy as np
import cv2
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import threading
import os
import time
from PIL import Image, ImageTk
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

class CNNModelTester(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.model = None
        self.tflite_model = None
        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.directory = ''
        self.processing = False
        self.config_file = os.path.join(os.path.expanduser("~"), ".config", "cnnModelTest.json")
        self.label_map = {0: "red_block", 1: "green_block"}
        self.load_config()
        self.setup_gui()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.model_path = config.get('model_path', None)
                self.directory = config.get('directory', '')
            if self.model_path and os.path.exists(self.model_path):
                try:
                    if self.model_path.endswith('.h5'):
                        self.model = tf.keras.models.load_model(self.model_path)
                    elif self.model_path.endswith('.tflite'):
                        self.load_tflite_model(self.model_path)
                except Exception as e:
                    print(f"Error loading model: {e}")
                    self.model = None
                    self.tflite_model = None
        else:
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            self.model_path = None
            self.directory = ''
            self.model = None
            self.tflite_model = None

    def save_config(self):
        config = {
            'model_path': self.model_path,
            'directory': self.directory
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f)

    def select_directory(self):
        self.directory = filedialog.askdirectory()
        base_name = os.path.basename(self.directory)
        self.dir_label.configure(text=f"Selected Directory: {base_name}")
        self.save_config()

    def select_model(self):
        self.model_path = filedialog.askopenfilename(filetypes=[("Model Files", "*.h5 *.tflite"), ("All Files", "*.*")])
        if self.model_path:
            self.model_label.configure(text=f"Selected Model: {self.model_path}")
            try:
                if self.model_path.endswith('.h5'):
                    self.model = tf.keras.models.load_model(self.model_path)
                    self.tflite_model = None
                elif self.model_path.endswith('.tflite'):
                    self.load_tflite_model(self.model_path)
                    self.model = None
                self.save_config()
            except Exception as e:
                print(f"Error loading model: {e}")
                self.model = None
                self.tflite_model = None

    def load_tflite_model(self, model_path):
        self.tflite_model = tf.lite.Interpreter(model_path=model_path)
        # print(f"Model input shape: {self.tflite_model.get_input_details()}")
        self.tflite_model.allocate_tensors()
        self.input_details = self.tflite_model.get_input_details()
        self.output_details = self.tflite_model.get_output_details()

    def start_processing(self):
        print("Starting image processing")
        if self.directory and (self.model or self.tflite_model) and not self.processing:
            print("Starting image processing")
            self.processing = True
            thread = threading.Thread(target=self.process_images)
            thread.start()

    def stop_processing(self):
        self.processing = False

    def process_images(self):
        image_files = []
        for root, dirs, files in os.walk(self.directory):
            for f in files:
                if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_files.append(os.path.join(root, f))
        index = 0
        print(f"Processing {len(image_files)} images")
        while self.processing and index < len(image_files):
            print(f"Processing image {index + 1}/{len(image_files)}")
            image_path = image_files[index]
            input_image = cv2.imread(image_path)
            if input_image is None:
                print(f"Failed to load image {image_path}")
                index += 1
                continue
    
            input_image_norm = np.expand_dims(input_image, axis=0) / 255.0
    
            if self.model:
                predictions = self.model.predict(input_image_norm)
            elif self.tflite_model:
                self.tflite_model.set_tensor(self.input_details[0]['index'], input_image_norm.astype(np.float32))
                start_time = time.time()    
                self.tflite_model.invoke()
                stop_time = time.time()
                print(f"Inference time: {stop_time - start_time}")
                predictions = [self.tflite_model.get_tensor(output['index']) for output in self.output_details]
    
            if len(predictions) != 2:
                print(f"Unexpected model output: {predictions}")
                index += 1
                continue
    
            if self.model:
                bounding_boxes = predictions[0][0]
                class_probs = predictions[1][0]
            elif self.tflite_model:
                bounding_boxes = predictions[1][0]
                class_probs = predictions[0][0]
    
            # Get confidence values for red_block and green_block
            red_index = None
            green_index = None
            for idx, name in self.label_map.items():
                if name == 'red_block':
                    red_index = idx
                elif name == 'green_block':
                    green_index = idx
    
            red_confidence = class_probs[red_index] if red_index is not None else 0
            green_confidence = class_probs[green_index] if green_index is not None else 0
    
            class_label = np.argmax(class_probs)
            class_name = self.label_map[class_label]
    
            x1, y1, x2, y2 = bounding_boxes
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    
            # Determine rectangle color based on class name
            if class_name == 'red_block':
                color = (0, 0, 255)  # Red in BGR
            elif class_name == 'green_block':
                color = (0, 255, 0)  # Green in BGR
            else:
                color = (255, 0, 0)  # Default to blue
    
            cv2.rectangle(input_image, (x1, y1), (x2, y2), color, 2)
    
            # Upscale the image
            upscale_factor = 2  # Adjust the upscale factor as needed
            input_image = cv2.resize(input_image, (0, 0), fx=upscale_factor, fy=upscale_factor, interpolation=cv2.INTER_LINEAR)
    
            # Set font and scale
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5  # Smaller font scale
            thickness = 1     # Thinner thickness
    
            # Positions for the text
            margin = 10  # Margin from the top and sides
            line_height = int(cv2.getTextSize('Text', font, font_scale, thickness)[0][1] + 5)
            # Position for the first line of text
            org_red = (margin, margin + line_height)
            # Position for the second line of text
            org_green = (margin, margin + 2 * line_height)
    
            # Write text on the image
            cv2.putText(input_image, f'Red Block Confidence: {red_confidence:.2f}', org_red, font, font_scale, (0, 0, 255), thickness, cv2.LINE_AA)
            cv2.putText(input_image, f'Green Block Confidence: {green_confidence:.2f}', org_green, font, font_scale, (0, 255, 0), thickness, cv2.LINE_AA)
    
            # Convert image to RGB format
            input_image_rgb = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
    
            # Display image using matplotlib
            self.ax.clear()
            self.ax.imshow(input_image_rgb)
            self.canvas.draw()
    
            time.sleep(0.08)
            index += 1

    def setup_gui(self):
        self.title("Image Processing")
        self.geometry("700x900")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        self.dir_button = ctk.CTkButton(self, text="Select Directory", command=self.select_directory)
        self.dir_button.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

        self.dir_label = ctk.CTkLabel(
            self,
            text=f"Selected Directory: {self.directory if self.directory else 'No directory selected'}"
        )
        self.dir_label.grid(row=1, column=0, pady=5, padx=10, sticky="ew")

        self.model_button = ctk.CTkButton(self, text="Select Model", command=self.select_model)
        self.model_button.grid(row=2, column=0, pady=10, padx=10, sticky="ew")

        self.model_label = ctk.CTkLabel(
            self,
            text=f"Selected Model: {self.model_path if self.model_path else 'No model selected'}"
        )
        self.model_label.grid(row=3, column=0, pady=5, padx=10, sticky="ew")

        self.start_button = ctk.CTkButton(self, text="Start", command=self.start_processing)
        self.start_button.grid(row=4, column=0, pady=10, padx=10, sticky="ew")

        self.stop_button = ctk.CTkButton(self, text="Stop", command=self.stop_processing)
        self.stop_button.grid(row=5, column=0, pady=10, padx=10, sticky="ew")

        # Set up matplotlib Figure and FigureCanvasTkAgg
        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.figure.patch.set_facecolor('black')  # Set figure background color to black
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('black')  # Set axes background color to black
        self.ax.axis('off')  # Hide axes lines and ticks
        
        # Load and display the default image
        image = plt.imread(r'AI/assets/hd-bars.jpg')
        self.ax.imshow(image, aspect='auto')
        self.ax.set_position([0, 0, 1, 1])  # Remove any margins
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().grid(row=6, column=0, pady=0, padx=0, sticky="nsew")
        
        # Configure the grid to allow the canvas to fill all available space
        self.grid_rowconfigure(6, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.mainloop()

if __name__ == "__main__":
    CNNModelTester()