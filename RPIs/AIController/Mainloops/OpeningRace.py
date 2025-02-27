import time
import numpy as np
import tensorflow as tf
import multiprocessing as mp
from RPIs.Devices.Utility.Angle.angle_functions import get_angles_edges

global USE_VISUAL_DATA
USE_VISUAL_DATA = False

def main_loop_opening_race(self):
    self.logger.info("Starting main loop for opening race...")

    IO_list = self.mp_manager.list([None, [[0.5]]])
    model_process = mp.Process(target=run_model, args=(IO_list,))
    model_process.start()
    
    with open("RPIs/AIController/model_features.txt", "r") as f:
        selected_feature_indexes = [int(feature) for feature in f.read().splitlines()]
    
    while self.running:
        try:
            if not self.interpolated_lidar_data:
                print(f"Waiting for data: {len(self.interpolated_lidar_data)}")
                time.sleep(0.05)  # Reduced sleep interval
                continue
            
            self.current_edge, self.relative_angle, self.last_yaw = get_angles_edges(self.motor_controller.yaw, self.last_yaw, self.current_edge)
            
            while IO_list[1] is None:
                time.sleep(0.005)  # Reduced sleep interval
            
            self.servo.setAngle(self.servo.mapToServoAngle(IO_list[1][0][0]))

            lidar_array = np.array(self.interpolated_lidar_data)[:, :2] / np.array([360, 5000], dtype=np.float32)
            new_lidar_array = lidar_array[:, 1:]
            new_lidar_array = new_lidar_array.reshape(new_lidar_array.shape[0], -1)
            new_lidar_array = new_lidar_array[selected_feature_indexes]
            
            new_lidar_array = np.expand_dims(new_lidar_array, axis=0).astype(np.float32)
            
            print(f"New lidar array: {new_lidar_array.shape}")
            
            inputs = new_lidar_array
            
            IO_list[1] = None
            IO_list[0] = inputs
            
            self.motor_controller.send_speed(0.75)
        
        except KeyboardInterrupt:
            self.motor_controller.send_speed(0.5)
            self.running = False

def run_model(shared_IO_list):
    interpreter = tf.lite.Interpreter(model_path='RPIs/AIController/model.tflite')
    interpreter.allocate_tensors()
    
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    while True:
        if shared_IO_list[0] is not None:
            lidar_data = shared_IO_list[0][0]
            shared_IO_list[0] = None
            
            lidar_data = np.array(lidar_data).astype(np.float32)
            
            print(f"Input data: {lidar_data.shape}")
            
            # Reshape lidar_data to match the expected input dimensions
            expected_shape = input_details[0]['shape']
            lidar_data = lidar_data.reshape(expected_shape)
            
            interpreter.set_tensor(input_details[0]['index'], lidar_data)
            
            start_time = time.time()
            interpreter.invoke()
            end_time = time.time()
            print(f"Time taken to run the model: {end_time - start_time} seconds")
            
            output_data = interpreter.get_tensor(output_details[0]['index'])
            print(f"Result: {output_data}")
            shared_IO_list[1] = output_data