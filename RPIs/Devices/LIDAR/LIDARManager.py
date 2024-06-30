import usb
import serial
import json
import time
import struct
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import pandas as pd    
from scipy.interpolate import interp1d

class LidarSensor():
    def __init__(self, address, shared_data_list, LIDAR_commands_path=r"RPIs/Devices/LIDAR/LIDARCommands.json"):
        """
        Initialize the LIDAR sensor by finding the usb device and resetting it.

        Args:
            address (str): The address of the LIDAR sensor.
            LIDAR_commands_path (str, optional): Path to the LIDAR command mapping. Defaults to "./LIDARCommands.json".
        """
        
        with open(LIDAR_commands_path) as f:
            self.LIDAR_commands = json.load(f)
        
        self.ser_device = serial.Serial(address, 460800)
        self.shared_data_list = shared_data_list
            
        self.reset_sensor()
    
    def reset_sensor(self):
        """
        Reset the LIDAR sensor.
        """
        command = bytes.fromhex(self.LIDAR_commands['RESET'].replace('\\x', ''))
        self.ser_device.write(command)
        
        self.ser_device.reset_output_buffer()
        self.ser_device.reset_input_buffer()
        
        # Wait for the sensor to reset
        time.sleep(0.5)
        
        while self.ser_device.in_waiting < 21:
            pass
        
        _ = self.ser_device.read(21)

    
    def start_sensor(self, response_size=7, mode="normal"):
        """
        Start the LIDAR sensor.
    
        Args:
            response_size (int, optional): Byte size of the respomse to the start command. Defaults to 7.
            
        Returns:
            str: The response from the LIDAR sensor.
        """
        if mode == "normal":
            command = bytes.fromhex(self.LIDAR_commands['SCAN'].replace('\\x', ''))
            self.ser_device.write(command)
            
            time.sleep(0.2)
            
            while self.ser_device.in_waiting < response_size:
                # print(self.ser_device.in_waiting)
                pass
            
            response = self.ser_device.read(response_size)
            
            return response
        
        elif mode == "express":
            command = bytes.fromhex(self.LIDAR_commands['EXPRESS_SCAN'].replace('\\x', ''))
            self.ser_device.write(command)
            
            while self.ser_device.in_waiting < response_size:
                pass
            
            response = self.ser_device.read(response_size)
            
            return response
        
    def stop_sensor(self):
        """
        Stop the LIDAR sensor.
        """
        command = bytes.fromhex(self.LIDAR_commands['STOP'].replace('\\x', ''))
        self.ser_device.write(command)
        self.ser_device.close()

    def read_data(self):
        """
        Read the data from the LIDAR sensor. This function is blocking and will run indefinitely.
        """
        
        self.data_arrays = []  # This will hold the arrays of data
        self.current_array = []  # This will hold the current array of data
        start_time = time.time()  # Start time for measuring the frequency

        while True:
            if self.ser_device.in_waiting >= 400:
                data = self.ser_device.read(400)
                
                # Ensure proper alignment by checking the start and stop bits
                i = 0
                while i <= len(data) - 5:
                    chunk = data[i:i+5]
                    
                    # Extract the S and S_bar bits from the first byte
                    S = (chunk[0]) & 0x01  # Bit 1 of the first byte
                    S_bar = (chunk[0] >> 1) & 0x01  # Bit 2 of the first byte
                    C = (chunk[1]) & 0x01  # Bit 3 of the first byte
                    
                    # print(C)
                    
                    # Check if the start and stop bits are correct (S and S_bar should complement each other)
                    if C == 1 and S == (1 - S_bar):
                        quality = chunk[0] >> 2  # Extracts the quality from the first byte
                        angle = ((chunk[2] << 7) + (chunk[1] >> 1)) / 64.0  # Extracts the angle from the second and third bytes
                        distance = ((chunk[3]) + (chunk[4] << 8)) / 4.0  # Extracts the distance from the fourth and fifth bytes

                        self.current_array.append((angle, distance, quality))

                        # If the angle has looped back to the start, save the current array and start a new one
                        if len(self.current_array) > 1 and S == 1 and S_bar == 0:
                            self.shared_data_list.append(self.current_array[: -2])
                            missing_data = self.current_array[-1]
                            self.current_array = [missing_data]

                            # Calculate and print the frequency
                            end_time = time.time()
                            frequency = 1.0 / (end_time - start_time)
                            # print(f"Frequency: {frequency} Hz")
                            # print(f"Data points: {shared_data_list[-1]}")
                            start_time = end_time

                        if len(self.shared_data_list) > 0 and len(self.shared_data_list) > 100:
                            self.shared_data_list.pop(0)

                        i += 5  # Move to the next chunk
                    else:
                        # If not correctly aligned, check the next byte
                        i += 1
                        print("Not aligned: ", C, S, S_bar)
                    # if shared list is not empty print a message
            # if len(self.shared_data_list) > 0:
            #     print("Shared list: ", self.shared_data_list[-1])
            #     print("Length of shared list: ", len(self.shared_data_list))

                                    
    def set_motor_speed(self, rpm):
        if not (0 <= rpm <= 65535):
            raise ValueError("RPM value must be between 0 and 65535")
        
        # Packet components
        header = b'\xA5\xA8'
        command = b'\x02'
        rpm_bytes = struct.pack('<H', rpm)  # Convert the RPM value to 2 bytes (little-endian)

        # Construct the packet
        packet = header + command + rpm_bytes
        
        # Send the packet to the device
        self.ser_device.write(packet)
        
    
    def polar_plot(self, lidar_data):
        """
        Generates a polar scatter plot from LIDAR data and returns the plot image as a bytes object.

        Parameters:
        - lidar_data: A list of tuples or a 2D array where each tuple/row contains (angle in degrees, distance).

        Returns:
        - A bytes object containing the image of the polar scatter plot.
        """
        # Convert the LIDAR data into two lists: angles and distances
        angles_degrees, distances, _ = zip(*lidar_data)
        angles_radians = np.radians(angles_degrees)  # Convert angles to radians for plotting

        # Create a polar scatter plot
        fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})
        ax.scatter(angles_radians, distances)

        # Customize the plot (optional)
        ax.set_title('LIDAR Data Polar Scatter Plot', va='bottom')
        ax.set_theta_zero_location('N')  # Zero degrees at the top
        ax.set_theta_direction(-1)  # Clockwise

        # Save the plot to a BytesIO object and return it
        img_bytes = BytesIO()
        fig.savefig(img_bytes, format='png')
        img_bytes.seek(0)  # Go to the beginning of the BytesIO object

        # Close the figure to free up memory
        plt.close(fig)

        return img_bytes.getvalue()
    
    def interpolate_data(self, lidar_data, step=1, cutoff=(110, 250), rotation=0):
        """
        Interpolates the LIDAR data to fill in missing angles and returns the interpolated data.

        Args:
            lidar_data (_type_): A list of tuples or a 2D array where each tuple/row contains (angle in degrees, distance, intensity).
            step (int, optional): Step size of the interpolation. Defaults to 1.
            cutoff (tuple, optional): LIDAR data cutoff angles. Defaults to (110, 250).
            rotation (int, optional): Angle to rotate the lidar data. Defaults to 0.

        Returns:
            interpolated_data: A list of tuples where each tuple contains (angle in degrees, distance).
        """
        
        df = pd.DataFrame(lidar_data, columns=["angle", "distance", "intensity"])
        df = df.drop(columns=["intensity"])
        df = df[df["distance"] != 0]  # Filter out invalid points
        df["angle"] = (df["angle"] - rotation) % 360
        df = df.sort_values("angle")

        desired_angles = np.arange(0, 360, step)
        interp_distance = interp1d(df["angle"], df["distance"], kind="linear", bounds_error=False, fill_value="extrapolate")
        interpolated_distances = interp_distance(desired_angles)

        interpolated_data = list(zip(desired_angles, interpolated_distances))
        
        # Convert to DataFrame for easier manipulation
        df_interpolated = pd.DataFrame(interpolated_data, columns=["angle", "distance"])

        # Remove data from 110 to 250 degrees
        df_interpolated = df_interpolated[(df_interpolated["angle"] < cutoff[0]) | (df_interpolated["angle"] > cutoff[1])]

        df_interpolated_list = df_interpolated.values.tolist()
        
        return df_interpolated_list
