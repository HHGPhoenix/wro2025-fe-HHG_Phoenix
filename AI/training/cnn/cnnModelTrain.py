import os
import json
from typing import List, Tuple, Dict, Iterator
import numpy as np
import tensorflow as tf
import cv2
import matplotlib.pyplot as plt
from tensorflow.keras.applications import MobileNetV2 # type: ignore
from tensorflow.keras.models import Model, Sequential # type: ignore
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Input, Dropout, Lambda, BatchNormalization, Activation, Reshape, GlobalAveragePooling2D # type: ignore
from tensorflow.keras.optimizers import Adam # type: ignore
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping # type: ignore
from tensorflow.keras.regularizers import l2 # type: ignore
from tensorflow.keras.layers import Rescaling, RandomFlip, RandomRotation, RandomZoom, RandomContrast # type: ignore
from tensorflow.keras.utils import Sequence # type: ignore
from sklearn.model_selection import train_test_split # type: ignore
from tensorflow.keras import backend as K # type: ignore

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class DataGenerator(Sequence):
    """Generate data for Keras"""
    def __init__(self, image_paths, bbox_labels, class_labels, batch_size=32, 
                 input_shape=(224, 224, 3), shuffle=True, augment=False):
        self.image_paths = image_paths
        self.bbox_labels = bbox_labels
        self.class_labels = class_labels
        self.batch_size = batch_size
        self.input_shape = input_shape
        self.shuffle = shuffle
        self.augment = augment
        self.indexes = np.arange(len(self.image_paths))
        if self.shuffle:
            np.random.shuffle(self.indexes)
            
    def __len__(self):
        """Return the number of batches per epoch"""
        return int(np.ceil(len(self.image_paths) / self.batch_size))
    
    def __getitem__(self, index):
        """Generate one batch of data"""
        # Generate indexes of the batch
        indexes = self.indexes[index * self.batch_size:(index + 1) * self.batch_size]
        
        # Find list of paths
        image_paths_temp = [self.image_paths[k] for k in indexes]
        bbox_labels_temp = [self.bbox_labels[k] for k in indexes]
        class_labels_temp = [self.class_labels[k] for k in indexes]
        
        # Generate data
        X, y_bbox, y_class = self.__data_generation(image_paths_temp, bbox_labels_temp, class_labels_temp)
        
        return X, {'bbox_output': y_bbox, 'class_output': y_class}
    
    def on_epoch_end(self):
        """Updates indexes after each epoch"""
        self.indexes = np.arange(len(self.image_paths))
        if self.shuffle:
            np.random.shuffle(self.indexes)
    
    def __data_generation(self, image_paths, bbox_labels, class_labels):
        """Generates data containing batch_size samples"""
        # Initialization
        X = np.empty((len(image_paths), *self.input_shape))
        y_bbox = np.empty((len(image_paths), 4))
        y_class = np.empty(len(image_paths), dtype=int)
        
        # Generate data
        for i, (img_path, bbox, cls) in enumerate(zip(image_paths, bbox_labels, class_labels)):
            # Read and preprocess image
            if isinstance(img_path, str):
                # It's a file path string
                img = cv2.imread(img_path)
            elif isinstance(img_path, dict):
                # It's a dictionary with transformation information
                original_path = img_path['original']
                img = cv2.imread(original_path)
                
                # Apply transformations based on dict contents
                if img is not None:
                    if img_path.get('transform') == 'h_flip':
                        img = cv2.flip(img, 1)  # Horizontal flip
                    elif img_path.get('transform') == 'v_flip':
                        img = cv2.flip(img, 0)  # Vertical flip
                    
                    # Apply brightness/saturation adjustments if specified
                    if 'brightness' in img_path:
                        img = cv2.convertScaleAbs(img, alpha=img_path['brightness'])
                    
                    if 'saturation' in img_path:
                        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype("float32")
                        (h, s, v) = cv2.split(img_hsv)
                        s = s * img_path['saturation']
                        s = np.clip(s, 0, 255)
                        img_hsv = cv2.merge([h, s, v])
                        img = cv2.cvtColor(img_hsv.astype("uint8"), cv2.COLOR_HSV2BGR)
            else:
                # It's already a numpy array
                img = img_path
                
            if img is not None:
                # Resize if needed
                if img.shape[:2] != self.input_shape[:2]:
                    img = cv2.resize(img, self.input_shape[:2])
                
                # Normalize pixel values
                X[i,] = img / 255.0
                
                # Store bounding box and class label
                y_bbox[i,] = bbox
                y_class[i,] = cls
        
        return X, y_bbox, y_class

