import time
import numpy as np
import tensorflow as tf
import multiprocessing as mp
from RPIs.Devices.Utility.Angle.angle_functions import get_angles_edges

global USE_VISUAL_DATA
USE_VISUAL_DATA = False

def main_loop_obstacle_race(self):
    self.logger.info("Starting main loop for obstacle race...")

    IO_list = self.mp_manager.list([None, [[0.5]]])
    model_process = mp.Process(target=run_model, args=(IO_list,))
    model_process.start()
    
    with open("RPIs/AIController/model_features.txt", "r") as f:
        selected_feature_indexes = [int(feature) for feature in f.read().splitlines()]
    
    self.motor_controller.send_speed(0.7)
    
    while self.running:
        try:
            if not self.interpolated_lidar_data or self.block_list[0] is None or self.block_list[1] is None:
                print(f"Waiting for data: {len(self.interpolated_lidar_data)}, {self.block_list}")
                time.sleep(0.05)
                continue
            
            while IO_list[1] is None:
                time.sleep(0.005)
            
            self.servo.setAngle(self.servo.mapToServoAngle(IO_list[1][0][0]))
                
            lidar_array = np.array(self.interpolated_lidar_data)[:, :2] / np.array([360, 5000], dtype=np.float32)
            new_lidar_array = lidar_array[:, 1:]
            new_lidar_array = new_lidar_array.reshape(new_lidar_array.shape[0], -1)
            new_lidar_array = new_lidar_array[selected_feature_indexes]
            
            new_lidar_array = np.expand_dims(new_lidar_array, axis=0)
            # new_lidar_array = np.expand_dims(new_lidar_array, axis=-1)
            
            red_blocks = np.array(self.block_list[0])
            green_blocks = np.array(self.block_list[1])
            
            
            print(f"red_blocks: {red_blocks}, green_blocks: {green_blocks}")
            
            new_red_blocks = []
            for red_block in red_blocks:
                red_block = np.array(red_block, dtype=np.float32)
                red_block[0] /= 213
                red_block[1] /= 100
                red_block[2] /= 213
                red_block[3] /= 100
                new_red_blocks.append(red_block)
                    
            new_green_blocks = []
            for green_block in green_blocks:
                green_block = np.array(green_block, dtype=np.float32)
                green_block[0] /= 213
                green_block[1] /= 100
                green_block[2] /= 213
                green_block[3] /= 100
                new_green_blocks.append(green_block)
            
            red_blocks = np.array(new_red_blocks)
            green_blocks = np.array(new_green_blocks)
            
            print(f"red_blocks: {red_blocks}, green_blocks: {green_blocks}")
            
            red_blocks = np.expand_dims(red_blocks, axis=0)
            red_blocks = np.expand_dims(red_blocks, axis=-1)
            green_blocks = np.expand_dims(green_blocks, axis=0)
            green_blocks = np.expand_dims(green_blocks, axis=-1)
            
            print(f"red_blocks: {red_blocks}, green_blocks: {green_blocks}")
            
            inputs = [new_lidar_array, red_blocks, green_blocks]
            
            IO_list[1] = None
            IO_list[0] = inputs
            
        
        except KeyboardInterrupt:
            self.motor_controller.send_speed(0)
            self.running = False

def run_model(shared_IO_list):
    model = tf.lite.Interpreter(model_path='RPIs/AIController/model.tflite')
    model.allocate_tensors()

    input_details = model.get_input_details()
    print(f"Input details: {input_details}")
    output_details = model.get_output_details()

    while True:
        if shared_IO_list[0] is not None:
            lidar_data, red_block, green_block = shared_IO_list[0]
            lidar_data = np.array(lidar_data, dtype=np.float32)
            red_block = np.array(red_block, dtype=np.float32)
            green_block = np.array(green_block, dtype=np.float32)
            shared_IO_list[0] = None
            
            red_block, red_block_2 = np.split(red_block, 2, axis=1)
            green_block, green_block_2 = np.split(green_block, 2, axis=1)
            
            red_block = np.squeeze(red_block, axis=1)
            green_block = np.squeeze(green_block, axis=1)
            red_block_2 = np.squeeze(red_block_2, axis=1)
            green_block_2 = np.squeeze(green_block_2, axis=1)
            
            
            # print(f"red_block: {red_block.flatten()}, green_block: {green_block.flatten()}")

            # Set the tensors
            model.set_tensor(input_details[0]['index'], lidar_data)
            model.set_tensor(input_details[1]['index'], red_block)
            model.set_tensor(input_details[2]['index'], green_block)
            model.set_tensor(input_details[3]['index'], red_block_2)
            model.set_tensor(input_details[4]['index'], green_block_2)
            
            start_time = time.time()
            model.invoke()
            end_time = time.time()
            print(f"Time taken to run the model: {end_time - start_time} seconds")
            
            output_data = model.get_tensor(output_details[0]['index'])
            print(f"Result: {output_data}")
            shared_IO_list[1] = output_data