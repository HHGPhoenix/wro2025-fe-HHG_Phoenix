import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from gpiozero import CPUTemperature
import psutil

#A class for writing to a OLED Display
class Display():
    def __init__(self):
        serial = i2c(port=0, address=0x3C)
        self.device = sh1106(serial)
        
        #Variable init
        self.first_line = ""
        self.second_line = ""
        self.threadStop = 0
        
        # Wake the screen by drawing an outline
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="white", fill="black")
    
    
    #Clear the Display 
    def clear(self):
        with canvas(self.device) as draw:
            draw.rectangle(self.device.bounding_box, outline="white", fill="black")
    
    
    #Write lines in variables so they get written by the update function   
    def write(self, first_line="", second_line="", reset=False, xCoord=0, yCoord=17):
        if reset:
            self.first_line = ""
            self.second_line = ""
        
        if first_line != "":
            self.first_line = first_line
        if second_line != "":
            self.second_line = second_line
        

    #Update the Display
    def update(self):
        while self.threadStop == 0:
            #Get CPU temperature, CPU usage, RAM usage and Disk usage
            cpuTemp = CPUTemperature()
            self.cpu_usage = psutil.cpu_percent(interval=0)
            self.ram = psutil.virtual_memory()
            self.disk = psutil.disk_usage('/')
            
            #Format them to always have the same number of decimal points
            cpu_temp_formatted = self.Utils.convert_to_decimal_points(cpuTemp.temperature, 1)
            cpu_usage_formatted = self.Utils.convert_to_decimal_points(self.cpu_usage, 1)
            ram_usage_formatted = self.Utils.convert_to_decimal_points(self.ram.percent, 1)
            disk_usage_formatted = self.Utils.convert_to_decimal_points(self.disk.percent, 1)
            voltage_value_formatted = self.Utils.convert_to_decimal_points(self.Utils.ADC.voltage, 2)
            
            #Draw all the data on the Display
            with canvas(self.device) as draw:
                    #top
                    draw.text((0, 0), f"{cpu_temp_formatted}°C", fill="white", align="left")
                    draw.text((40, 0), f"DISK:{(int(float(disk_usage_formatted)))}%", fill="white")
                    draw.text((92, 0), f"{voltage_value_formatted}V", fill="white")
                    
                    #bottom
                    draw.text((0, 50), f"CPU:{cpu_usage_formatted}%", fill="white")
                    draw.text((75, 50), f"RAM:{ram_usage_formatted}%", fill="white")
                    
                    #custom
                    draw.multiline_text((0, 15), f"{self.first_line}\n{self.second_line}", fill="white", align="center", anchor="ma")
                    
            time.sleep(2)