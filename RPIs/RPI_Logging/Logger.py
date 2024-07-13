import logging
import os
import platform
from logging.handlers import RotatingFileHandler
from datetime import datetime

class LoggerTemplate:
    def __init__(self, log_dir='LOGS', log_file_prefix='app_log', max_files=10, max_file_size=50*1024*1024):
        """
        Initialize the Logger class.

        Parameters:
        log_dir (str): Directory to store log files.
        log_file_prefix (str): Prefix for log file names.
        max_files (int): Maximum number of log files to retain.
        max_file_size (int): Maximum size (in bytes) of each log file before rotation.
        """
        self.local_log_dir = log_dir
        self.usb_log_dir = self._find_usb_log_dir() if platform.system() == 'Linux' else None
        self.log_file_prefix = log_file_prefix
        self.max_files = max_files
        self.max_file_size = max_file_size
        self.logger = None

    def setup_log(self):
        """
        Setup the logging configuration.
        
        Returns:
            logger (logging.Logger): Configured logger instance.
        """
        if not os.path.exists(self.local_log_dir):
            os.makedirs(self.local_log_dir)

        # Use a fixed log file name for the duration of the script's execution
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        local_log_filename = os.path.join(self.local_log_dir, f"{self.log_file_prefix}_{timestamp}.log")

        # Setup logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()

        # Create file handler for local logging
        local_file_handler = RotatingFileHandler(
            local_log_filename, maxBytes=self.max_file_size, backupCount=self.max_files
        )

        # Set logging levels for handlers
        console_handler.setLevel(logging.DEBUG)
        local_file_handler.setLevel(logging.DEBUG)
        
        # Create formatter with timestamp and add it to handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        local_file_handler.setFormatter(formatter)
        
        # Add handlers to the logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(local_file_handler)
        
        self.logger.info("Logger initialized locally")

        # Manage local log files
        self._manage_log_files(self.local_log_dir)

        # Setup USB logging if applicable
        if self.usb_log_dir:
            usb_log_filename = os.path.join(self.usb_log_dir, f"{self.log_file_prefix}_{timestamp}.log")
            usb_file_handler = RotatingFileHandler(
                usb_log_filename, maxBytes=self.max_file_size, backupCount=self.max_files
            )
            usb_file_handler.setLevel(logging.DEBUG)
            usb_file_handler.setFormatter(formatter)
            self.logger.addHandler(usb_file_handler)
            self.logger.info(f"Logger also initialized on USB drive at {self.usb_log_dir}")
            
            # Manage USB log files
            self._manage_log_files(self.usb_log_dir)

        return self.logger

    def _manage_log_files(self, directory):
        """
        Manage log files to ensure only the latest 'max_files' are kept in the specified directory.

        Parameters:
        directory (str): Directory to manage log files.
        """
        log_files = sorted(
            (f for f in os.listdir(directory) if f.startswith(self.log_file_prefix) and f.endswith(".log")),
            key=lambda f: os.path.getctime(os.path.join(directory, f))
        )
        
        while len(log_files) > self.max_files:
            oldest_file = log_files.pop(0)
            os.remove(os.path.join(directory, oldest_file))

    def _find_usb_log_dir(self):
        """
        Find if there is a USB drive with a 'LOGS' folder.

        Returns:
        str: Path to the 'LOGS' folder on the USB drive if found, otherwise None.
        """
        # Possible mount points for USB drives
        usb_mount_points = ['/media', '/mnt']

        for mount_point in usb_mount_points:
            if os.path.exists(mount_point):
                for subdir in os.listdir(mount_point):
                    potential_log_dir = os.path.join(mount_point, subdir, 'LOGS')
                    if os.path.isdir(potential_log_dir):
                        return potential_log_dir

        return None

class Logger():
    def __init__(self):
        self.logger_template = LoggerTemplate()

    def setup_log(self):
        return self.logger_template.setup_log()
    
    def _manage_log_files(self, directory):
        self.logger_template._manage_log_files(directory)

    def _find_usb_log_dir(self):
        return self.logger_template._find_usb_log_dir()
    
    def debug(self, message):
        self.logger_template.logger.debug(f"{message}")

    def info(self, message):
        self.logger_template.logger.info(f"{message}")

    def warning(self, message):
        self.logger_template.logger.warning(f"{message}")

    def error(self, message):
        self.logger_template.logger.error(f"{message}")

    def critical(self, message):
        self.logger_template.logger.critical(f"{message}")

class LoggerDatamanager():
    def __init__(self, Logger):
        self.logger = Logger

    def debug(self, message):
        self.logger.debug(f" --Datamanager-- {message}")

    def info(self, message):
        self.logger.info(f" --Datamanager-- {message}")

    def warning(self, message):
        self.logger.warning(f" --Datamanager-- {message}")

    def error(self, message):
        self.logger.error(f" --Datamanager-- {message}")

    def critical(self, message):
        self.logger.critical(f" --Datamanager-- {message}")

        
# Usage
if __name__ == "__main__":
    logger_obj = Logger()
    logger = logger_obj.setup_log()
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")
