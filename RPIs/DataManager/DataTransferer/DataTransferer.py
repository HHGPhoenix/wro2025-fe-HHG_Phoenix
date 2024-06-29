import cv2
import numpy as np
from multiprocessing import Manager

class DataTransferer:
    def __init__(self, camera, lidar, shared_list):
        self.camera = camera
        self.lidar = lidar
        self.shared_list = shared_list
    
    def process_cam_frames(self):
        while True:
            frameraw, framehsv = self.camera.capture_array()
            simplified_image = self.camera.simplify_image(framehsv, [0, 255, 0], [255, 0, 0])
            
            # Update shared list with the new frames
            self.shared_list[0] = frameraw.tobytes()
            self.shared_list[1] = simplified_image.tobytes()
