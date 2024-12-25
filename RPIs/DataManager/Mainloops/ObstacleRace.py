import time

def main_loop_obstacle_race(self):
    self.logger.info("Starting main loop for obstacle race...")
    
    while self.running:
        if len(self.interpolated_lidar_data) == 0:
            time.sleep(0.1)
            continue
        
        interpolated_lidar_data = self.interpolated_lidar_data[-1]
        
        self.client.send_message(f"LIDAR_DATA#{interpolated_lidar_data}")
        
        self.client.send_message(f"BLOCKS#{self.frame_list[2] if type(self.frame_list[2]) == tuple else (0, 0, 0, 0)}#{self.frame_list[3] if type(self.frame_list[3]) == tuple else (0, 0, 0, 0)}")
        
        time.sleep(0.1)
    
    print("Obstacle ended.")