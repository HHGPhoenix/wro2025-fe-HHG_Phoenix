import cv2
import numpy as np
from multiprocessing import Manager
import time

class DataTransferer:
    def __init__(self, shared_list):
        self.shared_list = shared_list
    
    def process_cam_frames(self):
        while True:
            # Generate random frames (640x480 RGB)
            frameraw = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
            simplified_image = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
            
            # Update shared list with the new frames
            self.shared_list[0] = frameraw.tobytes()
            self.shared_list[1] = simplified_image.tobytes()
            
            # Simulate frame rate
            time.sleep(1 / 30)  # 30 frames per second
