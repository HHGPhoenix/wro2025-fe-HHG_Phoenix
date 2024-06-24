import usb
import serial
import json
import time
import struct

class LidarSensor():
    def __init__(self, usb_address=None, LIDAR_commands_path=r"RPIs\Sensors\LIDAR\LIDARCommands.json"):
        """
        Initialize the LIDAR sensor by finding the usb device and resetting it.

        Args:
            usb_address (str, optional): When manually set disable auto-detect. Defaults to None.
            LIDAR_commands_path (str, optional): Path to the LIDAR command mapping. Defaults to "./LIDARCommands.json".

        Raises:
            Exception: When the auto-detect could not find the LIDAR sensor.
        """
        
        with open(LIDAR_commands_path) as f:
            self.LIDAR_commands = json.load(f)
        
        if usb_address is not None:
            self.ser_device = serial.Serial(usb_address, 460800)
        
        else:
            self.ser_device = self.find_usb_device(0x10c4, 0xea60)
            if self.ser_device is None:
                raise Exception("Lidar sensor not found, try specifying the USB address manually.")
            self.ser_device = serial.Serial(self.ser_device, 460800)
            
        self.reset_sensor()
        
    def find_usb_device(self, vendor_id, product_id):
        """
        Find the USB device by vendor and product id.

        Args:
            vendor_id (str): Vendor ID of the device.
            product_id (str): Product ID of the device.

        Returns:
            usb.core: The USB device.
        """
        
        # Find the device by vendor and product id
        for device in usb.core.find(find_all=True):
            if device.idVendor == vendor_id and device.idProduct == product_id:
                return device
        return None
    
    def reset_sensor(self):
        """
        Reset the LIDAR sensor.
        """
        command = bytes.fromhex(self.LIDAR_commands['RESET'].replace('\\x', ''))
        self.ser_device.write(command)
        
        while self.ser_device.in_waiting < 21:
            pass
        
        _ = self.ser_device.read(21)

        time.sleep(0.5)
    
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
            if self.ser_device.in_waiting >= 200:
                data = self.ser_device.read(200)
                
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
                            self.data_arrays.append(self.current_array[: -2])
                            missing_data = self.current_array[-1]
                            self.current_array = [missing_data]

                            # Calculate and print the frequency
                            end_time = time.time()
                            frequency = 1.0 / (end_time - start_time)
                            print(f"Frequency: {frequency} Hz")
                            start_time = end_time

                        if len(self.data_arrays) > 0 and len(self.data_arrays) > 100:
                            self.data_arrays.pop(0)

                        i += 5  # Move to the next chunk
                    else:
                        # If not correctly aligned, check the next byte
                        i += 1
                        print("Not aligned: ", C, S, S_bar)

                                    
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