class BoundaryBoxModel:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
        self.label_map = {"background": 0, "red_block": 1, "green_block": 2}
        self.label_counter = 3  # Start counting from 3 if new classes are added later
        self.input_shape = (224, 224, 3)  # Define standard input shape
        
    # Display methods remain unchanged...

    def find_all_images(self) -> List[Dict]:
        """Find all images and their metadata without loading them into memory"""
        image_data = []
        for root, _, files in os.walk(self.data_dir):
            frame_files = [f for f in files if f.endswith('.png')]
            for frame_file in frame_files:
                json_file = frame_file.replace('.png', '.json')
                json_path = os.path.join(root, json_file)
                png_path = os.path.join(root, frame_file)
                
                # Just store paths and metadata, don't load the images yet
                image_data.append({
                    'image_path': png_path,
                    'json_path': json_path if os.path.exists(json_path) else None
                })
        return image_data

    def process_image_metadata(self, image_data: List[Dict]) -> Tuple[List, List[List[float]], List[int]]:
        """Process image metadata and return paths/arrays with labels"""
        images = []  # Will store paths instead of actual images
        bbox_labels = []
        class_labels = []
        
        for item in image_data:
            png_path = item['image_path']
            json_path = item['json_path']
            
            # Get image dimensions for normalization
            img = cv2.imread(png_path)
            height, width, _ = img.shape
            
            if json_path:
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
                    
                    # Normalize bounding box coordinates
                    x1_norm, y1_norm = x1 / width, y1 / height
                    x2_norm, y2_norm = x2 / width, y2 / height
                    
                    # Store just the path and labels
                    images.append(png_path)
                    bbox_labels.append([x1_norm, y1_norm, x2_norm, y2_norm])
                    class_labels.append(class_label_int)
                    
                    # Horizontal flip metadata
                    h_flip_bbox = [1 - x2_norm, y1_norm, 1 - x1_norm, y2_norm]
                    images.append({'original': png_path, 'transform': 'h_flip'})
                    bbox_labels.append(h_flip_bbox)
                    class_labels.append(class_label_int)
                    
                    # Vertical flip metadata
                    v_flip_bbox = [x1_norm, 1 - y2_norm, x2_norm, 1 - y1_norm]
                    images.append({'original': png_path, 'transform': 'v_flip'})
                    bbox_labels.append(v_flip_bbox)
                    class_labels.append(class_label_int)
                    
                    # Store metadata for brightness/contrast adjustments
                    for transform in ['original', 'h_flip', 'v_flip']:
                        for brightness in [0.8, 1.2]:
                            for saturation in [0.8, 1.2]:
                                images.append({
                                    'original': png_path, 
                                    'transform': transform,
                                    'brightness': brightness,
                                    'saturation': saturation
                                })
                                
                                if transform == 'original':
                                    bbox_labels.append([x1_norm, y1_norm, x2_norm, y2_norm])
                                elif transform == 'h_flip':
                                    bbox_labels.append(h_flip_bbox)
                                else:  # v_flip
                                    bbox_labels.append(v_flip_bbox)
                                    
                                class_labels.append(class_label_int)
                else:
                    # Background class
                    class_label_int = self.label_map['background']
                    images.append(png_path)
                    bbox_labels.append([0, 0, 0, 0])  # No bounding box
                    class_labels.append(class_label_int)
            else:
                # No label file, treat as background
                class_label_int = self.label_map['background']
                images.append(png_path)
                bbox_labels.append([0, 0, 0, 0])  # No bounding box
                class_labels.append(class_label_int)
                
        print(f"Total images to process: {len(images)}")
        return images, bbox_labels, class_labels
    
    def build_model(self, input_shape: Tuple[int, int, int], num_classes: int):
        inputs = Input(shape=input_shape)

        # Convolutional base with Batch Normalization
        x = Conv2D(32, (3, 3), activation='relu', padding='same')(inputs)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2))(x)
        x = Conv2D(64, (3, 3), activation='relu', padding='same')(x)
        x = BatchNormalization()(x)
        x = MaxPooling2D((2, 2))(x)
        x = Conv2D(128, (3, 3), activation='relu', padding='same')(x)
        x = BatchNormalization()(x)
        x = Flatten()(x)
        x = Dense(256, activation='relu')(x)

        # Output layers
        bbox_output = Dense(4, activation='sigmoid', name='bbox_output')(x)  # Changed to sigmoid for normalized coordinates
        class_output = Dense(num_classes, activation='softmax', name='class_output')(x)

        model = Model(inputs=inputs, outputs=[bbox_output, class_output])

        return model

    def train_model(self) -> None:
        # Find all images but don't load them yet
        image_data = self.find_all_images()
        images, bbox_labels, class_labels = self.process_image_metadata(image_data)

        num_classes = len(self.label_map)
        print(f"Input shape: {self.input_shape}, Number of classes: {num_classes}")

        # Split the data (just the paths/metadata)
        train_indices, val_indices = train_test_split(
            range(len(images)), test_size=0.2, random_state=42)
            
        train_images = [images[i] for i in train_indices]
        train_bbox_labels = [bbox_labels[i] for i in train_indices]
        train_class_labels = [class_labels[i] for i in train_indices]
        
        val_images = [images[i] for i in val_indices]
        val_bbox_labels = [bbox_labels[i] for i in val_indices]
        val_class_labels = [class_labels[i] for i in val_indices]
        
        print(f"Train images: {len(train_images)}, Val images: {len(val_images)}")

        # Create data generators
        train_generator = DataGenerator(
            train_images, train_bbox_labels, train_class_labels, 
            batch_size=128, input_shape=self.input_shape, augment=True
        )
        
        val_generator = DataGenerator(
            val_images, val_bbox_labels, val_class_labels,
            batch_size=128, input_shape=self.input_shape, shuffle=True
        )
        
        model = self.build_model(self.input_shape, num_classes)
        
        model.compile(
            optimizer=Adam(learning_rate=1e-5),
            loss={
                'bbox_output': 'mean_squared_error',
                'class_output': 'sparse_categorical_crossentropy'
            },
            metrics={
                'bbox_output': 'mean_absolute_error',
                'class_output': 'accuracy'
            }
        )
        
        print("Model compiled successfully")
        
        checkpoint = ModelCheckpoint('best_cnn_model.h5', 
                                monitor='val_bbox_output_mean_absolute_error', 
                                save_best_only=True, 
                                mode='min')
        early_stopping = EarlyStopping(monitor='val_bbox_output_mean_absolute_error', patience=5)
        
        model.fit(
            train_generator, 
            epochs=100,
            validation_data=val_generator,
            callbacks=[checkpoint, early_stopping],
            workers=4,  # Use multiple workers for parallel data processing
            use_multiprocessing=False
        )
        
if __name__ == "__main__":
    data_dir = r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\CNN_block_detection\16.11._more_data - unfinished"
    model = BoundaryBoxModel(data_dir)
    model.train_model()