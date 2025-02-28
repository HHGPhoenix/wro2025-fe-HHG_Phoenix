import time

class Failsafe:
    def __init__(self, data_manager):
        self.failsafe_time = 0
        self.data_manager = data_manager
    
    def mainloop(self):
        while not self.data_manager.running:
            time.sleep(0.1)
        
        while self.data_manager.running:
            red_block = self.data_manager.frame_list[2][0]
            green_block = self.data_manager.frame_list[3][0]
            # if red_block == None:
            #     red_block = (0, 0, 0, 0)
            # if green_block == None:
            #     green_block = (0, 0, 0, 0)
            
            red_block_area = (red_block[2] - red_block[0]) * (red_block[3] - red_block[1])
            green_block_area = (green_block[2] - green_block[0]) * (green_block[3] - green_block[1])
            
            if ((red_block[2] >= 170 and red_block_area >= 1000) or red_block[2] >= 190) or ((green_block[0] <= 43 and green_block_area >= 1000) or green_block[0] <= 23):
                self.data_manager.client.send_message("FAILSAFE#1")
                # self.data_manager.logger.info("Failsafe activated.")
                self.failsafe_time = time.time()
            
            elif time.time() - self.failsafe_time > 0.5:
                self.data_manager.client.send_message("FAILSAFE#0")
                # self.data_manager.logger.info("Failsafe deactivated.")
                
            time.sleep(0.1)