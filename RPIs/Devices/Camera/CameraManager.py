import cv2
import numpy as np
import threading
import time
import uuid
import tensorflow as tf
from picamera2 import Picamera2 # type: ignore
from libcamera import controls # type: ignore

#A class for detecting red and green blocks in the camera stream           
class Camera():
    def __init__(self):
        """
        Initialize the camera and set up the color ranges for red and green blocks.
        """
        self.interpreter = tf.lite.Interpreter(model_path='RPIs/DataManager/cnn_model.tflite')
        self.interpreter.allocate_tensors()
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        # Variable initialization
        self.frame = None
        
        self.red_counter = []
        self.green_counter = []
        
        self.picam = Picamera2()
        # Configure and start the camera
        config = self.picam.create_still_configuration(main={"size": (1280, 720)}, raw={"size": (1280, 720)}, controls={"FrameRate": 34})
        self.picam.configure(config)
        self.picam.start()
        self.picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        self.picam.set_logging(Picamera2.ERROR)
        
        # Define the color ranges for green and red in HSV color space
        self.lower_green = np.array([57, 30, 40])
        self.upper_green = np.array([73, 120, 105])

        # self.lower_red1 = np.array([0, 105, 80])
        # self.upper_red1 = np.array([1, 200, 180])
        
        self.lower_red1 = np.array([175, 105, 80])
        self.upper_red1 = np.array([180, 200, 180])

        self.lower_red2 = np.array([175, 105, 80])
        self.upper_red2 = np.array([180, 200, 180])
        
        self.lower_black = np.array([15, 0, 0])
        self.upper_black = np.array([170, 55, 70])

        # Define the kernel for morphological operations
        self.kernel = np.ones((5, 5), np.uint8)
        
    def capture_array(self):
        """
        Capture an image from the camera and convert it to RGB and HSV color spaces.

        Returns:
            np.ndarray: The captured image in RGB color space.
            np.ndarray: The captured image in HSV color space.
        """
        frame = self.picam.capture_array()
        frameraw = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        framehsv = cv2.cvtColor(frameraw, cv2.COLOR_BGR2HSV)        
        return frameraw, framehsv
    
    def simplify_image(self, framehsv, black_color=[255, 255, 255], shade_of_red=[0, 0, 255], shade_of_green=[0, 255, 0]):
        """
        Simplify the image by coloring red and green areas with specified shades.

        Args:
            framehsv (np.ndarray): The image in HSV color space.
            shade_of_red (list): The RGB values of the shade of red to color the red areas.
            shade_of_green (list): The RGB values of the shade of green to color the green areas.

        Returns:
            np.ndarray: The simplified image with red and green areas colored with the specified shades.
        """
        
        # Masks for green and red pixels
        mask_green = cv2.inRange(framehsv, self.lower_green, self.upper_green)
        mask_red1 = cv2.inRange(framehsv, self.lower_red1, self.upper_red1)
        mask_red2 = cv2.inRange(framehsv, self.lower_red2, self.upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        mask_black = cv2.inRange(framehsv, self.lower_black, self.upper_black)

        # Initialize a blank white image
        height, width = framehsv.shape[:2]
        simplified_image = np.ones((height, width, 3), np.uint8) * 0  # White background

        # Apply specified shades to red and green areas
        simplified_image[mask_green > 0] = shade_of_green
        simplified_image[mask_red > 0] = shade_of_red

        # Apply black color to non-red and non-green areas
        simplified_image[mask_black > 0] = black_color  # Black color for non-red and non-green areas

        return simplified_image

    def draw_blocks(self, frameraw):
        """
        Draw rectangles around green and red blocks in the camera stream.

        Args:
            frameraw (np.ndarray): The image in RGB color space.

        Returns:
            np.ndarray: The image with rectangles drawn around green and red blocks.
        """
        # run the ai model
        framergb = cv2.cvtColor(frameraw, cv2.COLOR_BGR2RGB)
        self.interpreter.set_tensor(self.input_details[0]['index'], np.expand_dims(framergb, axis=0))
        
        start_time = time.time()
        self.interpreter.invoke()
        end_time = time.time()
        print(f"Time taken to run the model: {end_time - start_time} seconds")
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        print(f"Result: {output_data}")
        
        # x, y, w, h = output_data[0]
        # class_id = output_data[1]
        
            
        return frameraw
    
    # Compress the video frames for the webstream    
    def compress_frame(self, frame, new_height=120):
        """
        Compress the frame to a specified height while maintaining the aspect ratio.

        Args:
            frame (np.ndarray): The frame to compress.
            new_height (int, optional): The height to compress the frame to. Defaults to 480.

        Raises:
            ValueError: If the number of dimensions in the frame is not 2 or 3.

        Returns:
            np.ndarray: The compressed frame.
        """
        dimensions = len(frame.shape)
        if dimensions == 3:
            height, width, _ = frame.shape
        elif dimensions == 2:
            height, width = frame.shape
        else:
            raise ValueError(f"Unexpected number of dimensions in frame: {dimensions}")
        new_width = int(new_height * width / height)
        frame = cv2.resize(frame, (new_width, new_height))
        frame = frame[20:, :]
        
        return frame