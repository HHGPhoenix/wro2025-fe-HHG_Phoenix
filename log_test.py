from RPIs.RPI_Logging.Logger import Logger, LoggerDatamanager

logger_obj = Logger()
logger = logger_obj.setup_log()

logger_datamanager = LoggerDatamanager(logger)

logger_datamanager.debug("This is a debug message.")
logger_datamanager.info("This is an info message.")
logger_datamanager.warning("This is a warning message.")