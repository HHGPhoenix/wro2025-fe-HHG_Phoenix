import os
import json
from typing import List, Tuple
import numpy as np
import tensorflow as tf
import cv2
import matplotlib.pyplot as plt
from tensorflow.keras.applications import MobileNetV2 # type: ignore
from tensorflow.keras.models import Model, Sequential # type: ignore
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Input, Dropout, Lambda, BatchNormalization, Activation # type: ignore
from tensorflow.keras.optimizers import Adam # type: ignore
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping # type: ignore
from tensorflow.keras.regularizers import l2 # type: ignore
from tensorflow.keras.layers.experimental.preprocessing import Rescaling, RandomFlip, RandomRotation, RandomZoom, RandomContrast # type: ignore
from sklearn.model_selection import train_test_split # type: ignore

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

class BoundryBoxModel:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
                # Update the label_map to include 'background' class
        self.label_map = {"background": 0, "red_block": 1, "green_block": 2}
        self.label_counter = 3  # Start counting from 3 if new classes are added later
        
    def display_random_data_point(self, images: np.ndarray, bbox_labels: np.ndarray, class_labels: np.ndarray) -> None:
        # Invert label_map to get class labels from integers
        inv_label_map = {v: k for k, v in self.label_map.items()}
        
        while True:
            idx = np.random.randint(0, len(images))
            image = images[idx]
            bbox = bbox_labels[idx]
            class_label_int = class_labels[idx]
            class_label = inv_label_map[class_label_int]
            
            # Multiply by 255 to restore original pixel values
            image = (image * 255).astype(np.uint8)
            
            self.display_image(image, bbox, class_label)
            
            cont = input("Display another image? (y/n): ")
            if cont.lower() != 'y':
                break
            
    def display_image(self, image_array: np.ndarray, bbox_norm: List[float], class_label: str):
        height, width, _ = image_array.shape
        x1_norm, y1_norm, x2_norm, y2_norm = bbox_norm
        x1, y1 = int(x1_norm * width), int(y1_norm * height)
        x2, y2 = int(x2_norm * width), int(y2_norm * height)
    
        image_copy = image_array.copy()
        cv2.rectangle(image_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(image_copy, class_label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    
        plt.imshow(cv2.cvtColor(image_copy, cv2.COLOR_BGR2RGB))
        plt.title('Sample Image')
        plt.axis('off')
        plt.show()
    
    def adjust_brightness_saturation(self, image: np.ndarray, brightness: float, saturation: float) -> np.ndarray:
        hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv_image = np.array(hsv_image, dtype=np.float64)
        hsv_image[:, :, 1] = hsv_image[:, :, 1] * saturation
        hsv_image[:, :, 1][hsv_image[:, :, 1] > 255] = 255
        hsv_image[:, :, 2] = hsv_image[:, :, 2] * brightness
        hsv_image[:, :, 2][hsv_image[:, :, 2] > 255] = 255
        hsv_image = np.array(hsv_image, dtype=np.uint8)
        return cv2.cvtColor(hsv_image, cv2.COLOR_HSV2BGR)

    def load_data(self) -> Tuple[List[np.ndarray], List[List[float]], List[int]]:
        images = []
        bbox_labels = []
        class_labels = []
        image_counter = 0
    
        for root, _, files in os.walk(self.data_dir):
            frame_files = [f for f in files if f.endswith('.png')]
            for frame_file in frame_files:
                json_file = frame_file.replace('.png', '.json')
                json_path = os.path.join(root, json_file)
                png_path = os.path.join(root, frame_file)
    
                image = cv2.imread(png_path)
                image_array = np.array(image)
    
                if os.path.exists(json_path):
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
    
                        height, width, _ = image_array.shape
    
                        # Normalize bounding box coordinates
                        x1_norm, y1_norm = x1 / width, y1 / height
                        x2_norm, y2_norm = x2 / width, y2 / height
    
                        # Original image
                        images.append(image_array)
                        bbox_labels.append([x1_norm, y1_norm, x2_norm, y2_norm])
                        class_labels.append(class_label_int)
                        image_counter += 1
    
                        # Original image
                        images.append(image_array)
                        bbox_labels.append([x1_norm, y1_norm, x2_norm, y2_norm])
                        class_labels.append(class_label_int)
                        image_counter += 1
        
                        # Horizontal flip
                        h_flip_image = cv2.flip(image_array, 1)
                        h_flip_bbox = [1 - x2_norm, y1_norm, 1 - x1_norm, y2_norm]
                        images.append(h_flip_image)
                        bbox_labels.append(h_flip_bbox)
                        class_labels.append(class_label_int)
                        image_counter += 1
        
                        # Adjust brightness and saturation for horizontal flip
                        for brightness in [0.8, 1.2]:
                            for saturation in [0.8, 1.2]:
                                adjusted_h_flip_image = self.adjust_brightness_saturation(h_flip_image, brightness, saturation)
                                images.append(adjusted_h_flip_image)
                                bbox_labels.append(h_flip_bbox)
                                class_labels.append(class_label_int)
                                image_counter += 1
        
                        # Vertical flip
                        v_flip_image = cv2.flip(image_array, 0)
                        v_flip_bbox = [x1_norm, 1 - y2_norm, x2_norm, 1 - y1_norm]
                        images.append(v_flip_image)
                        bbox_labels.append(v_flip_bbox)
                        class_labels.append(class_label_int)
                        image_counter += 1
        
                        # Adjust brightness and saturation for vertical flip
                        for brightness in [0.8, 1.2]:
                            for saturation in [0.8, 1.2]:
                                adjusted_v_flip_image = self.adjust_brightness_saturation(v_flip_image, brightness, saturation)
                                images.append(adjusted_v_flip_image)
                                bbox_labels.append(v_flip_bbox)
                                class_labels.append(class_label_int)
                                image_counter += 1
        
                        # Adjust brightness and saturation for original image
                        for brightness in [0.8, 1.2]:
                            for saturation in [0.8, 1.2]:
                                adjusted_image = self.adjust_brightness_saturation(image_array, brightness, saturation)
                                images.append(adjusted_image)
                                bbox_labels.append([x1_norm, y1_norm, x2_norm, y2_norm])
                                class_labels.append(class_label_int)
                                image_counter += 1
    
                    else:
                        # If no shapes, treat as background
                        class_label_int = self.label_map['background']
                        images.append(image_array)
                        bbox_labels.append([0, 0, 0, 0])  # No bounding box
                        class_labels.append(class_label_int)
                        image_counter += 1
                else:
                    # No label file, treat as background
                    class_label_int = self.label_map['background']
                    images.append(image_array)
                    bbox_labels.append([0, 0, 0, 0])  # No bounding box
                    class_labels.append(class_label_int)
                    image_counter += 1

        # print(f"Total images processed: {image_counter}; images shape: {images[0].shape}; bbox_labels shape: {bbox_labels[0].shape}; class_labels shape: {class_labels[0].shape}")
        return images, bbox_labels, class_labels
        
    def preprocess_data(self, images: List[np.ndarray], bbox_labels: List[List[float]], class_labels: List[int]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        images = np.array(images)
        bbox_labels = np.array(bbox_labels)
        class_labels = np.array(class_labels)
        
        # print length of images, bbox_labels, class_labels
        print(f"Images: {images.shape}, Bbox labels: {bbox_labels.shape}, Class labels: {class_labels.shape}")
        
        images = images / 255.0
        
        return images, bbox_labels, class_labels
    
    def build_model(self, input_shape: Tuple[int, int, int], num_classes: int):
        inputs = Input(shape=input_shape)
    
        # Build a custom CNN
        x = Conv2D(32, (3, 3), activation='relu', padding='same')(inputs)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Conv2D(64, (3, 3), activation='relu', padding='same')(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Conv2D(128, (3, 3), activation='relu', padding='same')(x)
        x = MaxPooling2D(pool_size=(2, 2))(x)
        x = Flatten()(x)
        x = Dense(128, activation='relu')(x)
    
        # Output layers
        bbox_output = Dense(4, name='bbox_output')(x)
        class_output = Dense(num_classes, activation='softmax', name='class_output')(x)
    
        model = Model(inputs=inputs, outputs=[bbox_output, class_output])
    
        model.compile(
            optimizer=Adam(),
            loss={
                'bbox_output': 'mean_squared_error',
                'class_output': 'sparse_categorical_crossentropy'
            },
            metrics={
                'bbox_output': 'mean_absolute_error',
                'class_output': 'accuracy'
            }
        )
    
        return model
    
    def train_model(self) -> None:
        images, bbox_labels, class_labels = self.load_data()
        images, bbox_labels, class_labels = self.preprocess_data(images, bbox_labels, class_labels)
    
        input_shape = images.shape[1:]
        num_classes = len(self.label_map)
        print(f"Input shape: {input_shape}, Number of classes: {num_classes}")
    
        # Split the data
        train_images, val_images, train_bbox_labels, val_bbox_labels, train_class_labels, val_class_labels = train_test_split(
            images, bbox_labels, class_labels, test_size=0.2, random_state=42)
        
        print(f"Train images: {train_images.shape}, Val images: {val_images.shape}")
    
        model = self.build_model(input_shape, num_classes)
        
        print("Model builded")
    
        checkpoint = ModelCheckpoint('best_cnn_model.h5', monitor='val_bbox_output_mean_absolute_error', save_best_only=True, mode='max')
        early_stopping = EarlyStopping(monitor='val_class_output_loss', patience=5)
    
        model.fit(train_images, {'bbox_output': train_bbox_labels, 'class_output': train_class_labels},
                  epochs=100, batch_size=32,
                  validation_data=(val_images, {'bbox_output': val_bbox_labels, 'class_output': val_class_labels}),
                  callbacks=[checkpoint, early_stopping])
        
        
if __name__ == "__main__":
    data_dir = r"D:\Onedrive HHG\OneDrive - Helmholtz-Gymnasium\Dokumente\.Libery\Code\Flix,Emul Ordner\WRO2025\PrototypeV2\CNN_block_detection\16.11._more_data - unfinished"
    model = BoundryBoxModel(data_dir)
    model.train_model()