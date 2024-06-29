import time
import threading
from RPIs.RPI_COM.messageReceiverServer import MessageReceiver
from RPIs.RPI_COM.sendMessage import Messenger
from RPIs.RPI_Logging.Logger import Logger
from RPIs.DataManager.DataManagerLib import RemoteFunctions, CommunicationEstablisher
from RPIs.Devices.Camera.CameraManager import Camera
from RPIs.Devices.LIDAR.LIDARManager import LidarSensor

class DataManager:
    def __init__(self):
        try:
            print("Starting DataManager...")
            self.receiver = None
            self.client = None
            self.logger = None
            self.cam = None
            self.lidar = None
            self.mode = None
            self.communicationestablisher = CommunicationEstablisher(self)
            
            self.start_comm()

            self.logger.info("DataManager started.")
            
            self.mode = self.choose_mode()
            
            self.cam, self.lidar = self.initialize_components()

            self.communicationestablisher.spam()

            for i in range(3):
                time.sleep(1)
                self.logger.info(f"Waiting ... {i}")
                
        except:
            self.receiver.server_socket.close()

    def start_comm(self):
        # Start the server

        self.remotefunctions = RemoteFunctions(self)

        self.receiver = MessageReceiver(r'RPIs/RPI_COM/Mappings/DataManagerMappings.json', 11111, handler_instance=self.remotefunctions, ip='192.168.1.3')
        threading.Thread(target=self.receiver.start_server, daemon=True).start()

        self.client = Messenger('192.168.1.2', 22222)
        logger_obj = Logger()
        self.logger = logger_obj.setup_log()
        
    def initialize_components(self):
        cam = Camera()
        
        lidar = LidarSensor("/dev/ttyUSB0")
        lidar.reset_sensor()
        lidar.start_sensor()
        lidar_thread = threading.Thread(target=lidar.read_data, daemon=True)
        lidar_thread.start()

        self.logger.info("Camera and LIDAR initialized.")
        
        return cam, lidar
    
    def choose_mode(self):
        with open ("RPIs/DataManager/mode.txt", "r") as file:
            mode = file.read().strip()
            
        self.client.send_message(f"MODE#{mode}")
        
        return mode
    
    def start(self):
        self.logger.info('Starting AIController...')
        self.client.send_message('START')
        
        self.running = True
        
        if self.mode == 'OpeningRace':
            self.main_loop_opening_race()
            
        elif self.mode == 'ObstacleRace':
            self.main_loop_obstacle_race()
            
        else:
            self.logger.error(f'Unknown mode: {self.mode}')
            self.running = False
    
    def main_loop_opening_race(self):
        self.logger.info("Starting main loop for opening race...")
        
    def main_loop_obstacle_race(self):
        self.logger.info("Starting main loop for obstacle race...")
        
if __name__ == "__main__":
    try:
        data_manager = DataManager()
        data_manager.start()
    finally:
        data_manager.lidar.stop_sensor()
        data_manager.receiver.server_socket.close()
        data_manager.logger.info("DataManager stopped.")
        data_manager.logger.info("Exiting...")