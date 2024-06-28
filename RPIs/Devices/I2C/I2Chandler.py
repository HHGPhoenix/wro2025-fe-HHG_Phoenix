from ADC.ADCManager import AnalogDigitalConverter
import threading

class I2Chandler:
    def __init__(self):
        """
        Initialize the I2Chandler and all of its components.
        """
        
        self.ADC = AnalogDigitalConverter(bus=0, channel=3)
        
    def start_threads(self):
        """
        Start the I2C sensor threads.
        """
        
        self.ADC.threadStop = 0
        adc_thread = threading.Thread(target=self.ADC.read)
        adc_thread.start()
        
    def stop_threads(self):
        """
        Stop the I2C sensor threads.
        """
        
        self.ADC.threadStop = 1