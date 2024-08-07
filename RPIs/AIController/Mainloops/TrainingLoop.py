import time
import numpy as np
import tensorflow as tf
import multiprocessing as mp
import cv2

def main_loop_training(self):
    self.logger.info("Starting main loop for training...")
    
    IO_list = self.mp_manager.list([None, None])
    mp.Process(target=run_model, args=(IO_list,)).start()
    
    while self.running:
        start_time = time.time()
        # servo_angle = self.servo.mapToServoAngle(self.x)
        # self.servo.setAngle(servo_angle)
        
        if self.ry < 0.55 and self.ry > 0.45:
            motor_speed = 0.5
        else:
            motor_speed = self.ry
            
        print(f"IO_list[1]: {IO_list[1]}")
        if IO_list[1] is not None:
            servo_angle = self.servo.mapToServoAngle(IO_list[1][0][0])
            self.servo.setAngle(servo_angle)
        
        simplified_frame = np.frombuffer(self.frame_list[1], dtype=np.uint8).reshape((110, 213, 3))
        
        lidar_data = []
        interpolated_lidar_data = np.array(self.interpolated_lidar_data)
        print(f"interpolated_lidar_data: {interpolated_lidar_data.shape}")
        for angle, distance, _ in self.interpolated_lidar_data:
            lidar_data.append([angle / 360, distance / 4000])
        lidar_data = np.array(lidar_data)
        
        # Ensure lidar data has the correct features (angle and distance) and shape
        lidar_data = np.expand_dims(lidar_data, axis=-1)  # Adding the last dimension
        lidar_data = np.expand_dims(lidar_data, axis=0)  # Adding the batch dimension
        # lidar_data = lidar_data[:, :, :2]
        
        # simplified_frame = np.array(cv2.cvtColor(simplified_frame, cv2.COLOR_BGR2GRAY))
        # simplified_frame = np.expand_dims(simplified_frame, axis=-1)  # Adding the last dimension
        simplified_frame = simplified_frame / 255.0
        simplified_frame = np.expand_dims(simplified_frame, axis=0)  # Adding the batch dimension
        
        counters = np.expand_dims(self.counters, axis=0)

        # Combine the inputs into a list
        inputs = [lidar_data, simplified_frame, counters]
        
        IO_list[0] = inputs
        self.motor_controller.send_speed(motor_speed)
        stop_time = time.time()
        
                
        time.sleep(max(0, 0.05 - (stop_time - start_time)))
        # print(f"total time: {stop_time - start_time}")
        
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