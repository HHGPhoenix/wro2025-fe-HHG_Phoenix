from evdev import InputDevice, ecodes, list_devices
import threading
import time

class PSController():
    def __init__(self, servo_middle_angle=7.5, servo_min_angle=5, servo_max_angle=10):
        self.servo_middle_angle = servo_middle_angle
        self.servo_min_angle = servo_min_angle
        self.servo_max_angle = servo_max_angle
        
        self.AXIS_CODES = {
            ecodes.ABS_X: 'left_analog_x',
            ecodes.ABS_Y: 'left_analog_y',
            ecodes.ABS_RX: 'right_analog_x',
            ecodes.ABS_RY: 'right_analog_y'
        }
        
        self.calibrated_x_value = 128
        self.calibrated_y_value = 128
        self.calibrated_rx_value = 128
        self.calibrated_ry_value = 128
        
        self.left_analog_x = 128
        self.left_analog_y = 128
        self.right_analog_x = 128
        self.right_analog_y = 128

        self.device_path = self.find_ps4_controller()
        print(f"Found PS4 controller at {self.device_path}")
        self.device = InputDevice(self.device_path)
        
        threading.Thread(target=self.get_raw_analog_stick_values).start()
        
    def find_ps4_controller(self):
        devices = [InputDevice(path) for path in list_devices()]
        for device in devices:
            if "Wireless Controller" in device.name:
                return device.path
            
        raise RuntimeError("PS controller not found")
    
    def calibrate_analog_sticks(self):
        left_analog_x_values = []
        left_analog_y_values = []
        right_analog_x_values = []
        right_analog_y_values = []
        
        for _ in range(100):
            left_analog_x_values.append(self.left_analog_x)
            left_analog_y_values.append(self.left_analog_y)
            right_analog_x_values.append(self.right_analog_x)
            right_analog_y_values.append(self.right_analog_y)
            time.sleep(0.01)
            
        self.calibrated_x_value = sum(left_analog_x_values) / len(left_analog_x_values)
        self.calibrated_y_value = sum(left_analog_y_values) / len(left_analog_y_values)
        self.calibrated_rx_value = sum(right_analog_x_values) / len(right_analog_x_values)
        self.calibrated_ry_value = sum(right_analog_y_values) / len(right_analog_y_values)
        
        print(f"Calibrated values: {self.calibrated_x_value}, {self.calibrated_y_value}, {self.calibrated_rx_value}, {self.calibrated_ry_value}")
        
    def get_raw_analog_stick_values(self):
        for event in self.device.read_loop():
            if event.type == ecodes.EV_ABS and event.code in self.AXIS_CODES:
                if self.AXIS_CODES[event.code] == 'left_analog_x':
                    self.left_analog_x = event.value
                elif self.AXIS_CODES[event.code] == 'left_analog_y':
                    self.left_analog_y = event.value
                elif self.AXIS_CODES[event.code] == 'right_analog_x':
                    self.right_analog_x = event.value
                elif self.AXIS_CODES[event.code] == 'right_analog_y':
                    self.right_analog_y = event.value

    def get_analog_stick_values(self):
        left_analog_x_value = self.left_analog_x / self.calibrated_x_value / 2
        left_analog_y_value = self.left_analog_y / self.calibrated_y_value / 2
        right_analog_x_value = self.right_analog_x / self.calibrated_rx_value / 2
        right_analog_y_value = self.right_analog_y / self.calibrated_ry_value / 2
        
        # Limit the values to the range of 0 - 1
        left_analog_x_value = max(0, min(left_analog_x_value, 1))
        left_analog_y_value = max(0, min(left_analog_y_value, 1))
        right_analog_x_value = max(0, min(right_analog_x_value, 1))
        right_analog_y_value = max(0, min(right_analog_y_value, 1))
        
        return left_analog_x_value, left_analog_y_value, right_analog_x_value, right_analog_y_value    
    
    def map_servo_angle(self, value):
        if value <= 0.5:
            # Map the value from 0-0.5 to 5-6.7
            return (value * 2) * (self.servo_middle_angle - self.servo_min_angle) + self.servo_min_angle
        else:
            # Map the value from 0.5-1 to 6.7-10
            return ((value - 0.5) * 2) * (self.servo_max_angle - self.servo_middle_angle) + self.servo_middle_angle
        
    def map_speed_value(self, value):
        return (1 - value - 0.5) * 300