import json
import time
import random
import struct
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import pandas as pd
from scipy.interpolate import interp1d

class Lidar():
    def __init__(self, lidar_data_list):
        """
        Initialize the dummy LIDAR sensor with random behavior.
        
        Args:
            address (str): The address of the LIDAR sensor.
            LIDAR_commands_path (str, optional): Path to the LIDAR command mapping. Defaults to "./LIDARCommands.json".
        """
        
        self.lidar_data_list = lidar_data_list
        self.ser_device = "DummySerial"  # Placeholder for the serial device
        
        self.reset_sensor()

    def reset_sensor(self):
        """
        Simulate resetting the LIDAR sensor.
        """
        # print("Dummy reset sensor")
        time.sleep(0.5)  # Simulate time delay for reset

    def start_sensor(self, response_size=7, mode="normal"):
        """
        Simulate starting the LIDAR sensor.
        
        Args:
            response_size (int, optional): Byte size of the response to the start command. Defaults to 7.
            
        Returns:
            str: A dummy response from the LIDAR sensor.
        """
        # print(f"Dummy start sensor in {mode} mode")
        # Generate a random byte response
        response = bytes(random.getrandbits(8) for _ in range(response_size))
        return response

    def stop_sensor(self):
        """
        Simulate stopping the LIDAR sensor.
        """
        # print("Dummy stop sensor")

    def read_data(self):
        """
        Simulate reading data from the LIDAR sensor.
        """
        # start_time = time.time()

        try:

            while True:
                time.sleep(0.1)  # Simulate data reading delay
                current_lidar_data = []
                
                for i in range(360):
                    distance = random.uniform(100, 3000)
                    intensity = random.randint(0, 255)
                    current_lidar_data.append((i, distance, intensity))
                    
                self.lidar_data_list.append(current_lidar_data)
                
                if len(self.lidar_data_list) > 10:
                    self.lidar_data_list.pop(0)

        except KeyboardInterrupt:
            pass
        except BrokenPipeError:
            pass

    def set_motor_speed(self, rpm):
        if not (0 <= rpm <= 65535):
            raise ValueError("RPM value must be between 0 and 65535")
        
        # Simulate setting motor speed
        # print(f"Dummy set motor speed to {rpm} RPM")

    def polar_plot(self, lidar_data):
        """
        Generates a polar scatter plot from LIDAR data and returns the plot image as a bytes object.

        Parameters:
        - lidar_data: A list of tuples or a 2D array where each tuple/row contains (angle in degrees, distance).

        Returns:
        - A bytes object containing the image of the polar scatter plot.
        """
        angles_degrees, distances, _ = zip(*lidar_data)
        angles_radians = np.radians(angles_degrees)

        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
        ax.scatter(angles_radians, distances)

        ax.set_title('Dummy LIDAR Data Polar Scatter Plot', va='bottom')
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)

        img_bytes = BytesIO()
        fig.savefig(img_bytes, format='png')
        img_bytes.seek(0)

        plt.close(fig)
        return img_bytes.getvalue()

    def interpolate_data(self, lidar_data, step=1, cutoff=(110, 250), rotation=0):
        """
        Interpolates the LIDAR data to fill in missing angles and returns the interpolated data.

        Args:
            lidar_data: A list of tuples or a 2D array where each tuple/row contains (angle in degrees, distance, intensity).
            step (int, optional): Step size of the interpolation. Defaults to 1.
            cutoff (tuple, optional): LIDAR data cutoff angles. Defaults to (110, 250).
            rotation (int, optional): Angle to rotate the lidar data. Defaults to 0.

        Returns:
            interpolated_data: A list of tuples where each tuple contains (angle in degrees, distance).
        """
        df = pd.DataFrame(lidar_data, columns=["angle", "distance", "intensity"])
        df = df.drop(columns=["intensity"])
        df = df[df["distance"] != 0]
        df["angle"] = (df["angle"] - rotation) % 360
        df = df.sort_values("angle")

        desired_angles = np.arange(0, 360, step)
        interp_distance = interp1d(df["angle"], df["distance"], kind="linear", bounds_error=False, fill_value="extrapolate")
        interpolated_distances = interp_distance(desired_angles)

        interpolated_data = list(zip(desired_angles, interpolated_distances))

        df_interpolated = pd.DataFrame(interpolated_data, columns=["angle", "distance"])
        df_interpolated = df_interpolated[(df_interpolated["angle"] < cutoff[0]) | (df_interpolated["angle"] > cutoff[1])]

        df_interpolated_list = df_interpolated.values.tolist()
        return df_interpolated_list

# Example usage
if __name__ == "__main__":
    dummy_lidar_data_list = []
    dummy_sensor = LidarSensor("dummy_address", dummy_lidar_data_list)
    
    dummy_sensor.reset_sensor()
    response = dummy_sensor.start_sensor()
    # print(f"Start response: {response}")
    
    dummy_sensor.read_data()
    dummy_sensor.set_motor_speed(300)
    
    lidar_data = [(i, random.uniform(100, 3000), random.randint(0, 255)) for i in range(360)]
    img_bytes = dummy_sensor.polar_plot(lidar_data)
    
    interpolated_data = dummy_sensor.interpolate_data(lidar_data)
    # # print(f"Interpolated data: {interpolated_data[:5]}")  # Print first 5 entries of interpolated data
    # print(f"Interpolated data length: {len(interpolated_data)}")
