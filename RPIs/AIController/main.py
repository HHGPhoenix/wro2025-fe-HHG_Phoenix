import time
import threading
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
from RPIs.Devices.MotorController.MotorController import MotorController
# import tensorflow as tf

###########################################################################

START_LOCAL_SERVER = False

###########################################################################

class AIController:
    def __init__(self):
        self.initialized = False

        self.servo_pin = 4
        
        print("Starting AIController...")
        self.receiver = None
        self.client = None
        self.logger = None
        self.mode = "Training"
        self.servo = None
        self.interpolated_lidar_data = None
        self.simplified_image = None
        
        self.running = False
        
        self.x = 0.5
        self.y = 0.5
        self.rx = 0.5
        self.ry = 0.5
        
        self.communicationestablisher = CommunicationEstablisher(self)

        self.start_comm()

        self.logger.info("AIController started.")
        
        self.servo, self.motor_controller = self.initialize_components()
        
        self.initialized = True

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
        servo = Servo(self.servo_pin, minAngle=94, middleAngle=120, maxAngle=150)
        servo.setAngle(120)
        
        motor_controller = MotorController()
        
        return servo, motor_controller
    
    ###########################################################################
    
    def start(self):
        try:
            for i in range(3):
                time.sleep(1)
                self.logger.info(f"Waiting ... {i}")

            if self.running:
                self.logger.error('AIController already running!')
                return
            
            while not self.initialized:
                time.sleep(0.1)

            self.logger.info('Starting AIController...')
            
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
        
        finally:
            self.motor_controller.send_speed(0.5)
            self.servo.stop()
    
###########################################################################

if __name__ == "__main__":
    ai_controller = None 
    try:
        ai_controller = AIController()  
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt")
    finally:
        print("\nAIController stopped.")