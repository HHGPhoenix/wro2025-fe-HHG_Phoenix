import time
from RPIs.Devices.Utility.Angle.angle_functions import get_angles_edges

def main_loop_obstacle_race(self):
    edge_cooldown = 0
    self.logger.info("Starting main loop for obstacle race...")
    
    while self.running:
        if len(self.interpolated_lidar_data) == 0:
            time.sleep(0.1)
            continue
        
        self.current_edge, self.relative_angle, self.last_yaw, self.running, edge_cooldown = get_angles_edges(self.shared_info_list[7], self.last_yaw, self.current_edge, True, edge_cooldown)
        
        interpolated_lidar_data = self.interpolated_lidar_data[-1]
        
        self.client.send_message(f"LIDAR_DATA#{interpolated_lidar_data}")
        
        self.client.send_message(f"BLOCKS#{self.frame_list[2] if type(self.frame_list[2]) == tuple else (0, 0, 0, 0)}#{self.frame_list[3] if type(self.frame_list[3]) == tuple else (0, 0, 0, 0)}")
        
        # print(f"red: {self.frame_list[2] if type(self.frame_list[2]) == tuple else (0, 0, 0, 0)}, green: {self.frame_list[3] if type(self.frame_list[3]) == tuple else (0, 0, 0, 0)}")
        
        time.sleep(0.1)
    
    print("Obstacle ended.")