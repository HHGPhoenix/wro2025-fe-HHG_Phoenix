import time
import threading
import cv2
import multiprocessing as mp
import os
import signal
import requests
import psutil
from RPIs.RPI_COM.messageReceiverServer import MessageReceiver
from RPIs.RPI_COM.sendMessage import Messenger
from RPIs.AIController.AICLib import AICU_Logger, RemoteFunctions

from RPIs.RPI_COM.ComEstablisher.ComEstablisher import CommunicationEstablisher

from RPIs.AIController.Mainloops.OpeningRace import main_loop_opening_race
from RPIs.AIController.Mainloops.ObstacleRace import main_loop_obstacle_race
from RPIs.AIController.Mainloops.TrainingLoop import main_loop_training

# from RPIs.Devices.Dummy.Servo.Servo import Servo
# from RPIs.Devices.Dummy.MotorController.MotorController import MotorController
from RPIs.Devices.Servo.Servo import Servo
from RPIs.Devices.I2C.DisplayOLED.DisplayManager import Display
from RPIs.Devices.MotorController.MotorController import MotorController

# import tensorflow as tf

###########################################################################

START_LOCAL_SERVER = False

###########################################################################

os.system('cls' if os.name=='nt' else 'clear')
print("\n\nStarting AIController only for you :(\n\n")

###########################################################################

class AIController:
    def __init__(self):
        self.initialized = False

        print("Initializing AIController...")

        self.receiver = None
        self.client = None
        self.logger = None
        self.mode = None
        self.servo = None
        self.stop_with_interrupt = False
        self.interpolated_lidar_data = None
        self.servo_pin = 4
        self.failsafe_mode = 0
        self.relative_angle = 0
        
        self.current_edge = 0
        self.last_yaw = 0
        self.relative_angle = 0
        
        self.running = False
        
        self.mp_manager = mp.Manager()
        self.block_list = self.mp_manager.list([None, None])
        
        self.x = 0.5
        self.y = 0.5
        self.rx = 0.5
        self.ry = 0.5
        
        self.servo, self.motor_controller, self.display = self.initialize_components()
        self.communicationestablisher = CommunicationEstablisher(self)
        self.start_comm()

        self.initialized = True
        self.logger.info("AIController initialized.")
        
        self.display.write_centered_text("Ready!", clear_display=True)
        self.communicationestablisher.establish_communication()
        
    
    def start_comm(self):
        self.remote_functions = RemoteFunctions(self)
        
        # Start the server
        if not START_LOCAL_SERVER:
            self.receiver = MessageReceiver(r'RPIs/RPI_COM/Mappings/AIControllerMappings.json', 22222, handler_instance=self.remote_functions, ip='192.168.1.2')
            threading.Thread(target=self.receiver.start_server, daemon=True).start()
            self.client = Messenger('192.168.1.3', port=11111)

        else:
            self.receiver = MessageReceiver(r'RPIs/RPI_COM/Mappings/AIControllerMappings.json', 22222, handler_instance=self.remote_functions)
            threading.Thread(target=self.receiver.start_server, daemon=True).start()
            self.client = Messenger(port=11111)

        self.logger = AICU_Logger(self.client)
        
    def initialize_components(self):
        display = Display(1)
        display.write_centered_text("AIController Screen", clear_display=True)
        
        servo = Servo(self.servo_pin, minAngle=94, middleAngle=117, maxAngle=147)
        servo.setAngle(120)
        
        motor_controller = MotorController()
        motor_controller.reset()

        transmit_information_thread = threading.Thread(target=self.transmit_information, daemon=True)
        transmit_information_thread.start()
        
        return servo, motor_controller, display
    
    def transmit_information(self):
        while True:
            self.stop_with_interrupt
            start_time = time.time()
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent 
            cpu_temp = round(int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1000, 2)
            
            if self.motor_controller.voltage != 0:
                self.client.send_message(f"SYSTEM_INFO#{cpu_usage}#{memory_usage}#{disk_usage}#{cpu_temp}#{self.motor_controller.voltage}#{self.motor_controller.roll}#{self.motor_controller.pitch}#{self.motor_controller.yaw}")
            stop_time = time.time()
            # if it took longer than 1 second to get the information, raise a warning
            if stop_time - start_time > 1:
                self.logger.warning(f"Transmitting information took {stop_time - start_time} seconds.")
            time.sleep(max(0, 0.1 - (stop_time - start_time)))
    
    ###########################################################################
    
    def start(self):
        try:
            # for i in range(3):
            #     time.sleep(1)
            #     self.logger.info(f"Waiting ... {i}")

            if self.running:
                self.logger.error('AIController already running!')
                return
            
            while not self.initialized:
                time.sleep(0.1)

            self.logger.info('Starting AIController...')
            
            self.running = True
            self.motor_controller.reset()
            
            if self.mode == 'OpeningRace':
                main_loop_opening_race(self)
                
            elif self.mode == 'ObstacleRace':
                main_loop_obstacle_race(self)
                
            elif self.mode == 'Training':
                main_loop_training(self)
                
            else:
                self.logger.error(f'Unknown mode: {self.mode}')
                self.running = False
        
        finally:
            self.motor_controller.send_speed(0.5)
            self.servo.stop()
       
###########################################################################     

if __name__ == "__main__":
    ai_controller = None 
    try:
        ai_controller = AIController()  
        
        while not ai_controller.stop_with_interrupt:
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt")
        
    finally:
        print("\nAIController stopped.")