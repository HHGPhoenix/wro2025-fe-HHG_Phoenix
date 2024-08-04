import time
from uuid import uuid4
import datetime
from copy import deepcopy
import numpy as np

# from RPIs.Devices.Dummy.PSController.PSController import PSController
from RPIs.Devices.PSController.PSController import PSController


def main_loop_training(self):
    self.logger.info("Starting main loop for training...")
    ps_controller = PSController()
    ps_controller.calibrate_analog_sticks()
    
    file_uuid = str(uuid4())
    date = datetime.date.today()
    
    recording_status = False
    cross_button_pressed = False
    right_trigger_pressed = False

    start_time = time.time()

    try:
        while self.running:
            # Check for cross button press
            if ps_controller.cross == 1 and not cross_button_pressed:
                cross_button_pressed = True
                recording_status = not recording_status
                self.logger.info(f"Recording status toggled by cross: {recording_status}")
            elif ps_controller.cross == 0 and cross_button_pressed:
                cross_button_pressed = False

            # Check for right trigger press
            if ps_controller.right_trigger == 1 and not right_trigger_pressed:
                right_trigger_pressed = True
                recording_status = not recording_status  # Toggle recording status
                self.logger.info(f"Recording status toggled by right trigger: {recording_status}")
            elif ps_controller.right_trigger == 0 and right_trigger_pressed:
                right_trigger_pressed = False

            if len(self.interpolated_lidar_data) > 0:
                lidar_data = deepcopy(self.interpolated_lidar_data[-1])
                x, y, rx, ry = ps_controller.get_analog_stick_values()

                lidar_data_str = f"LIDAR_DATA#{lidar_data}"
                analog_sticks_str = f"ANALOG_STICKS#{x}#{y}#{rx}#{ry}"
                self.client.send_message(lidar_data_str)
                self.client.send_message(analog_sticks_str)
                
                # simplified_image = np.frombuffer(self.frame_list[1], dtype=np.uint8).reshape((480, 853, 3))
                # print(f"SIMPLIFIED_IMAGE#" + str(simplified_image))
                start_time = time.time()
                
                # self.client.send_message("SIMPLIFIED_IMAGE#{}".format(self.frame_list[1]))
                
                stop_time = time.time()
                # self.logger.info(f"Time taken to send simplified image: {stop_time - start_time:.2f} seconds")

                if recording_status:
                    with open(f"RPIs/DataManager/Data/lidar_data_{file_uuid}_{date}.txt", "a") as file:
                        file.write(f"{lidar_data}\n")
                        
                    with open(f"RPIs/DataManager/Data/x_values_{file_uuid}_{date}.txt", "a") as file:
                        file.write(f"{x}\n")
                        
                    # with open(f"RPIs/DataManager/Data/raw_frames{file_uuid}_{date}.txt", "a") as file:
                    #     file.write(f"{self.frame_list[0]}\n")
                        
                    # with open(f"RPIs/DataManager/Data/simplified_frames_{file_uuid}_{date}.txt", "a") as file:
                    #     file.write(f"{self.frame_list[1]}\n")
                        
            end_time = time.time()
            sleep_time = 0.1 - (end_time - start_time)

            if sleep_time > 0:
                time.sleep(sleep_time)

            start_time = time.time()

    except KeyboardInterrupt:
        pass
