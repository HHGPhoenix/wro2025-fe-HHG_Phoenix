class DummySerial:
    def write(self, message):
        # Dummy write method to mimic serial communication
        print(message.decode(), end='')

class MotorController:
    def __init__(self):
        # Replace actual serial communication with dummy serial
        self.ser = DummySerial()
    
    def map_speed_value(self, value):
        return (0.5 - value) * 510
    
    def send_speed(self, value):
        mapped_value = self.map_speed_value(value)
        self.ser.write(("SPEED " + str(mapped_value) + "\n").encode())
        if mapped_value >= 0:
            print(f"Sent message: SPEED +{mapped_value:.4f}", end=' ')
        else:
            print(f"Sent message: SPEED {mapped_value:.4f}", end=' ')

# Example usage
if __name__ == "__main__":
    mc = MotorController()
    mc.send_speed(0.3)
    mc.send_speed(0.7)
