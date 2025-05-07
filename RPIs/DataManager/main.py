import time
import threading
from RPIs.RPI_COM.messageReceiverServer import MessageReceiver
from RPIs.RPI_COM.sendMessage import Messenger
from RPIs.RPI_Logging.Logger import Logger, LoggerDatamanager
from RPIs.DataManager.DMLib import RemoteFunctions
from RPIs.Devices.Failsafe.Failsafe import Failsafe

from RPIs.RPI_COM.ComEstablisher.ComEstablisher import CommunicationEstablisher

from RPIs.Devices.LIDAR.LIDAR import Lidar
from RPIs.Devices.Button.Button import Button
from RPIs.Devices.I2C.DisplayOLED.DisplayManager import Display
from RPIs.Devices.Utility.NotificationClient.NotificationClient import NotificationClient
# from RPIs.Devices.Dummy.LIDAR.LIDAR import Lidar

from RPIs.DataManager.DataTransferer.DataTransferer import DataTransferer
from RPIs.WebServer.WebServer import WebServer

from RPIs.DataManager.Mainloops.TrainingLoop import main_loop_training
from RPIs.DataManager.Mainloops.OpeningRace import main_loop_opening_race
from RPIs.DataManager.Mainloops.ObstacleRace import main_loop_obstacle_race

import multiprocessing as mp
import os
import platform
import traceback

###########################################################################

START_LOCAL_SERVER = False

###########################################################################

os.system('cls' if os.name=='nt' else 'clear')
print("\n\nStarting DataManager only for you :)\n\n")

###########################################################################

def set_nice_priority(nice_value):
    try:
        os.nice(nice_value)
    except AttributeError:
        pass  # os.nice() is not available on Windows

def target_with_nice_priority(target, nice_value, *args, **kwargs):
    if platform.system() != 'Windows':
        set_nice_priority(nice_value)
    target(*args, **kwargs)

###########################################################################

class DataManager:
    def __init__(self):
        self.initialized = False

        print("Initializing DataManager...")
        
        self.receiver = None
        self.client = None
        self.logger = None
        self.cam = None
        self.lidar = None
        self.mode = None
        self.data_transferer = None
        self.failsafe = None
        
        self.current_edge = 0
        self.last_yaw = 0
        self.relative_angle = 0

        self.running = False

        self.mp_manager = mp.Manager()
        self.frame_list = self.mp_manager.list([None, None, None, None, None])
        self.interpolated_lidar_data = self.mp_manager.list([None])
        self.lidar_data_list = self.mp_manager.list()
        self.shared_info_list = self.mp_manager.list([0, 0, 0, 0, 0, 0, 0, 0]) # 0 - CPU; 1 - Memory; 2 - Disk; 3 - Temperature; 4 - Voltage; 5 - Roll; 6 - Pitch; 7 - Yaw
        
        self.communicationestablisher = CommunicationEstablisher(self)
        
        self.start_comm()
        
        self.lidar, self.data_transferer, self.notification_client, self.failsafe, self.display, self.button = self.initialize_components()
        self.communicationestablisher.establish_communication()
        
        self.logger.info("DataManager initialized.")
        
        self.initialized = True
        
        self.display.write_centered_text("Ready!", clear_display=True)
        self.mode = self.choose_mode()
        self.client.send_message(f"MODE#{self.mode}")
        
    def start_comm(self):
        logger_obj = Logger()
        self.logger_obj = logger_obj.setup_log()
        self.logger = LoggerDatamanager(self.logger_obj)
        
        self.remotefunctions = RemoteFunctions(self)

        if not START_LOCAL_SERVER:
            self.receiver = MessageReceiver(r'RPIs/RPI_COM/Mappings/DataManagerMappings.json', 11111, handler_instance=self.remotefunctions, ip='10.10.1.5')
            threading.Thread(target=self.receiver.start_server, daemon=True).start()
            self.client = Messenger('10.10.1.2', port=22222)
        else:
            self.receiver = MessageReceiver(r'RPIs/RPI_COM/Mappings/DataManagerMappings.json', 11111, handler_instance=self.remotefunctions)
            threading.Thread(target=self.receiver.start_server, daemon=True).start()
            self.client = Messenger(port=22222)

    def initialize_components(self):
        self.logger.info("Initializing LIDAR sensor...")
        
        lidar = Lidar(self.lidar_data_list)
        self.lidarProcess = mp.Process(target=target_with_nice_priority, args=(lidar.read_data, -10), daemon=True)
        self.lidarProcess.start()
        self.logger.info("Camera and LIDAR initialized.")
        
        data_transferer = DataTransferer(lidar, self.frame_list, self.lidar_data_list, self.interpolated_lidar_data)
        self.dataTransferProcess = mp.Process(target=target_with_nice_priority, args=(data_transferer.start, 0), daemon=True)
        self.dataTransferProcess.start()
        
        if not START_LOCAL_SERVER:
            self.webServerProcess = mp.Process(target=target_with_nice_priority, args=(WebServer, 0, self.frame_list, [self.lidar_data_list, self.interpolated_lidar_data], self.shared_info_list, 5000), daemon=True)
        else:
            self.webServerProcess = mp.Process(target=target_with_nice_priority, args=(WebServer, 0, self.frame_list, [self.lidar_data_list, self.interpolated_lidar_data], self.shared_info_list, 5000), daemon=True)
        self.webServerProcess.start()
        
        notification_client = NotificationClient()
        
        display = Display(0)
        display.write_centered_text("DataManager Screen", clear_display=True)
        
        failsafe = Failsafe(self)
        threading.Thread(target=target_with_nice_priority, args=(failsafe.mainloop, 0), daemon=True).start()
        
        button = Button(18)

        return lidar, data_transferer, notification_client, failsafe, display, button
    
###########################################################################
    
    def choose_mode(self):
        with open ("RPIs/DataManager/mode.txt", "r") as file:
            mode = file.read().strip()
            
            print(f"Mode: {mode}")
                    
        return mode
    
    def start(self):
        try:
            self.logger.info('Starting AIController...')
            self.client.send_message('START')
            
            self.running = True
            
            if self.mode == 'OpeningRace':
                main_loop_opening_race(self)
                
            elif self.mode == 'ObstacleRace':
                main_loop_obstacle_race(self)
                
            elif self.mode == 'Training':
                main_loop_training(self)
                
            else:
                self.logger.error(f'Unknown mode: {self.mode}')
                self.running = False
                
        except Exception as e:
            self.logger.error(f"Exception occurred: {e}")
            traceback.print_exc()
        
        finally:
            self.client.send_message('STOP')
            time.sleep(0.1)
            self.client.send_message('STOP')
            time.sleep(0.1)
            self.client.send_message('STOP')
            
###########################################################################

if __name__ == "__main__":
    data_manager = None
    try:
        data_manager = DataManager()
        # if data_manager.mode != 'Training':
        #     data_manager.button.wait_for_press()
        data_manager.start()
        
    except Exception as e:
        print(f"Exception occurred: {e}")
        traceback.print_exc()
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt")
    finally:
        print("\nDataManager stopped.")