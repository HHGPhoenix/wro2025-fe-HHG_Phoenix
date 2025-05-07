import os
import json
from typing import List
import numpy as np
import cv2
import csv
from mediapipe_model_maker import object_detector
from mediapipe_model_maker.config import ExportFormat
from mediapipe_model_maker.object_detector import DataLoader

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class BoundryBoxModel:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self.label_map = {}
        self.label_counter = 1  # Label IDs start from 1

    def load_data(self) -> DataLoader:
        annotations = []
        for root, _, files in os.walk(self.data_dir):
            frame_files = [f for f in files if f.endswith('.png')]
            for frame_file in frame_files:
                json_file = frame_file.replace('.png', '.json')
                json_path = os.path.join(root, json_file)
                png_path = os.path.join(root, frame_file)

                if os.path.exists(json_path) and os.path.exists(png_path):
                    with open(json_path, 'r') as f:
                        label_data = json.load(f)

                    shapes = label_data.get('shapes', [])
                    if shapes:
                        shape = shapes[0]
                        points = shape.get('points', [])
                        class_label = shape.get('label', 'unknown')

                        if class_label not in self.label_map:
                            self.label_map[class_label] = self.label_counter
                            self.label_counter += 1

                        x_coords = [p[0] for p in points]
                        y_coords = [p[1] for p in points]
                        xmin, xmax = min(x_coords), max(x_coords)
                        ymin, ymax = min(y_coords), max(y_coords)

                        annotations.append([
                            png_path,
                            xmin, ymin, xmax, ymax,
                            class_label
                        ])

        # Write annotations to CSV file
        csv_file = 'annotations.csv'
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filepath', 'xmin', 'ymin', 'xmax', 'ymax', 'label'])
            writer.writerows(annotations)

        # Create DataLoader
        data = DataLoader.from_csv(
            csv_file,
            images_dir=None,
            label_map=self.label_map
        )
        return data

    def train_model(self) -> None:
        data = self.load_data()

        # Split data into training and validation
        train_data, val_data = data.split(0.8)

        # Define the model specification
        spec = object_detector.EfficientDetLite0Spec()

        # Train the model
        model = object_detector.create(
            train_data=train_data,
            model_spec=spec,
            batch_size=8,
            epochs=20,
            validation_data=val_data
        )

        # Evaluate the model
        model.evaluate(val_data)

        # Export the model
        model.export(
            export_dir='.',
            tflite_filename='model.tflite',
            label_filename='labels.txt',
            export_format=[ExportFormat.TFLITE, ExportFormat.LABEL]
        )
        
if __name__ == '__main__':
    model = BoundryBoxModel('data')
    model.train_model()