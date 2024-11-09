import time
import numpy as np
import tensorflow as tf
import multiprocessing as mp

global USE_VISUAL_DATA
USE_VISUAL_DATA = False

def main_loop_opening_race(self):
    self.logger.info("Starting main loop for opening race...")

    IO_list = self.mp_manager.list([None, None])
    mp.Process(target=run_model, args=(IO_list,)).start()
    
    while self.running:
        try:
            # run the model
            if len(self.interpolated_lidar_data) == 0 or self.frame_list[1] is None or self.frame_list[3] is None:
                print(f"Waiting for data: {len(self.interpolated_lidar_data)}, {self.counters}")
                time.sleep(0.1)
                continue
            
            while IO_list[0] is None:
                time.sleep(0.01)
            
            self.servo.setAngle(self.servo.mapToServoAngle(IO_list[1][0][0]))
                
            if USE_VISUAL_DATA:
                simplified_frame = np.frombuffer(self.frame_list[1], dtype=np.uint8).reshape((100, 213, 3))
                simplified_frame = simplified_frame / 255.0
                simplified_frame = np.expand_dims(simplified_frame, axis=0)  # Adding the batch dimension
                
                counters = np.expand_dims([self.frame_list[3], self.frame_list[4]], axis=0)

            lidar_data = []
            for angle, distance, _ in self.interpolated_lidar_data:
                lidar_data.append([angle / 360, distance / 5000])
            lidar_data = np.array(lidar_data)
            
            # Ensure lidar data has the correct features (angle and distance) and shape
            lidar_data = np.expand_dims(lidar_data, axis=-1)  # Adding the last dimension
            lidar_data = np.expand_dims(lidar_data, axis=0)  # Adding the batch dimension
            
            # Combine the inputs into a list
            if USE_VISUAL_DATA:
                inputs = [lidar_data, simplified_frame, counters]
            else:
                inputs = [lidar_data]
            
            IO_list[1] = None
            IO_list[0] = inputs
            
            motor_speed = 0.35
            # self.motor_controller.send_speed(motor_speed)
        
        except KeyboardInterrupt:
            self.motor_controller.send_speed(0)
            self.running = False


def run_model(shared_IO_list):
    # Load the TFLite model and allocate tensors
    interpreter = tf.lite.Interpreter(model_path='RPIs/AIController/model.tflite')
    interpreter.allocate_tensors()

    # Get input and output tensor details
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    while True:
        print("Running model")
        if shared_IO_list[0] is not None:
            # Extract the individual inputs
            lidar_data, simplified_frame, counters = shared_IO_list[0]
            shared_IO_list[0] = None
            
            # Convert inputs to FLOAT32
            lidar_data = lidar_data.astype(np.float32)
            simplified_frame = simplified_frame.astype(np.float32)
            counters = counters.astype(np.float32)
            
            # Set the input tensors
            interpreter.set_tensor(input_details[0]['index'], simplified_frame)
            interpreter.set_tensor(input_details[1]['index'], lidar_data)
            interpreter.set_tensor(input_details[2]['index'], counters)
            
            # Measure the time taken to run the model
            start_time = time.time()
            interpreter.invoke()
            end_time = time.time()
            print(f"Time taken to run the model: {end_time - start_time} seconds")
            
            # Get the output tensor
            output_data = interpreter.get_tensor(output_details[0]['index'])
            print(f"Result: {output_data}")
            shared_IO_list[1] = output_data
        else:
            time.sleep(0.1)