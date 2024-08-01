import time
import numpy as np

def main_loop_training(self):
    self.logger.info("Starting main loop for training...")
    
    while self.running:
        servo_angle = self.servo.mapToServoAngle(self.x)
        # print(f"servo_angle: {servo_angle:.2f}", end=' ')
        self.servo.setAngle(servo_angle)
        
        if self.ry < 0.55 and self.ry > 0.45:
            motor_speed = 0.5
        else:
            motor_speed = self.ry
        
        # self.motor_controller.send_speed(0.5)
        
        # Assuming self.simplified_image is a string representation of a numpy array
        if self.simplified_image:
            # Convert the string to a numpy
            simplified_image_str = self.simplified_image
            
            # Convert the string back to a numpy array
            simplified_image = np.frombuffer(simplified_image_str, dtype=np.uint8).reshape((480, 853, 3))
            
            # Print the shape of the numpy array
            print(simplified_image.shape)
        
        time.sleep(0.05)