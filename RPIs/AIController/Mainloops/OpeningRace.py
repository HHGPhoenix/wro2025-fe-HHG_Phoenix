import time
import tensorflow as tf

def main_loop_opening_race(self):
    import pandas as pd
    self.logger.info("Starting main loop for opening race...")
    
    self.model = tf.keras.models.load_model('RPIs/AIController/model.h5')
    
    while self.running:
        # run the model
        if len(self.interpolated_lidar_data) == 0:
            time.sleep(0.1)
            continue
        
        lidar_data = []
        
        # print(f"len(self.lidar_data): {len(self.lidar_data)}, self.lidar_data[-1]: {self.lidar_data}")
        
        df = pd.DataFrame(self.interpolated_lidar_data, columns=["angle", "distance", "intensity"])
        
        df = df.drop(columns=["intensity"])

        df_interpolated_list = df.values.tolist()  
        
        lidar_data.append(df_interpolated_list)
        
        # print(f"lidar_data: {lidar_data}")
        
        prediction = self.model.predict(lidar_data)
        
        print(f"prediction: {prediction}")
        
        servo_angle = self.servo.mapToServoAngle(prediction[0][0])
        self.servo.setAngle(servo_angle)
        
        motor_speed = 0.3
        
        self.motor_controller.send_speed(motor_speed)