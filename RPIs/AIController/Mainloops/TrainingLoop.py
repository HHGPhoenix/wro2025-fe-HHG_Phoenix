import time
from RPIs.AIController.Mainloops.Utils import check_for_failsafe

def main_loop_training(self):
    try:
        self.logger.info("Starting main loop for training...")
        steer_servo = True
        control_speed = True
        
        while self.running:
            try:
                start_time = time.time()
                # steer_servo, control_speed = check_for_failsafe(self)
                
                if steer_servo:
                    servo_angle = self.servo.mapToServoAngle(self.x)
                    self.servo.setAngle(servo_angle)
                    
                if control_speed:
                    if self.ry < 0.55 and self.ry > 0.45:
                        motor_speed = 0.5
                    else:
                        motor_speed = self.ry
                    self.motor_controller.send_speed(motor_speed)

                stop_time = time.time()
                time.sleep(max(0, 0.05 - (stop_time - start_time)))
                # print(f"total time: {stop_time - start_time}")
            finally:
                self.motor_controller.send_speed(0.5)
    finally:
        self.motor_controller.send_speed(0.5)