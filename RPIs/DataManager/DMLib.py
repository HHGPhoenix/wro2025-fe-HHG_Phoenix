from RPIs.RPI_Logging.Logger import Logger
import time
import threading

COM_LOCK = threading.Lock()
COM_HANDLE_ACTIVE = False

class RemoteFunctions:
    def __init__(self, DataManager):
        self.DataManager = DataManager
        self.logger = DataManager.logger_obj

    def log_debug(self, message):
        self.logger.debug(f"--DataManager--: {message}")

    def log_info(self, message):
        self.logger.info(f"--DataManager--: {message}")

    def log_warning(self, message):
        self.logger.warning(f"--DataManager--: {message}")

    def log_error(self, message):
        self.logger.error(f"--DataManager--: {message}")

    def log_critical(self, message):
        self.logger.critical(f"--DataManager--: {message}")

    def log_exception(self, message):
        self.logger.exception(f"--DataManager--: {message}")

###########################################################################
    
    def send_heartbeat(self):
        with COM_LOCK:
            if COM_HANDLE_ACTIVE:
                return
            
            COM_HANDLE_ACTIVE = True

        while not self.DataManager.initialized:
            time.sleep(0.1)

        if self.DataManager.running:
            self.DataManager.error('DataManager already running!')
            self.DataManager.client.send_message("ALREADY_RUNNING")
            COM_HANDLE_ACTIVE = False
            return

        self.DataManager.client.send_message('BEAT')
        COM_HANDLE_ACTIVE = False

    def receive_heartbeat(self):
        self.DataManager.communicationestablisher.received_message = True

    def handle_alread_running(self):
        self.DataManager.logger.error('DataManager already running!')

###########################################################################
    