import time
from RPIs.Devices.Utility.Angle.angle_functions import get_angles_edges

def main_loop_opening_race(self):
    self.logger.info("Starting main loop for opening race...")
    
    while self.running:
        if len(self.interpolated_lidar_data) == 0:
            time.sleep(0.1)
            continue
        
        self.current_edge, self.relative_angle, self.last_yaw, self.running = get_angles_edges(self.shared_info_list[7], self.last_yaw, self.current_edge, True)
        
        interpolated_lidar_data = self.interpolated_lidar_data[-1]
        
        self.client.send_message(f"LIDAR_DATA#{interpolated_lidar_data}")
        
        time.sleep(0.1)
    
    print("Opening ended.")