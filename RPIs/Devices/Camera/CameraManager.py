import cv2
import numpy as np
import threading
import time
import uuid
from picamera2 import Picamera2
from picamera2 import controls

#A class for detecting red and green blocks in the camera stream           
class Camera():
    def __init__(self, enable_video_stream=False, enable_video_writer=False):
        # Variable initialization
        self.freeze = False
        self.frame = None
        self.frame_lock_1 = threading.Lock()
        self.frame_lock_2 = threading.Lock()
        self.enable_video_stream = enable_video_stream
        self.enable_video_writer = enable_video_writer
        
        self.picam = Picamera2()
        # Configure and start the camera
        config = self.picam.create_still_configuration(main={"size": (1280, 720)}, raw={"size": (1280, 720)}, controls={"FrameRate": 34})
        self.picam.configure(config)
        self.picam.start()
        self.picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        
        # Define the color ranges for green and red in HSV color space
        self.lower_green = np.array([53, 100, 40])
        self.upper_green = np.array([93, 220, 150])

        self.lower_red1 = np.array([0, 160, 120])
        self.upper_red1 = np.array([5, 220, 200])

        self.lower_red2 = np.array([173, 160, 100])
        self.upper_red2 = np.array([180, 220, 200])

        # Define the kernel for morphological operations
        self.kernel = np.ones((7, 7), np.uint8)
        
    def capture_array(self):
        frame = self.picam.capture_array()
        frameraw = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        framehsv = cv2.cvtColor(frameraw, cv2.COLOR_BGR2HSV)
        
        return frameraw, framehsv
    
    def simplify_image(self, framehsv, shade_of_red, shade_of_green):
        # Masks for green and red pixels
        mask_green = cv2.inRange(framehsv, self.lower_green, self.upper_green)
        mask_red1 = cv2.inRange(framehsv, self.lower_red1, self.upper_red1)
        mask_red2 = cv2.inRange(framehsv, self.lower_red2, self.upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        # Combine red and green masks and then find the inverse to get non-red and non-green areas
        mask_combined = cv2.bitwise_or(mask_red, mask_green)
        mask_black = cv2.bitwise_not(mask_combined)

        # Initialize a blank white image
        height, width = framehsv.shape[:2]
        simplified_image = np.ones((height, width, 3), np.uint8) * 255  # White background

        # Apply specified shades to red and green areas
        simplified_image[mask_green == 255] = shade_of_green
        simplified_image[mask_red == 255] = shade_of_red

        # Apply black color to non-red and non-green areas
        simplified_image[mask_black == 255] = [0, 0, 0]  # Black

        return simplified_image
         
    # Function running in a new thread that constantly updates the coordinates of the blocks in the camera stream
    def process_blocks(self):
        self.video_writer = None
        self.frames = [None] * 3

        while True:
            self.block_array, framenormal, frameraw = self.get_coordinates()
            framebinary = self.get_edges(frameraw)

            self.frames[0] = framenormal
            self.frames[1] = framebinary
            self.frames[2] = frameraw

            if self.video_writer is None and self.enable_video_writer:
                # Create a VideoWriter object to save the frames as an mp4 file
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(f'./videos/output_{str(uuid.uuid4())}.mp4', fourcc, 20, (frameraw.shape[1], frameraw.shape[0]), True)

            # Write the frame to the video file
            if self.enable_video_writer:
                self.video_writer.write(frameraw)    
    
    # Compress the video frames for the webstream    
    def compress_frame(self, frame):
        dimensions = len(frame.shape)
        if dimensions == 3:
            height, width, _ = frame.shape
        elif dimensions == 2:
            height, width = frame.shape
        else:
            raise ValueError(f"Unexpected number of dimensions in frame: {dimensions}")
        new_height = 180
        new_width = int(new_height * width / height)
        frame = cv2.resize(frame, (new_width, new_height))
        return frame