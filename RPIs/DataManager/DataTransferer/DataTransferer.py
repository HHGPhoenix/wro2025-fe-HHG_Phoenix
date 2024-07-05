import cv2
import numpy as np
from multiprocessing import Manager
import time
import threading
import pandas as pd
from scipy.interpolate import interp1d

class DataTransferer:
    def __init__(self, cam, lidar, frame_list=None, lidar_data_list=None, interpolated_lidar_data=None):
        self.camera = cam
        self.frame_list = frame_list
        
        self.lidar = lidar
        self.lidar_data_list = lidar_data_list
        self.interpolated_lidar_data = interpolated_lidar_data

    def start(self):
        camera_thread = threading.Thread(target=self.process_cam_frames)
        # camera_thread.start()
        
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
            if len(self.lidar_data_list) == 0:
                continue
            
            start_time = time.time()
            
            lidar_data = self.lidar_data_list[-1]
            
            df = pd.DataFrame(lidar_data, columns=["angle", "distance", "intensity"])
            
            df = df.drop(columns=["intensity"])

            # Filter out invalid points (distance zero)
            df = df[(df["distance"] != 0)]
            df["angle"] = (df["angle"] - 90) % 360

            # Sort the data by angle
            df = df.sort_values("angle")

            # Define the desired angles (one point per angle from 0 to 359)
            desired_angles = np.arange(0, 360, 1)

            # Interpolate distance for missing angles, use nearest for fill_value
            interp_distance = interp1d(df["angle"], df["distance"], kind="linear", bounds_error=False, fill_value=(df["distance"].iloc[0], df["distance"].iloc[-1]))

            # Generate the interpolated values
            interpolated_distances = interp_distance(desired_angles)

            # Create the new list with interpolated data
            interpolated_data = list(zip(desired_angles, interpolated_distances))

            # Convert to DataFrame for easier manipulation
            df_interpolated = pd.DataFrame(interpolated_data, columns=["angle", "distance"])

            # Remove data from 110 to 250 degrees
            df_interpolated = df_interpolated[(df_interpolated["angle"] < 110) | (df_interpolated["angle"] > 250)]

            df_interpolated_list = df_interpolated.values.tolist()  
            
            self.interpolated_lidar_data[0] = df_interpolated_list
            
            elapsed_time = time.time() - start_time  # Calculate elapsed time
            wait_time = max(0.1 - elapsed_time, 0)  # Adjust wait time to ensure loop runs every 100ms
            time.sleep(wait_time)  # Wait for the adjusted time