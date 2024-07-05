import time
class AICU_Logger:
    def __init__(self, client):
        self.client = client

    def debug(self, message):
        self.client.send_message(f'LOG_DEBUG#{message}')

    def info(self, message):
        self.client.send_message(f'LOG_INFO#{message}')

    def warning(self, message):
        self.client.send_message(f'LOG_WARNING#{message}')

    def error(self, message):
        self.client.send_message(f'LOG_ERROR#{message}')

    def critical(self, message):
        self.client.send_message(f'LOG_CRITICAL#{message}')

    def exception(self, message):
        self.client.send_message(f'LOG_EXCEPTION#{message}')

class RemoteFunctions:
    def __init__(self, AIController):
        self.AIController = AIController
    
    def set_mode(self, mode):
        self.AIController.logger.info(f'Setting mode to {mode}')
        self.AIController.mode = mode
        
    def start(self):
        self.AIController.logger.info('Starting AIController...')
        
        self.AIController.running = True
        
        if self.AIController.mode == 'OpeningRace':
            self.AIController.main_loop_opening_race()
            
        elif self.AIController.mode == 'ObstacleRace':
            self.AIController.main_loop_obstacle_race()
            
        else:
            self.AIController.logger.error(f'Unknown mode: {self.AIController.mode}')
            self.AIController.running = False
        
    def send_good(self):
        self.AIController.client.send_message('GOOD')
    
    def receive_good(self):
        self.AIController.communicationestablisher.received_message = 'GOOD'
        
    def set_analog_stick_values(self, x, y, rx, ry):
        self.AIController.x = x
        self.AIController.y = y
        self.AIController.rx = rx
        self.AIController.ry = ry

class CommunicationEstablisher():
    def __init__(self, pi):
        self.pi = pi
        self.received_message = None


    def spam(self):
        while self.received_message == None:
            self.pi.client.send_message("How is it going?")
            time.sleep(1)