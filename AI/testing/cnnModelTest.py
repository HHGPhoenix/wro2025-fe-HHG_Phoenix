import tensorflow as tf
from tensorflow.keras import backend as K
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
        self.dir_base_name = None
        self.config_file = os.path.join(".config", "cnnModelTest.json")
        self.label_map = {0: "background", 1: "red_block", 2: "green_block"}
        self.image_files = []
        self.current_image_index = 0
        self.model_input_shape = (224, 224, 3)  # Add this line
        self.load_config()
        self.setup_gui()

    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.model_path = config.get('model_path', None)
                self.directory = config.get('directory', '')
                self.dir_base_name = os.path.basename(self.directory)
            if self.model_path and os.path.exists(self.model_path):
                try:
                    if self.model_path.endswith('.h5'):
                        self.model = tf.keras.models.load_model(self.model_path, custom_objects={'iou_loss': self.iou_loss})
                    elif self.model_path.endswith('.tflite'):
                        self.load_tflite_model(self.model_path)
                    if self.model and self.image_files:
                        self.display_image(self.image_files[0])
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
        self.dir_base_name = os.path.basename(self.directory)
        
        self.dir_label.configure(text=f"Selected Directory: {self.dir_base_name}")
        self.save_config()
        self.load_image_files()
        
        if self.model and self.image_files:
            self.display_image(self.image_files[0])
    
    def iou_loss(y_true, y_pred):
        # Compute Intersection over Union
        x1 = K.maximum(y_true[..., 0], y_pred[..., 0])
        y1 = K.maximum(y_true[..., 1], y_pred[..., 1])
        x2 = K.minimum(y_true[..., 2], y_pred[..., 2])
        y2 = K.minimum(y_true[..., 3], y_pred[..., 3])
    
        intersection = K.maximum(0.0, x2 - x1) * K.maximum(0.0, y2 - y1)
        union = (
            (y_true[..., 2] - y_true[..., 0]) *
            (y_true[..., 3] - y_true[..., 1]) +
            (y_pred[..., 2] - y_pred[..., 0]) *
            (y_pred[..., 3] - y_pred[..., 1]) -
            intersection
        )
        iou = intersection / (union + K.epsilon())
        return 1 - iou + K.mean(K.abs(y_true - y_pred), axis=-1)  # Combine with MAE
    
    def select_model(self):
        self.model_path = filedialog.askopenfilename(filetypes=[("Model Files", "*.h5 *.tflite"), ("All Files", "*.*")])
        if self.model_path:
            self.model_label.configure(text=f"Selected Model: {self.model_path}")
            try:
                if self.model_path.endswith('.h5'):
                    self.model = tf.keras.models.load_model(self.model_path, custom_objects={'iou_loss': self.iou_loss})
                    self.tflite_model = None
                elif self.model_path.endswith('.tflite'):
                    self.load_tflite_model(self.model_path)
                    self.model = None
                self.save_config()
                
                if self.image_files:
                    self.display_image(self.image_files[0])
            except Exception as e:
                print(f"Error loading model: {e}")
                self.model = None
                self.tflite_model = None

    def load_tflite_model(self, model_path):
        self.tflite_model = tf.lite.Interpreter(model_path=model_path)
        self.tflite_model.allocate_tensors()
        self.input_details = self.tflite_model.get_input_details()
        self.output_details = self.tflite_model.get_output_details()

    def load_image_files(self):
        self.image_files = []
        for root, dirs, files in os.walk(self.directory):
            for f in files:
                if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                    self.image_files.append(os.path.join(root, f))
        self.current_image_index = 0
        if self.image_files:
            self.display_image(self.image_files[self.current_image_index])

    def display_image(self, image_path):
        input_image = cv2.imread(image_path)
        if input_image is None:
            print(f"Failed to load image {image_path}")
            return

        # Resize to match model's expected input dimensions
        input_image_resized = cv2.resize(input_image, (224, 224))
        input_image_rgb = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
        input_image_rgb_resized = cv2.cvtColor(input_image_resized, cv2.COLOR_BGR2RGB)

        if self.model or self.tflite_model:
            # Use resized image for prediction
            input_image_norm = np.expand_dims(input_image_resized, axis=0) / 255.0

            if self.model:
                predictions = self.model.predict(input_image_norm)
            elif self.tflite_model:
                self.tflite_model.set_tensor(self.input_details[0]['index'], input_image_norm.astype(np.float32))
                self.tflite_model.invoke()
                predictions = [self.tflite_model.get_tensor(output['index']) for output in self.output_details]

            if len(predictions) == 2:
                if self.model:
                    bounding_boxes = predictions[0][0]
                    class_probs = predictions[1][0]
                elif self.tflite_model:
                    bounding_boxes = predictions[1][0]
                    class_probs = predictions[0][0]

                class_label = np.argmax(class_probs)
                class_name = self.label_map[class_label]

                # Scale bounding box to the original image dimensions
                x1, y1, x2, y2 = bounding_boxes
                x1, y1, x2, y2 = int(x1 * input_image.shape[1]), int(y1 * input_image.shape[0]), int(x2 * input_image.shape[1]), int(y2 * input_image.shape[0])

                if class_name == 'red_block':
                    color = (255, 0, 0)  # RGB
                elif class_name == 'green_block':
                    color = (0, 255, 0)  # RGB
                else:
                    color = (0, 0, 255)  # RGB

                cv2.rectangle(input_image_rgb, (x1, y1), (x2, y2), color, 2)

        self.ax.clear()
        self.ax.imshow(input_image_rgb)
        self.canvas.draw()

    def next_image(self):
        if self.image_files:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_files)
            self.display_image(self.image_files[self.current_image_index])

    def previous_image(self):
        if self.image_files:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_files)
            self.display_image(self.image_files[self.current_image_index])

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
        self.load_image_files()
        index = 0
        print(f"Processing {len(self.image_files)} images")
        while self.processing and index < len(self.image_files):
            print(f"Processing image {index + 1}/{len(self.image_files)}")
            image_path = self.image_files[index]
            input_image = cv2.imread(image_path)
            if input_image is None:
                print(f"Failed to load image {image_path}")
                index += 1
                continue

            # Resize to match model's expected input dimensions
            input_image_resized = cv2.resize(input_image, (224, 224))
            input_image_norm = np.expand_dims(input_image_resized, axis=0) / 255.0

            if self.model:
                predictions = self.model.predict(input_image_norm)
            elif self.tflite_model:
                self.tflite_model.set_tensor(self.input_details[0]['index'], input_image_norm.astype(np.float32))
                start_time = time.time()    
                self.tflite_model.invoke()
                stop_time = time.time()
                print(f"Inference time: {stop_time - start_time}")
                predictions = [self.tflite_model.get_tensor(output['index']) for output in self.output_details]

            print(f"Predictions: {predictions}")

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
            x1, y1, x2, y2 = int(x1 * input_image.shape[1]), int(y1 * input_image.shape[0]), int(x2 * input_image.shape[1]), int(y2 * input_image.shape[0])
    
            if class_name == 'red_block':
                color = (0, 0, 255)
            elif class_name == 'green_block':
                color = (0, 255, 0)
            else:
                color = (255, 0, 0)
    
            cv2.rectangle(input_image, (x1, y1), (x2, y2), color, 2)
    
            upscale_factor = 2
            input_image = cv2.resize(input_image, (0, 0), fx=upscale_factor, fy=upscale_factor, interpolation=cv2.INTER_LINEAR)
    
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
    
            margin = 10
            line_height = int(cv2.getTextSize('Text', font, font_scale, thickness)[0][1] + 5)
            org_red = (margin, margin + line_height)
            org_green = (margin, margin + 2 * line_height)
    
            cv2.putText(input_image, f'Red Block Confidence: {red_confidence:.2f}', org_red, font, font_scale, (0, 0, 255), thickness, cv2.LINE_AA)
            cv2.putText(input_image, f'Green Block Confidence: {green_confidence:.2f}', org_green, font, font_scale, (0, 255, 0), thickness, cv2.LINE_AA)
    
            input_image_rgb = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
    
            self.ax.clear()
            self.ax.imshow(input_image_rgb)
            self.canvas.draw()
    
            time.sleep(0.08)
            index += 1

    def setup_gui(self):
        self.title("Image Processing")
        self.geometry("700x900")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1)

        self.dir_button = ctk.CTkButton(self, text="Select Directory", command=self.select_directory)
        self.dir_button.grid(row=0, column=0, pady=10, padx=10, sticky="ew")

        self.dir_label = ctk.CTkLabel(
            self,
            text=f"Selected Directory: {self.dir_base_name if self.dir_base_name else 'No directory selected'}"
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

        self.next_button = ctk.CTkButton(self, text="Next", command=self.next_image)
        self.next_button.grid(row=6, column=0, pady=10, padx=10, sticky="ew")

        self.previous_button = ctk.CTkButton(self, text="Previous", command=self.previous_image)
        self.previous_button.grid(row=7, column=0, pady=10, padx=10, sticky="ew")

        self.figure = Figure(figsize=(5, 5), dpi=100)
        self.figure.patch.set_facecolor('black')
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('black')
        self.ax.axis('off')
        
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().grid(row=8, column=0, pady=0, padx=0, sticky="nsew")
        
        self.grid_rowconfigure(8, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.mainloop()

if __name__ == "__main__":
    CNNModelTester()