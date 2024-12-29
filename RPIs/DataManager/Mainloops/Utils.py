def update_angles_edges(self):
    if abs(self.i2c_handler.Gyro.angle) > self.last_angle + 75:
        self.current_edge += 1
        self.last_angle = self.last_angle + 90
        
    self.relative_angle = self.i2c_handler.Gyro.angle - self.current_edge * 90
    self.client.send_message(f"RELATIVE_ANGLE#{self.relative_angle}")
    
    print(f"Current edge: {self.current_edge}, Relative angle: {self.relative_angle}")
    
    if self.current_edge >= 12:
        self.running = False