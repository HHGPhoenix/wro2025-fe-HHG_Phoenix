import time
import threading
from RPIs.RPI_COM.messageReceiverServer import MessageReceiver
from RPIs.RPI_COM.sendMessage import Messenger
from RPIs.RPI_Logging.Logger import Logger


class RemoteFunctions:
    def __init__(self):
        logger_obj = Logger()
        self.logger = logger_obj.setup_log()

    def execute_LOG_DEBUG(self, message):
        self.logger.debug(message)

    def execute_LOG_INFO(self, message):
        self.logger.info(message)

    def execute_LOG_WARNING(self, message):
        self.logger.warning(message)

    def execute_LOG_ERROR(self, message):
        self.logger.error(message)

    def execute_LOG_CRITICAL(self, message):
        self.logger.critical(message)

    def execute_LOG_EXCEPTION(self, message):
        self.logger.exception(message)


# Start the server
receiver = MessageReceiver(r'RPIs\RPI_COM\Mappings\DataManagerMappings.json', 11111, handler_class=RemoteFunctions)
threading.Thread(target=receiver.start_server, daemon=True).start()

time.sleep(1)  # Give the server some time to start

client = Messenger('127.0.0.1', 22222)  # Use '127.0.0.1' instead of '0.0.0.0' for the client
logger_obj = Logger()
logger = logger_obj.setup_log()

logger

while True:
    pass