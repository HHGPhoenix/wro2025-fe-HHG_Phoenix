def check_for_failsafe(self):
    if self.failsafe_mode == 1:
        steer_servo = False
        control_speed = False
        
        multiplier = 0.025
        steering_angle = self.servo.mapToServoAngle(0.5 - self.relative_angle * multiplier)
        self.servo.setAngle(steering_angle)
        self.motor_controller.send_speed(0.65)
        
    else:
        steer_servo = True
        control_speed = True
        
    return steer_servo, control_speed