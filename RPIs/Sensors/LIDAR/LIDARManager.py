import usb
import serial

class LidarSensor():
    def __init__(self, usb_address=None):
        if usb_address is not None:
            self.ser_device = serial.Serial(usb_address, 115200)
        
        else:
            self.ser_device = self.find_usb_device(0x10c4, 0xea60)
            if self.ser_device is None:
                raise Exception("Lidar sensor not found, try specifying the USB address manually.")
            self.ser_device = serial.Serial(self.ser_device, 115200)
        
    def find_usb_device(self, vendor_id, product_id):
        # Find the device by vendor and product id
        for device in usb.core.find(find_all=True):
            if device.idVendor == vendor_id and device.idProduct == product_id:
                return device
        return None
    
    def start_sensor(self):
        self.ser_device.open()
        self.ser_device.write(b'\xA5\x60')
        
    def stop_sensor(self):
        self.ser_device.write(b'\xA5\x25')
        self.ser_device.close()
        
    def read_data(self):
        return self.ser_device.read(9)