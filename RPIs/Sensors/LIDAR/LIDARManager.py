import usb
import serial
import json
import time

class LidarSensor():
    def __init__(self, usb_address=None, LIDAR_commands_path="./LIDARCommands.json"):
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
    
    def reset_sensor(self, response_size=13):
        """
        Reset the LIDAR sensor.

        Args:
            response_size (int, optional): Byte size of the response to the reset command. Defaults to 13.

        Returns:
            str: The response from the LIDAR sensor.
        """
        
        self.ser_device.write(f'{self.LIDAR_commands["RESET"]}'.encode())
        time.sleep(0.5)
        
        while self.ser_device.available() < response_size:
            pass
        
        response = self.ser_device.read(response_size)
        
        return response
    
    def start_sensor(self, response_size=7):
        """
        Start the LIDAR sensor.

        Args:
            response_size (int, optional): Byte size of the respomse to the start command. Defaults to 7.
        """
        
        self.ser_device.write(f'{self.LIDAR_commands["SCAN"]}'.encode())
        
        while self.ser_device.available() < response_size:
            pass
        
        response = self.ser_device.read(response_size)
        
    def stop_sensor(self):
        """
        Stop the LIDAR sensor.
        """
        self.ser_device.write(f'{self.LIDAR_commands["STOP"]}'.encode())
        self.ser_device.close()
