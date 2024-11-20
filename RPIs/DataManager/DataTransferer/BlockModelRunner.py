import tensorflow as tf
import cv2
import numpy as np
import sys
import time

class BlockModelRunner:
    def __init__(self):
        self.model = tf.lite.Interpreter(model_path='RPIs/DataManager/block_model.tflite')
        self.model.allocate_tensors()
        self.input_details = self.model.get_input_details()
        self.output_details = self.model.get_output_details()
        
    def run_model(self):
        # print("\n")
        # time.sleep(1)
        while True:
            # Read binary data from standard input
            # print("Waiting for input data...")
            while len(sys.stdin.buffer.peek()) < 100 * 213 * 3:
                print(f"Waiting for input data... {len(sys.stdin.buffer.peek())}")
                time.sleep(0.1)  # Add a delay to avoid busy waiting
            
            print("Reading input data...")
            
            model_input = sys.stdin.buffer.read(100 * 213 * 3)
            print(f"Received input data: {model_input}")            # while not model_input:
            #     print("No input data received. Waiting for data...")
            #     pass
            # if not model_input:
            #     raise 
            #     break
            
            # raw_frame = np.frombuffer(model_input, dtype=np.uint8).reshape((100, 213, 3)) / 255.0
            # raw_frame = np.expand_dims(raw_frame, axis=0).astype(np.float32)
            
            # self.model.set_tensor(self.input_details[0]['index'], raw_frame)
            # self.model.invoke()
            
            # output = self.model.get_tensor(self.output_details[0]['index'])
            # output_2 = self.model.get_tensor(self.output_details[1]['index'])
            
            output = "output"
            output_2 = "output_2"
            
            print(f"Output: {output}, {output_2}")  

if __name__ == "__main__":
    runner = BlockModelRunner()
    runner.run_model()