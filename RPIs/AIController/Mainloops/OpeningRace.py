import time
import numpy as np
import tensorflow as tf
import multiprocessing as mp

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
            if not self.interpolated_lidar_data or self.frame_list[1] is None or self.frame_list[3] is None:
                print(f"Waiting for data: {len(self.interpolated_lidar_data)}, {self.counters}")
                time.sleep(0.05)  # Reduced sleep interval
                continue
            
            while IO_list[1] is None:
                time.sleep(0.005)  # Reduced sleep interval
            
            self.servo.setAngle(self.servo.mapToServoAngle(IO_list[1][0][0]))
                
            if USE_VISUAL_DATA:
                simplified_frame = np.frombuffer(self.frame_list[1], dtype=np.uint8).reshape((100, 213, 3)) / 255.0
                simplified_frame = np.expand_dims(simplified_frame, axis=0)
                counters = np.expand_dims([self.frame_list[3], self.frame_list[4]], axis=0)

            lidar_data = np.array([[angle / 360, distance / 5000] for angle, distance, _ in self.interpolated_lidar_data])
            # lidar_data = np.expand_dims(np.expand_dims(lidar_data, axis=-1), axis=0)
            
            lidar_data = lidar_data[:, 1:]
            new_lidar_array = lidar_data.reshape(-1)
            new_lidar_array = new_lidar_array[selected_feature_indexes]
            new_lidar_array = np.expand_dims(new_lidar_array, axis=0)
            
            
            inputs = [new_lidar_array, simplified_frame, counters] if USE_VISUAL_DATA else new_lidar_array
            
            IO_list[1] = None
            IO_list[0] = inputs
            
            self.motor_controller.send_speed(0.35)
        
        except KeyboardInterrupt:
            self.motor_controller.send_speed(0)
            self.running = False

def run_model(shared_IO_list):
    interpreter = tf.lite.Interpreter(model_path='RPIs/AIController/model.tflite')
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    while True:
        if shared_IO_list[0] is not None:
            if USE_VISUAL_DATA:
                lidar_data, simplified_frame, counters = shared_IO_list[0]
            else:
                lidar_data = shared_IO_list[0]
            shared_IO_list[0] = None
            
            lidar_data = lidar_data.astype(np.float32)
            if USE_VISUAL_DATA:
                simplified_frame = simplified_frame.astype(np.float32)
                counters = counters.astype(np.float32)
            
            if USE_VISUAL_DATA:
                interpreter.set_tensor(input_details[0]['index'], simplified_frame)
                interpreter.set_tensor(input_details[1]['index'], lidar_data)
                interpreter.set_tensor(input_details[2]['index'], counters)
            else:
                interpreter.set_tensor(input_details[0]['index'], lidar_data)
            
            start_time = time.time()
            interpreter.invoke()
            end_time = time.time()
            print(f"Time taken to run the model: {end_time - start_time} seconds")
            
            output_data = interpreter.get_tensor(output_details[0]['index'])
            print(f"Result: {output_data}")
            shared_IO_list[1] = output_data