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

###########################################################################
    
    def send_heartbeat(self):
        global COM_HANDLE_ACTIVE
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

    def handle_already_running(self):
        self.DataManager.logger.error('DataManager already running!')
        
    def receive_system_info(self, cpu_usage, memory_usage, disk_usage, temperature, voltage):
        self.DataManager.shared_info_list[0] = cpu_usage
        self.DataManager.shared_info_list[1] = memory_usage
        self.DataManager.shared_info_list[2] = disk_usage
        self.DataManager.shared_info_list[3] = temperature
        self.DataManager.shared_info_list[4] = voltage
        # print(f"System info: {cpu_usage}, {memory_usage}, {disk_usage}, {temperature}, {voltage}")

###########################################################################
    