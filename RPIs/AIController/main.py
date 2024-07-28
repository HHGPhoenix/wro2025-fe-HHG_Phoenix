import time
import threading
from RPIs.RPI_COM.messageReceiverServer import MessageReceiver
from RPIs.RPI_COM.sendMessage import Messenger
from RPIs.AIController.AICLib import AICU_Logger, RemoteFunctions

from RPIs.RPI_COM.ComEstablisher.ComEstablisher import CommunicationEstablisher

# from RPIs.Devices.Dummy.Servo.Servo import Servo
# from RPIs.Devices.Dummy.MotorController.MotorController import MotorController
from RPIs.Devices.Servo.Servo import Servo
from RPIs.Devices.MotorController.MotorController import MotorController
import tensorflow as tf

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
        self.mode = "OpeningRace"
        self.servo = None
        self.interpolated_lidar_data = None
        
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
        
        motor_controller = MotorController()
        
        return servo, motor_controller
    
    ###########################################################################
    
    def start(self):
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
            self.main_loop_opening_race()
            
        elif self.mode == 'ObstacleRace':
            self.main_loop_obstacle_race()
            
        elif self.mode == 'Training':
            self.main_loop_training()
            
        else:
            self.logger.error(f'Unknown mode: {self.mode}')
            self.running = False
    
    ###########################################################################

    def main_loop_opening_race(self):
        import pandas as pd
        self.logger.info("Starting main loop for opening race...")
        
        self.model = tf.keras.models.load_model('RPIs/AIController/model.h5')
        
        while self.running:
            # run the model
            if len(self.interpolated_lidar_data) == 0:
                time.sleep(0.1)
                continue
            
            lidar_data = []
            
            # print(f"len(self.lidar_data): {len(self.lidar_data)}, self.lidar_data[-1]: {self.lidar_data}")
            
            df = pd.DataFrame(self.interpolated_lidar_data, columns=["angle", "distance", "intensity"])
            
            df = df.drop(columns=["intensity"])

            df_interpolated_list = df.values.tolist()  
            
            lidar_data.append(df_interpolated_list)
            
            # print(f"lidar_data: {lidar_data}")
            
            prediction = self.model.predict(lidar_data)
            
            print(f"prediction: {prediction}")
            
            servo_angle = self.servo.mapToServoAngle(prediction[0][0])
            self.servo.setAngle(servo_angle)
            
            motor_speed = 0.3
            
            self.motor_controller.send_speed(motor_speed)
        
    def main_loop_obstacle_race(self):
        self.logger.info("Starting main loop for obstacle race...")
        
        while self.running:
            pass
        
    def main_loop_training(self):
        self.logger.info("Starting main loop for training...")
        
        while self.running:
            servo_angle = self.servo.mapToServoAngle(self.x)
            # print(f"servo_angle: {servo_angle:.2f}", end=' ')
            self.servo.setAngle(servo_angle)
            
            if self.ry < 0.55 and self.ry > 0.45:
                motor_speed = 0.5
            else:
                motor_speed = self.ry
            
            self.motor_controller.send_speed(motor_speed)
            
            time.sleep(0.05)

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