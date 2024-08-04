import time
import numpy as np
import tensorflow as tf

def main_loop_training(self):
    self.logger.info("Starting main loop for training...")
    self.model = tf.keras.models.load_model('RPIs/AIController/model.h5')
    
    while self.running:
        servo_angle = self.servo.mapToServoAngle(self.x)
        # print(f"servo_angle: {servo_angle:.2f}", end=' ')
        self.servo.setAngle(servo_angle)
        
        if self.ry < 0.55 and self.ry > 0.45:
            motor_speed = 0.5
        else:
            motor_speed = self.ry
            
        try:
            simplified_frame = np.frombuffer(self.frame_list[1], dtype=np.uint8).reshape((360, 640, 3))
            simplified_frame = simplified_frame / 255.0
                
            result = self.model.predict(np.array(self.interpolated_lidar_data), simplified_frame)	
        except Exception as e:
            self.logger.error(f"Error: {e}")
            continue
                
        # self.motor_controller.send_speed(motor_speed)
        
        time.sleep(0.05)