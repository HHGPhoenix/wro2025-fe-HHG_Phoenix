import cv2
import numpy as np
from multiprocessing import Manager
import time
import threading

class DataTransferer:
    def __init__(self, cam, lidar, frame_list=None, lidar_list=None):
        self.camera = cam
        self.lidar = lidar
        self.frame_list = frame_list
        self.lidar_list = lidar_list

    def start(self):
        camera_thread = threading.Thread(target=self.process_cam_frames)
        camera_thread.start()
        
        print("Camera thread started")

        lidar_thread = threading.Thread(target=self.process_lidar_data)
        lidar_thread.start()
        
        print("Lidar thread started")

    def process_cam_frames(self):
        print("Processing camera frames", self.camera)
        while True:
            frameraw, framehsv = self.camera.capture_array()
            
            print(f"frameraw: {frameraw.shape}")
            simplified_image = self.camera.simplify_image(framehsv, [0, 255, 0], [255, 0, 0])
            object_image = self.camera.draw_blocks(frameraw, framehsv)
            
            # Update shared list with the new frames
            self.frame_list[0] = frameraw.tobytes()
            self.frame_list[1] = simplified_image.tobytes()
            self.frame_list[2] = object_image.tobytes()
            
    def process_lidar_data(self):
        print("Processing LIDAR data", self.lidar)
        while True:
            print(f"Lidar data: {self.lidar.data_arrays}")
            if self.lidar.data_arrays:
                self.lidar_list[0] = self.lidar.data_arrays[-1].tobytes()
                print(f"Lidar data: {self.lidar_list[0]}")
            time.sleep(0.1)
