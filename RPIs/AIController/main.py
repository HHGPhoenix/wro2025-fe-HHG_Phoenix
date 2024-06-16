import time
import threading
from RPIs.RPI_COM.messageReceiverServer import MessageReceiver
from RPIs.RPI_COM.sendMessage import Messenger
from AICUtilityFunctions import AICU_Logger

class RemoteFunctions:
    def __init__(self):
        pass

# Start the server
receiver = MessageReceiver(r'RPIs\RPI_COM\Mappings\AIControllerMappings.json', 22222, handler_class=RemoteFunctions)
threading.Thread(target=receiver.start_server, daemon=True).start()

time.sleep(2)  # Give the server some time to start

client = Messenger('127.0.0.1', 11111)  # Use '127.0.0.1' instead of '0.0.0.0' for the client

logger = AICU_Logger(client)

logger

print("AIController started")

client.send_message('LOG_DEBUG#This is a debug message')

time.sleep(2)   

client.send_message('LOG_INFO#This is an info message')
