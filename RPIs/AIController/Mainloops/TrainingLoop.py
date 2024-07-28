import time

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
        
        self.motor_controller.send_speed(motor_speed)
        
        time.sleep(0.05)