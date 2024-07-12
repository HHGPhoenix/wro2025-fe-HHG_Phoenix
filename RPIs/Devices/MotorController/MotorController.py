import serial

class MotorController:
    def __init__(self):
        self.ser = serial.Serial('/dev/ttyUSB0', 921600)
    
    def map_speed_value(self, value):
        return (0.5 - value) * 510
    
    def send_speed(self, value):
        mapped_value = self.map_speed_value(value)
        self.ser.write(("SPEED " + str(mapped_value) + "\n").encode())
        if mapped_value >= 0:
            print(f"Sent message: SPEED +{mapped_value:.4f}", end=' ')
        else:
            print(f"Sent message: SPEED {mapped_value:.4f}", end=' ')