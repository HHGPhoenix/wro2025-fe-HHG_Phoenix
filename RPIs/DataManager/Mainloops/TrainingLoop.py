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
    saved_after_recording = False

    start_time = time.time()

    x_values = []
    lidar_arrays = []
    raw_frames = []
    simplified_frames = []
    counters = []

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
                # print(lidar_data)
                x, y, rx, ry = ps_controller.get_analog_stick_values()

                lidar_data_str = f"LIDAR_DATA#{lidar_data}"
                analog_sticks_str = f"ANALOG_STICKS#{x}#{y}#{rx}#{ry}"
                counters_str = f"COUNTERS#{self.frame_list[3]}#{self.frame_list[4]}"
                
                self.client.send_message(lidar_data_str)
                self.client.send_message(analog_sticks_str)
                self.client.send_message(counters_str)

                if recording_status:
                    saved_after_recording = False
                    
                    x_values.append(x)
                    lidar_arrays.append(lidar_data)
                    
                    raw_frame = np.frombuffer(self.frame_list[0], dtype=np.uint8).reshape((100, 213, 3))
                    raw_frames.append(raw_frame)

                    simplified_frame = np.frombuffer(self.frame_list[1], dtype=np.uint8).reshape((100, 213, 3))
                    simplified_frames.append(simplified_frame)
                    
                    counters.append([self.frame_list[3], self.frame_list[4]])
                
                elif not saved_after_recording:
                    np.savez(f"RPIs/DataManager/Data/run_data_{file_uuid}_{date}.npz", controller_data=np.array(x_values), counters = np.array(counters),
                             lidar_data=np.array(lidar_arrays), raw_frames=np.array(raw_frames), simplified_frames=np.array(simplified_frames))
                    saved_after_recording = True
                    
            end_time = time.time()
            sleep_time = 0.1 - (end_time - start_time)

            if sleep_time > 0:
                time.sleep(sleep_time)

            start_time = time.time()

    except KeyboardInterrupt:
        pass
    
    finally:
        np.savez(f"RPIs/DataManager/Data/run_data_{file_uuid}_{date}.npz", controller_data=np.array(x_values), counters = np.array(counters),
                 lidar_data=np.array(lidar_arrays), raw_frames=np.array(raw_frames), simplified_frames=np.array(simplified_frames))

