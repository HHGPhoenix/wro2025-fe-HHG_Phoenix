import time

# from RPIs.Devices.Dummy.PSController.PSController import PSController
from RPIs.Devices.PSController.PSController import PSController

from uuid import uuid4
import datetime
from copy import deepcopy

def main_loop_training(self):
    self.logger.info("Starting main loop for training...")
    ps_controller = PSController()
    ps_controller.calibrate_analog_sticks()
    
    file_uuid = str(uuid4())
    date = datetime.date.today()
    
    recording_status = False
    cross_pressed = False

    start_time = time.time()

    try:
    
        while self.running:
            if ps_controller.cross == 1 and not cross_pressed:
                cross_pressed = True
                recording_status = not recording_status
                self.logger.info(f"Recording status: {recording_status}")
            elif ps_controller.cross == 0:
                cross_pressed = False
                # self.logger.info("Cross button released")
            
            if len(self.interpolated_lidar_data) > 0:
                lidar_data = deepcopy(self.interpolated_lidar_data[-1])
                x, y, rx, ry = ps_controller.get_analog_stick_values()

                lidar_data_str = f"LIDAR_DATA#{lidar_data}"
                analog_sticks_str = f"ANALOG_STICKS#{x}#{y}#{rx}#{ry}"

                # print(f"Analogdatastr: {analog_sticks_str}")
                
                self.client.send_message(lidar_data_str)
                self.client.send_message(analog_sticks_str)
                
                if recording_status:
                    with open(f"RPIs/DataManager/Data/lidar_data_{file_uuid}_{date}.txt", "a") as file:
                        file.write(f"{lidar_data}\n")
                        
                    with open(f"RPIs/DataManager/Data/x_values_{file_uuid}_{date}.txt", "a") as file:
                        file.write(f"{x}\n")
            
            end_time = time.time()
            # print(f"Loop iteration time: {end_time - start_time} seconds")

            sleep_time = 0.1 - (end_time - start_time)

            if sleep_time > 0:
                time.sleep(sleep_time)

            start_time = time.time()

    except KeyboardInterrupt:
        pass