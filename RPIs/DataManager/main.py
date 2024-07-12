import time
import threading
from RPIs.RPI_COM.messageReceiverServer import MessageReceiver
from RPIs.RPI_COM.sendMessage import Messenger
from RPIs.RPI_Logging.Logger import Logger, LoggerDatamanager
from RPIs.DataManager.DataManagerLib import RemoteFunctions, CommunicationEstablisher

from RPIs.Devices.Dummy.Camera.CameraManager import Camera
from RPIs.Devices.LIDAR.LIDARManager import LidarSensor

from RPIs.DataManager.DataTransferer.DataTransferer import DataTransferer
from RPIs.WebServer.WebServer import WebServer

from RPIs.DataManager.Mainloops.TrainingLoop import main_loop_training

import multiprocessing as mp
import queue
import os

def set_nice_priority(nice_value):
    os.nice(nice_value)

def target_with_nice_priority(target, nice_value):
    def wrapper(*args, **kwargs):
        set_nice_priority(nice_value)
        target(*args, **kwargs)
    return wrapper

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
            self.data_transferer = None

            self.running = False

            self.mp_manager = mp.Manager()
            self.frame_list = self.mp_manager.list([None, None, None])
            self.interpolated_lidar_data = self.mp_manager.list([None])
            self.lidar_data_list = self.mp_manager.list()
            
            self.communicationestablisher = CommunicationEstablisher(self)
            
            self.start_comm()

            self.logger.info("DataManager started.")
            
            self.mode = self.choose_mode()
            
            self.cam, self.lidar, self.data_transferer = self.initialize_components()

            self.communicationestablisher.spam()
            
            self.logger.info("DataManager initialized.")
            
            self.client.send_message(f"MODE#{self.mode}")
            
            for i in range(3):
                time.sleep(1)
                self.logger.info(f"Waiting ... {i}")
                
        except:
            self.receiver.server_socket.close()

    def start_comm(self):
        logger_obj = Logger()
        self.logger_obj = logger_obj.setup_log()
        self.logger = LoggerDatamanager(self.logger_obj)
        
        self.remotefunctions = RemoteFunctions(self)
        self.receiver = MessageReceiver(r'RPIs/RPI_COM/Mappings/DataManagerMappings.json', 11111, handler_instance=self.remotefunctions, ip='192.168.1.3')
        threading.Thread(target=self.receiver.start_server, daemon=True).start()

        self.client = Messenger('192.168.1.2', 22222)
        
    def initialize_components(self):
        cam = Camera()
        
        self.logger.info("Initializing LIDAR sensor...")
        
        lidar = LidarSensor("/dev/ttyUSB0", self.lidar_data_list)
        lidar.reset_sensor()
        lidar.start_sensor()
        lidar_thread = mp.Process(target=target_with_nice_priority(lidar.read_data, -10), daemon=True)
        lidar_thread.start()
        self.logger.info("Camera and LIDAR initialized.")
        
        data_transferer = DataTransferer(cam, lidar, self.frame_list, self.lidar_data_list, self.interpolated_lidar_data)
        p_transferer = mp.Process(target=target_with_nice_priority(data_transferer.start, 0))
        p_transferer.start()
        
        p_web_server = mp.Process(target=target_with_nice_priority(WebServer, 0), args=(self.frame_list, [self.lidar_data_list, self.interpolated_lidar_data], 5000, '192.168.178.88'))
        p_web_server.start()

        return cam, lidar, data_transferer
    
    def choose_mode(self):
        with open ("RPIs/DataManager/mode.txt", "r") as file:
            mode = file.read().strip()
            
            print(f"Mode: {mode}")
                    
        return mode
    
    def start(self):
        self.logger.info('Starting AIController...')
        self.client.send_message('START')
        
        self.running = True
        
        if self.mode == 'OpeningRace':
            self.main_loop_opening_race()
            
        elif self.mode == 'ObstacleRace':
            self.main_loop_obstacle_race()
            
        elif self.mode == 'Training':
            main_loop_training(self)
            
        else:
            self.logger.error(f'Unknown mode: {self.mode}')
            self.running = False
    
    def main_loop_opening_race(self):
        self.logger.info("Starting main loop for opening race...")
        
        while self.running:
            # print("running")
            # self.logger.info(f"LIDAR data: {self.lidar_data_list[-1]}")
                
            
            time.sleep(0.1)
        
        print("Opening ended. !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ")
        
    def main_loop_obstacle_race(self):
        self.logger.info("Starting main loop for obstacle race...")

        
if __name__ == "__main__":
    try:
        data_manager = DataManager()
        # time.sleep(10)
        data_manager.start()
    finally:
        data_manager.lidar.stop_sensor()
        data_manager.receiver.server_socket.close()
        data_manager.logger.info("DataManager stopped.")
        data_manager.logger.info("Exiting...")