import os
import json
from typing import List, Tuple
import numpy as np
import tensorflow as tf
import cv2
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Input, Dropout, Lambda, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
from tensorflow.keras.regularizers import l2
from tensorflow.keras.layers.experimental.preprocessing import Rescaling, RandomFlip, RandomRotation, RandomZoom, RandomContrast

class BoundryBoxModel:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self.label_map = {"red_block": 0, "green_block": 1}
        self.label_counter = 0
    
    def load_data(self) -> Tuple[List[np.ndarray], List[List[float]], List[int]]:
        images = []
        bbox_labels = []
        class_labels = []
        
        for root, _, files in os.walk(self.data_dir):
            frame_files = [f for f in files if f.startswith('frame_') and f.endswith('.png')]
            for frame_file in frame_files:
                json_file = frame_file.replace('.png', '.json')
                json_path = os.path.join(root, json_file)
                png_path = os.path.join(root, frame_file)
                
                if os.path.exists(json_path) and os.path.exists(png_path):
                    with open(json_path, 'r') as f:
                        label_data = json.load(f)
                    
                    shapes = label_data.get('shapes', [])
                    if shapes:
                        rectangle_label_box = shapes[0].get('points', [])
                        class_label = shapes[0].get('label', 'unknown')
                        
                        if class_label not in self.label_map:
                            self.label_map[class_label] = self.label_counter
                            self.label_counter += 1
                        
                        class_label_int = self.label_map[class_label]
                        
                        point1 = rectangle_label_box[0]
                        point2 = rectangle_label_box[2]
                        x1, y1 = point1
                        x2, y2 = point2
                    
                    image = cv2.imread(png_path)
                    image_array = np.array(image)
                    
                    images.append(image_array)
                    bbox_labels.append([x1, y1, x2, y2])
                    class_labels.append(class_label_int)
        
        return images, bbox_labels, class_labels
    
    def preprocess_data(self, images: List[np.ndarray], bbox_labels: List[List[float]], class_labels: List[int]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        images = np.array(images)
        bbox_labels = np.array(bbox_labels)
        class_labels = np.array(class_labels)
        
        images = images / 255.0
        
        return images, bbox_labels, class_labels
    
    def build_model(self, input_shape: Tuple[int, int, int], num_classes: int) -> tf.keras.Model:
        inputs = Input(shape=input_shape)
        
        x = Conv2D(32, (3, 3), activation='relu', kernel_regularizer=l2(0.001))(inputs)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2))(x)
        
        x = Conv2D(64, (3, 3), activation='relu', kernel_regularizer=l2(0.001))(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2))(x)
        
        x = Conv2D(128, (3, 3), activation='relu', kernel_regularizer=l2(0.001))(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2))(x)
        
        x = Flatten()(x)
        x = Dense(64, activation='relu', kernel_regularizer=l2(0.01))(x)
        x = Dropout(0.5)(x)
        
        bbox_output = Dense(4, name='bbox_output')(x)
        class_output = Dense(num_classes, activation='softmax', name='class_output')(x)
        
        model = Model(inputs=inputs, outputs=[bbox_output, class_output])
        
        model.compile(optimizer=Adam(learning_rate=0.0001),
                      loss={'bbox_output': 'mean_squared_error', 'class_output': 'sparse_categorical_crossentropy'}, 
                      metrics={'bbox_output': 'mean_squared_error', 'class_output': 'accuracy'})
        
        return model
    
    def train_model(self) -> None:
        images, bbox_labels, class_labels = self.load_data()
        images, bbox_labels, class_labels = self.preprocess_data(images, bbox_labels, class_labels)
        
        input_shape = images.shape[1:]
        num_classes = len(self.label_map)
        print(f"Input shape: {input_shape}, Number of classes: {num_classes}")
        
        model = self.build_model(input_shape, num_classes)
        
        checkpoint = ModelCheckpoint('best_cnn_model.h5', monitor='val_class_output_accuracy', save_best_only=True, mode='max')
        early_stopping = EarlyStopping(monitor='val_class_output_accuracy', patience=100)
        
        model.fit(images, {'bbox_output': bbox_labels, 'class_output': class_labels}, 
                  epochs=120, batch_size=32, validation_split=0.2, callbacks=[checkpoint, early_stopping])

if __name__ == "__main__":
    data_dir = r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\CNN_block_detection\11.11._hopefully_first_good_dataset"
    model = BoundryBoxModel(data_dir)
    model.train_model()