import cv2
import numpy as np
from multiprocessing import Manager
import time
import threading
import pandas as pd
from scipy.interpolate import interp1d
from RPIs.Devices.Camera.CameraManager import Camera

class DataTransferer:
    def __init__(self, lidar, frame_list=None, lidar_data_list=None, interpolated_lidar_data=None):
        self.frame_list = frame_list
        
        self.lidar = lidar
        self.lidar_data_list = lidar_data_list
        self.interpolated_lidar_data = interpolated_lidar_data

    def start(self):
        self.camera_thread = threading.Thread(target=self.process_cam_frames)
        self.camera_thread.daemon = False
        self.camera_thread.start()
        
        print("Camera thread started")

        self.lidar_thread = threading.Thread(target=self.process_lidar_data)
        self.lidar_thread.daemon = False
        self.lidar_thread.start()
        
        print("Lidar thread started")

        #stop those


    def stop(self):
        self.camera_thread.join()
        self.lidar_thread.join()

    def process_cam_frames(self):
        self.camera = Camera()
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
                while len(self.lidar_data_list) == 0:
                    print("No LIDAR data available")
                    time.sleep(0.1)
                
                start_time = time.time()
                
                lidar_data = self.lidar_data_list[-1]
                
                # Sort data by angle
                lidar_data.sort(key=lambda x: x[0], reverse=True)
                
                # Create DataFrame
                df = pd.DataFrame(lidar_data, columns=["angle", "distance", "intensity"])
                
                # Remove rows where distance is 0
                df = df[df["distance"] != 0]
                
                # Sort by angle
                df = df.sort_values("angle")
                
                # Desired angles for interpolation
                desired_angles = np.arange(0, 360, 1)
                
                # Interpolate distance and intensity
                interp_distance = interp1d(df["angle"], df["distance"], kind="linear", bounds_error=False, fill_value="extrapolate")
                interp_intensity = interp1d(df["angle"], df["intensity"], kind="linear", bounds_error=False, fill_value="extrapolate")

                interpolated_distances = interp_distance(desired_angles)
                interpolated_intensities = interp_intensity(desired_angles)

                # Create DataFrame for interpolated data
                df_interpolated = pd.DataFrame({
                    "angle": desired_angles,
                    "distance": interpolated_distances,
                    "intensity": interpolated_intensities
                })

                # Handle NaN and Inf values
                df_interpolated.replace([np.inf, -np.inf], np.nan, inplace=True)
                df_interpolated["distance"].fillna(method='ffill', inplace=True)
                df_interpolated["distance"].fillna(method='bfill', inplace=True)
                df_interpolated["intensity"].fillna(method='ffill', inplace=True)
                df_interpolated["intensity"].fillna(method='bfill', inplace=True)

                # Filter angles not within the range [140, 220]
                df_interpolated = df_interpolated[(df_interpolated["angle"] < 140) | (df_interpolated["angle"] > 220)]

                # Convert to list and round values
                df_interpolated_list = df_interpolated.values.tolist()
                df_interpolated_list = [[round(angle, 3), round(distance, 3), round(intensity, 3)] for angle, distance, intensity in df_interpolated_list]

                # Store the processed data
                self.interpolated_lidar_data[0] = df_interpolated_list
                self.interpolated_lidar_data[0].sort(key=lambda x: x[0], reverse=True)

                # Measure elapsed time
                elapsed_time = time.time() - start_time
                wait_time = max(0.1 - elapsed_time, 0)
                time.sleep(wait_time)

                if wait_time < 0:
                    print(f"Processing LIDAR data took longer than 100ms: {elapsed_time}")
                
        except KeyboardInterrupt:
            pass
        except BrokenPipeError:
            pass
        except EOFError:
            pass
        except KeyError:
            pass
