from RPIs.RPI_Logging.Logger import Logger
import time

class RemoteFunctions:
    def __init__(self, DataManager):
        self.DataManager = DataManager
        logger_obj = Logger()
        self.logger = logger_obj.setup_log()

    def log_debug(self, message):
        self.logger.debug(f"--AIController--: {message}")

    def log_info(self, message):
        self.logger.info(f"--AIController--: {message}")

    def log_warning(self, message):
        self.logger.warning(f"--AIController--: {message}")

    def log_error(self, message):
        self.logger.error(f"--AIController--: {message}")

    def log_critical(self, message):
        self.logger.critical(f"--AIController--: {message}")

    def log_exception(self, message):
        self.logger.exception(f"--AIController--: {message}")
    
    def send_good(self):
        self.DataManager.client.send_message('GOOD')

    def receive_good(self):
        self.DataManager.communicationestablisher.received_message = 'GOOD'
    
class CommunicationEstablisher():
    def __init__(self, pi):
        self.pi = pi
        self.received_message = None


    def spam(self):
        while self.received_message == None:
            self.pi.client.send_message("How is it going?")
            time.sleep(1)