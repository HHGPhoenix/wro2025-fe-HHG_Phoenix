import time
from RPIs.Devices.Utility.Angle.angle_functions import get_angles_edges

def main_loop_opening_race(self):
    running_change = True
    running_change_time = 0
    edge_cooldown = 0
    self.logger.info("Starting main loop for opening race...")
    
    while self.running:
        start_time = time.time()
        if len(self.interpolated_lidar_data) == 0:
            time.sleep(0.1)
            continue
        
        self.current_edge, self.relative_angle, self.last_yaw, running_change, edge_cooldown = get_angles_edges(self.shared_info_list[7], self.last_yaw, self.current_edge, True, edge_cooldown)
        
        if running_change == False:
            if running_change_time == 0:
                running_change_time = time.time()
                
            if time.time() - running_change_time >= 2.5:
                self.running = False
        
        interpolated_lidar_data = self.interpolated_lidar_data[-1]
        
        self.client.send_message(f"LIDAR_DATA#{interpolated_lidar_data}")
        
        end_time = time.time()
        time.sleep(max(0, 0.1 - (end_time - start_time)))

    print("Opening ended.")