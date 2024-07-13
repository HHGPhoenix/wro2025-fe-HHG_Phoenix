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
        camera_thread.start()
        
        print("Camera thread started")

        lidar_thread = threading.Thread(target=self.process_lidar_data)
        lidar_thread.start()
        
        print("Lidar thread started")

    def process_cam_frames(self):
        print("Processing camera frames", self.camera)
        try:
            while True:
                frameraw, framehsv = self.camera.capture_array()
                
                frameraw = self.camera.compress_frame(frameraw)
                framehsv = self.camera.compress_frame(framehsv)
                
                # print(f"frameraw: {frameraw.shape}")
                simplified_image = self.camera.simplify_image(framehsv.copy(), [0, 255, 0], [255, 0, 0])
                object_image = self.camera.draw_blocks(frameraw.copy(), framehsv.copy())
                
                # Update shared list with the new frames
                self.frame_list[0] = frameraw.tobytes()
                self.frame_list[1] = simplified_image.tobytes()
                self.frame_list[2] = object_image.tobytes()
        except KeyboardInterrupt:
            pass
        except BrokenPipeError:
            pass
        except EOFError:
            pass
            
    def process_lidar_data(self):
        print("Processing LIDAR data", self.lidar)
        try:
            while True:
                if len(self.lidar_data_list) == 0:
                    continue
                
                start_time = time.time()
                
                lidar_data = self.lidar_data_list[-1]
                
                lidar_data.sort(key=lambda x: x[0], reverse=True)
                
                df = pd.DataFrame(lidar_data, columns=["angle", "distance", "intensity"])
                
                # Instead of dropping the "intensity" column, keep it
                df = df[(df["distance"] != 0)]
                
                # Sort the data by angle
                df = df.sort_values("angle")
                
                # Define the desired angles (one point per angle from 0 to 359)
                desired_angles = np.arange(0, 360, 1)
                
                # Interpolate distance and intensity for missing angles, use nearest for fill_value
                interp_distance = interp1d(df["angle"], df["distance"], kind="linear", bounds_error=False, fill_value="extrapolate")
                interp_intensity = interp1d(df["angle"], df["intensity"], kind="linear", bounds_error=False, fill_value="extrapolate")
                
                # Generate the interpolated values for distance and intensity
                interpolated_distances = interp_distance(desired_angles)
                interpolated_intensities = interp_intensity(desired_angles)
                
                # Create the new list with interpolated data including intensity
                interpolated_data = list(zip(desired_angles, interpolated_distances, interpolated_intensities))
                
                # Convert to DataFrame for easier manipulation, now including intensity
                df_interpolated = pd.DataFrame(interpolated_data, columns=["angle", "distance", "intensity"])
                
                # Remove data from 110 to 250 degrees
                df_interpolated = df_interpolated[(df_interpolated["angle"] < 140) | (df_interpolated["angle"] > 220)]
                
                df_interpolated_list = df_interpolated.values.tolist()
                
                self.interpolated_lidar_data[0] = df_interpolated_list
                
                self.interpolated_lidar_data[0].sort(key=lambda x: x[0], reverse=True)
                
                elapsed_time = time.time() - start_time  # Calculate elapsed time
                wait_time = max(0.1 - elapsed_time, 0)  # Adjust wait time to ensure loop runs every 100ms
                time.sleep(wait_time)  # Wait for the adjusted time

        except KeyboardInterrupt:
            pass
        except BrokenPipeError:
            pass
        except EOFError:
            pass
        except KeyError:
            pass
