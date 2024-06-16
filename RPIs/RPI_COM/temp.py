import time
from messageReceiverServer import MessageReceiver
from sendMessage import Messenger
import threading

class Handler:
    def execute_AB(self, value1, value2):
        print(f"Executing command AB with values {value1} and {value2}")
        
    def execute_2(self, value1, value2):
        print(f"Executing command 2 with values {value1} and {value2}")
        
    def execute_3(self, value1, value2, value3):
        print(f"Executing command 3 with values {value1}, {value2}, and {value3}")


# Start the server
receiver = MessageReceiver(r'RPIs\RPI_COM\Mappings\Controller.json', 12345, handler_class=Handler)
threading.Thread(target=receiver.start_server, daemon=True).start()

time.sleep(1)  # Give the server some time to start

# Client sending a message
client = Messenger('127.0.0.1', 12345)  # Use '127.0.0.1' instead of '0.0.0.0' for the client
response = client.send_message('AB#1#2')
print(f"Client received response: {response}")
