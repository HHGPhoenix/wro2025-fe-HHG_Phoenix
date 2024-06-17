import busio
import board
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

class AnalogDigitalConverter():
    def __init__(self, channel=1, bus=1):
        """
        Initialize the ADC

        Args:
            channel (int, optional): The channel of the ADC to read from. Defaults to 1.
            bus (int, optional): The I2C bus the ADC is connected to. Defaults to 1.

        Raises:
            Exception: If an invalid channel is specified
            
        Returns:
            None
        """

        self.threadStop = 0
        self.channel = channel
        self.voltage = 12
        
        if bus == 1:
            i2c = busio.I2C(board.SCL, board.SDA)
        elif bus == 0:
            i2c = busio.I2C(board.D1, board.D0)
        
        #ADC init
        self.ads = ADS.ADS1015(i2c)
        self.ads.active = True
        
        #Channel init
        if channel == 0:
            self.chan = AnalogIn(self.ads, ADS.P0)
        elif channel == 1:
            self.chan = AnalogIn(self.ads, ADS.P1)
        elif channel == 2:
            self.chan = AnalogIn(self.ads, ADS.P2)
        elif channel == 3:
            self.chan = AnalogIn(self.ads, ADS.P3)
        else:
            raise Exception(f"No valid ADC channel specified: {channel}")
        
        return
       
    def read(self):
        """
        Read the voltage from the ADC as long as the threadStop flag is not set.
        
        Returns:
            None
        """
        while self.threadStop == 0:
            self.voltage = self.chan.voltage * 4.395