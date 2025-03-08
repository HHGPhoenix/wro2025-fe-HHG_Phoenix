import time

def main_loop_training(self):
    try:
        self.logger.info("Starting main loop for training...")
        steer_servo = True
        control_speed = True
        speed_sent = False
        
        while self.running:
            try:
                start_time = time.time()
                
                if steer_servo:
                    servo_angle = self.servo.mapToServoAngle(self.x)
                    self.servo.setAngle(servo_angle)
                    
                if control_speed:
                    if self.ry < 0.55 and self.ry > 0.45:
                        motor_speed = 0.5
                        if speed_sent:
                            self.motor_controller.send_speed(motor_speed)
                            speed_sent = False
                        
                    else:
                        motor_speed = 0.70
                        if not speed_sent:
                            self.motor_controller.send_speed(motor_speed)
                            speed_sent = True
                        
                        # motor_speed = self.ry
                        # self.motor_controller.send_speed(motor_speed)
                        

                stop_time = time.time()
                time.sleep(max(0, 0.05 - (stop_time - start_time)))
                # print(f"total time: {stop_time - start_time}")
            except:
                self.motor_controller.send_speed(0.5)
    finally:
        self.motor_controller.send_speed(0.5)