import time

def main_loop_opening_race(self):
    self.logger.info("Starting main loop for opening race...")
    
    while self.running:
        if len(self.interpolated_lidar_data) == 0:
            time.sleep(0.1)
            continue
        
        interpolated_lidar_data = self.interpolated_lidar_data[-1]
        
        self.client.send_message(f"LIDAR_DATA#{interpolated_lidar_data}")
        
        time.sleep(0.1)
    
    print("Opening ended.")