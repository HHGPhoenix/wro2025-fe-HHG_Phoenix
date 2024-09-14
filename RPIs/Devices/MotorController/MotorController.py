import serial
import threading

class MotorController:
    def __init__(self, high_voltage=12.6, high_voltage_value=760, low_voltage=11.1, low_voltage_value=650):
        self.high_voltage = high_voltage
        self.high_voltage_value = high_voltage_value
        self.low_voltage = low_voltage
        self.low_voltage_value = low_voltage_value
        self.voltage = 0
        
        self.ser = serial.Serial('/dev/ttyUSB0', 921600)
        
        response_thread = threading.Thread(target=self.process_responses, daemon=True)
        response_thread.start()
    
    def map_speed_value(self, value):
        return (0.5 - value) * 510
    
    def send_speed(self, value):
        mapped_value = self.map_speed_value(value)
        self.ser.write(("SPEED " + str(mapped_value) + "\n").encode())

    def process_responses(self):
        while True:
            if self.ser.in_waiting > 0:
                response = self.ser.readline().decode()    
                responses = response.split("\n")
                for response in responses:
                    if "V: " in response:
                        self.voltage = self.map_voltage_value(float(response.split("V: ")[1]))
                        # print(f"Voltage: {self.voltage}")

    def map_voltage_value(self, value):
        proportion = (value - self.low_voltage_value) / (self.high_voltage_value - self.low_voltage_value)
        scaled_value = proportion * (self.high_voltage - self.low_voltage)
        return round(self.low_voltage + scaled_value, 2)