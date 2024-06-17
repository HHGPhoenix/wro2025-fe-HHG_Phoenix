from RPIs.RPI_Logging.Logger import Logger

class RemoteFunctions:
    def __init__(self):
        logger_obj = Logger()
        self.logger = logger_obj.setup_log()

    def execute_LOG_DEBUG(self, message):
        self.logger.debug(f"--AIController--: {message}")

    def execute_LOG_INFO(self, message):
        self.logger.info(f"--AIController--: {message}")

    def execute_LOG_WARNING(self, message):
        self.logger.warning(f"--AIController--: {message}")

    def execute_LOG_ERROR(self, message):
        self.logger.error(f"--AIController--: {message}")

    def execute_LOG_CRITICAL(self, message):
        self.logger.critical(f"--AIController--: {message}")

    def execute_LOG_EXCEPTION(self, message):
        self.logger.exception(f"--AIController--: {message}")