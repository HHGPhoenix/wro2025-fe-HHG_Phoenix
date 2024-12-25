import time
import numpy as np
import tensorflow as tf
import multiprocessing as mp

global USE_VISUAL_DATA
USE_VISUAL_DATA = False

def main_loop_obstacle_race(self):
    self.logger.info("Starting main loop for obstacle race...")

    IO_list = self.mp_manager.list([None, [[0.5]]])
    model_process = mp.Process(target=run_model, args=(IO_list,))
    model_process.start()
    
    with open("RPIs/AIController/model_features.txt", "r") as f:
        selected_feature_indexes = [int(feature) for feature in f.read().splitlines()]
    
    while self.running:
        try:
            if not self.interpolated_lidar_data or self.block_list[0] is None or self.block_list[1] is None:
                print(f"Waiting for data: {len(self.interpolated_lidar_data)}, {self.block_list}")
                time.sleep(0.05)
                continue
            
            while IO_list[1] is None:
                time.sleep(0.005)
            
            self.servo.setAngle(self.servo.mapToServoAngle(IO_list[1][0][0]))
                
            lidar_data = np.array([[angle / 360, distance / 5000] for angle, distance, _ in self.interpolated_lidar_data])
            new_lidar_array = lidar_data.reshape(-1)
            new_lidar_array = new_lidar_array[selected_feature_indexes]
            

            
            new_lidar_array = np.expand_dims(new_lidar_array, axis=0)
            new_lidar_array = np.expand_dims(new_lidar_array, axis=-1)
            
            red_block = np.array(self.block_list[0])
            green_block = np.array(self.block_list[1])
            
            red_block = red_block / np.array([213, 100, 213, 100], dtype=np.float32)
            green_block = green_block / np.array([213, 100, 213, 100], dtype=np.float32)
            
            red_block = np.expand_dims(red_block, axis=0)
            red_block = np.expand_dims(red_block, axis=-1)
            
            green_block = np.expand_dims(green_block, axis=0)
            green_block = np.expand_dims(green_block, axis=-1)
            
            inputs = [new_lidar_array, red_block, green_block]
            
            IO_list[1] = None
            IO_list[0] = inputs
            
            self.motor_controller.send_speed(0.5)
        
        except KeyboardInterrupt:
            self.motor_controller.send_speed(0)
            self.running = False

def run_model(shared_IO_list):
    interpreter = tf.lite.Interpreter(model_path='RPIs/AIController/model.tflite')
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    print(f"Input details: {input_details}")
    output_details = interpreter.get_output_details()

    while True:
        if shared_IO_list[0] is not None:
            lidar_data, red_block, green_block = shared_IO_list[0]
            lidar_data = np.array(lidar_data)
            red_block = np.array(red_block)
            green_block = np.array(green_block)
            shared_IO_list[0] = None
            
            lidar_data = lidar_data.astype(np.float32)
            red_block = red_block.astype(np.float32)
            green_block = green_block.astype(np.float32)
            
            # Set the tensors
            interpreter.set_tensor(input_details[0]['index'], lidar_data)
            interpreter.set_tensor(input_details[1]['index'], red_block)
            interpreter.set_tensor(input_details[2]['index'], green_block)
            
            start_time = time.time()
            interpreter.invoke()
            end_time = time.time()
            print(f"Time taken to run the model: {end_time - start_time} seconds")
            
            output_data = interpreter.get_tensor(output_details[0]['index'])
            print(f"Result: {output_data}")
            shared_IO_list[1] = output_data