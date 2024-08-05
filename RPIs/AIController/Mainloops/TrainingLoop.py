import time
import numpy as np
import tensorflow as tf

def main_loop_training(self):
    self.logger.info("Starting main loop for training...")
    self.model = tf.keras.models.load_model('RPIs/AIController/model.h5')
    
    while self.running:
        servo_angle = self.servo.mapToServoAngle(self.x)
        self.servo.setAngle(servo_angle)
        
        if self.ry < 0.55 and self.ry > 0.45:
            motor_speed = 0.5
        else:
            motor_speed = self.ry
            
        simplified_frame = np.frombuffer(self.frame_list[1], dtype=np.uint8).reshape((120, 213, 3))
        simplified_frame = simplified_frame / 255.0
        
        lidar_data = np.array(self.interpolated_lidar_data)  # Assuming you need the first two columns (angle and distance)
        # Ensure lidar data has the correct features (angle and distance) and shape
        lidar_data = np.expand_dims(lidar_data, axis=-1)  # Adding the last dimension
        lidar_data = np.expand_dims(lidar_data, axis=0)  # Adding the batch dimension
        lidar_data = lidar_data[:, :, :2]
        
        simplified_frame = np.expand_dims(simplified_frame, axis=0)  # Adding the batch dimension

        # Combine the inputs into a list
        inputs = [lidar_data, simplified_frame]
        
        result = self.model.predict(inputs)
                
        time.sleep(0.05)