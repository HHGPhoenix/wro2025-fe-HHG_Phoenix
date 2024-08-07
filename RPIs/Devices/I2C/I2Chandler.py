from RPIs.Devices.I2C.ADC.ADCManager import AnalogDigitalConverter
from RPIs.Devices.I2C.Gyro.GyroManager import GyroSensor
import threading

class I2Chandler:
    def __init__(self):
        """
        Initialize the I2Chandler and all of its components.
        """
        
        self.ADC = AnalogDigitalConverter(bus=0, channel=3)
        
        self.Gyro = GyroSensor()
        
    def start_threads(self):
        """
        Start the I2C sensor threads.
        """
        
        self.ADC.threadStop = 0
        adc_thread = threading.Thread(target=self.ADC.read)
        adc_thread.start()
        
        gyro_thread = threading.Thread(target=self.Gyro.start)
        gyro_thread.start()
        
    def stop_threads(self):
        """
        Stop the I2C sensor threads.
        """
        
        self.ADC.threadStop = 1
        self.Gyro.stop()