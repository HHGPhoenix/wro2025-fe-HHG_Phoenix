import time
import numpy as np
import tensorflow as tf
import multiprocessing as mp

def main_loop_training(self):
    self.logger.info("Starting main loop for training...")
    
    IO_list = self.mp_manager.list([None, None])
    mp.Process(target=run_model, args=(IO_list,)).start()
    
    while self.running:
        start_time = time.time()
        servo_angle = self.servo.mapToServoAngle(self.x)
        self.servo.setAngle(servo_angle)
        
        if self.ry < 0.55 and self.ry > 0.45:
            motor_speed = 0.5
        else:
            motor_speed = self.ry
            
        print(f"IO_list[1]: {IO_list[1]}")
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
        
        IO_list[0] = inputs
        stop_time = time.time()
                
        time.sleep(max(0, 0.1 - (stop_time - start_time)))
        print(f"total time: {stop_time - start_time}")
        
def run_model(shared_IO_list):
    model = tf.keras.models.load_model('RPIs/AIController/model.h5')
    while True:
        print("Running model")
        if shared_IO_list[0] is not None:
            result = model.predict(shared_IO_list[0])
            print(f"Result: {result}")
        else:
            time.sleep(0.1)