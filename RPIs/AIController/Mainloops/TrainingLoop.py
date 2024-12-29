import time

def main_loop_training(self):
    self.logger.info("Starting main loop for training...")
    
    while self.running:
        start_time = time.time()
        servo_angle = self.servo.mapToServoAngle(self.x)
        self.servo.setAngle(servo_angle)
        
        if self.ry < 0.55 and self.ry > 0.45:
            motor_speed = 0.5
        else:
            motor_speed = self.ry
            
        print(f"failsafe_mode: {self.failsafe_mode}")
        if self.failsafe_mode == 1:
            motor_speed = 0.65
        
        self.motor_controller.send_speed(motor_speed)
        stop_time = time.time()
        
        time.sleep(max(0, 0.05 - (stop_time - start_time)))
        # print(f"total time: {stop_time - start_time}")