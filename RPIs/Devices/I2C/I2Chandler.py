from RPIs.Devices.I2C.Gyro.GyroManager import GyroSensor

class I2Chandler:
    def __init__(self):
        """
        Initialize the I2Chandler and all of its components.
        """
        
        # self.Gyro = GyroSensor()
        
    def start_threads(self):
        """
        Start the I2C sensor threads.
        """
        
        # gyro_thread = threading.Thread(target=self.Gyro.start)
        # gyro_thread.start()
        
    def stop_threads(self):
        """
        Stop the I2C sensor threads.
        """
        
        # self.Gyro.stop()
        
if __name__ == '__main__':
    i2c_handler = I2Chandler()
    i2c_handler.start_threads()