import time
import threading
from RPIs.RPI_COM.messageReceiverServer import MessageReceiver
from RPIs.RPI_COM.sendMessage import Messenger
from RPIs.AIController.AICLib import AICU_Logger, RemoteFunctions, CommunicationEstablisher

class AIController:
    def __init__(self):
        print("Starting AIController...")
        self.receiver = None
        self.client = None
        self.logger = None
        self.mode = None
        self.running = False
        self.communicationestablisher = CommunicationEstablisher(self)
        self.start_comm()

        self.logger.info("AIController started.")

        self.communicationestablisher.spam()

    def start_comm(self):
        self.remote_functions = RemoteFunctions(self)
        
        # Start the server
        self.receiver = MessageReceiver(r'RPIs\RPI_COM\Mappings\AIControllerMappings.json', 22222, handler_class=self.remote_functions)
        threading.Thread(target=self.receiver.start_server, daemon=True).start()

        self.client = Messenger('192.168.1.3', 11111)

        self.logger = AICU_Logger(self.client)

    def main_loop_opening_race(self):
        self.logger.info("Starting main loop for opening race...")
        
        while self.running:
            pass
        
    def main_loop_obstacle_race(self):
        self.logger.info("Starting main loop for obstacle race...")
        
        while self.running:
            pass