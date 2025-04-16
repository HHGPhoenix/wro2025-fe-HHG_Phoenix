from pyPS4Controller.controller import Controller
import threading
import time

class PSController(Controller):
    def __init__(self, servo_middle_angle=7.5, servo_min_angle=5, servo_max_angle=10, **kwargs):
        self.servo_middle_angle = servo_middle_angle
        self.servo_min_angle = servo_min_angle
        self.servo_max_angle = servo_max_angle
        
        # Initialize analog stick values
        self.left_analog_x = 0.0
        self.left_analog_y = 0.0
        self.right_analog_x = 0.0
        self.right_analog_y = 0.0
        
        # Initialize button states
        self.cross = 0
        self.circle = 0
        self.triangle = 0
        self.square = 0
        self.right_trigger = 0
        
        # Call the parent class constructor
        Controller.__init__(self, **kwargs)
        

    
    # Left analog stick events
    def on_L3_up(self, value):
        self.left_analog_y = value / 32767.0  # Normalize to -1.0 to 1.0
    
    def on_L3_down(self, value):
        self.left_analog_y = value / 32767.0
    
    def on_L3_left(self, value):
        self.left_analog_x = value / 32767.0
    
    def on_L3_right(self, value):
        self.left_analog_x = value / 32767.0
    
    # Right analog stick events
    def on_R2_press(self, value):
        self.right_analog_y = value / 32767.0
    
    def on_L2_press(self, value):
        self.right_analog_x = value / 32767.0
    
    # def on_R3_left(self, value):
    #     self.right_analog_x = value / 32767.0
    
    # def on_R3_right(self, value):
    #     self.right_analog_x = value / 32767.0
    
    # Button events
    def on_x_press(self):
        self.cross = 1
    
    def on_x_release(self):
        self.cross = 0
    
    def on_circle_press(self):
        self.circle = 1
    
    def on_circle_release(self):
        self.circle = 0
    
    def on_triangle_press(self):
        self.triangle = 1
    
    def on_triangle_release(self):
        self.triangle = 0
    
    def on_square_press(self):
        self.square = 1
    
    def on_square_release(self):
        self.square = 0
    
    def on_R2_release(self):
        return

    def on_L2_release(self):
        return
    
    def on_L3_x_at_rest(self):
        return
    
    def on_L3_y_at_rest(self):
        return
    
    def on_R1_press(self):
        self.right_trigger = 1
        
    def on_R1_release(self):
        self.right_trigger = 0

    def get_analog_stick_values(self):
        # Convert to the expected range (0 to 1) instead of (-1 to 1)
        left_analog_x_value = (self.left_analog_x + 1) / 2
        left_analog_y_value = (self.left_analog_y + 1) / 2
        right_analog_x_value = (self.right_analog_x + 1) / 2
        right_analog_y_value = (self.right_analog_y + 1) / 2
        
        # Limit the values to the range of 0 - 1
        left_analog_x_value = round(max(0, min(left_analog_x_value, 1)), 3)
        left_analog_y_value = round(max(0, min(left_analog_y_value, 1)), 3)
        right_analog_x_value = round(max(0, min(right_analog_x_value, 1)), 3)
        right_analog_y_value = round(max(0, min(right_analog_y_value, 1)), 3)
        
        return left_analog_x_value, left_analog_y_value, right_analog_x_value, right_analog_y_value

def start_controller_in_thread(controller_instance):
    """Function to start the controller listening in a separate thread"""
    controller_instance.listen(timeout=60)

if __name__ == "__main__":
    # Create controller interface
    controller = PSController(interface="/dev/input/js0")
    
    # Start controller in a separate thread
    controller_thread = threading.Thread(target=start_controller_in_thread, args=(controller,))
    controller_thread.daemon = True
    controller_thread.start()
    
    try:
        while True:
            x, y, rx, ry = controller.get_analog_stick_values()
            print(f"X: {x}, Y: {y}, RX: {rx}, RY: {ry}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting...")