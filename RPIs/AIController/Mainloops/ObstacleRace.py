import time
import numpy as np
from ai_edge_litert.interpreter import Interpreter
import multiprocessing as mp
from RPIs.Devices.Utility.Angle.angle_functions import get_angles_edges

def main_loop_obstacle_race(self):
    image_dimensions = (1024, 480)
    
    self.logger.info("Starting main loop for obstacle race...")

    IO_list = self.mp_manager.list([None, [[0.5]]])
    model_process = mp.Process(target=run_model, args=(IO_list,))
    model_process.start()
    
    with open("RPIs/AIController/model_test_features.txt", "r") as f:
        selected_feature_indexes = [int(feature) for feature in f.read().splitlines()]
    
    self.motor_controller.send_speed(0.65)
    
    while self.running:
        try:
            if not self.interpolated_lidar_data or self.block_list[0] is None or self.block_list[1] is None:
                print(f"Waiting for data: {len(self.interpolated_lidar_data)}, {self.block_list}")
                time.sleep(0.05)
                continue
            
            while IO_list[1] is None:
                time.sleep(0.005)
            
            self.servo.setAngle(self.servo.mapToServoAngle(IO_list[1][0][0]))
            # self.display.write_centered_text(f"Result: {IO_list[1][0][0]}", clear_display=True)
                
            # Prepare the lidar data
            lidar_array = np.array(self.interpolated_lidar_data)[:, :2] / np.array([360, 5000], dtype=np.float32)
            new_lidar_array = lidar_array[:, 1:]
            new_lidar_array = new_lidar_array.reshape(new_lidar_array.shape[0], -1)
            new_lidar_array = new_lidar_array[selected_feature_indexes]
            new_lidar_array = np.expand_dims(new_lidar_array, axis=0)
            
            # Prepare the blocks
            red_blocks = np.array(self.block_list[0])
            green_blocks = np.array(self.block_list[1])
            print(f"red_blocks: {red_blocks}, green_blocks: {green_blocks}")
            
            # Normalize the blocks
            new_red_blocks = []
            for red_block in red_blocks:
                red_block = np.array(red_block, dtype=np.float32)
                red_block[0] /= image_dimensions[0]
                red_block[1] /= image_dimensions[1]
                red_block[2] /= image_dimensions[0]
                red_block[3] /= image_dimensions[1]
                new_red_blocks.append(red_block)
                    
            new_green_blocks = []
            for green_block in green_blocks:
                green_block = np.array(green_block, dtype=np.float32)
                green_block[0] /= image_dimensions[0]
                green_block[1] /= image_dimensions[1]
                green_block[2] /= image_dimensions[0]
                green_block[3] /= image_dimensions[1]
                new_green_blocks.append(green_block)
            
            # Convert the blocks to numpy arrays
            red_blocks = np.array(new_red_blocks)
            green_blocks = np.array(new_green_blocks)
            
            # Add the batch and channel dimensions
            red_blocks = np.expand_dims(red_blocks, axis=0)
            red_blocks = np.expand_dims(red_blocks, axis=-1)
            green_blocks = np.expand_dims(green_blocks, axis=0)
            green_blocks = np.expand_dims(green_blocks, axis=-1)
            
            inputs = [new_lidar_array, red_blocks, green_blocks]
            
            IO_list[1] = None
            IO_list[0] = inputs
            
        
        except KeyboardInterrupt:
            self.motor_controller.send_speed(0)
            self.running = False

def run_model(shared_IO_list):
    # Load the model
    model = Interpreter(model_path='RPIs/AIController/model_test.tflite')
    model.allocate_tensors()

    # Get the input and output details
    input_details = model.get_input_details()
    print(f"Input details: {input_details}")
    output_details = model.get_output_details()

    while True:
        if shared_IO_list[0] is not None:
            lidar_data = np.array(shared_IO_list[0][0], dtype=np.float32)
            red_block = np.array(shared_IO_list[0][1], dtype=np.float32)
            green_block = np.array(shared_IO_list[0][2], dtype=np.float32)
            shared_IO_list[0] = None
            
            # Split the red and green blocks
            red_block, red_block_2 = np.split(red_block, 2, axis=1)
            green_block, green_block_2 = np.split(green_block, 2, axis=1)
            red_block = np.squeeze(red_block, axis=1)
            green_block = np.squeeze(green_block, axis=1)
            red_block_2 = np.squeeze(red_block_2, axis=1)
            green_block_2 = np.squeeze(green_block_2, axis=1)

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