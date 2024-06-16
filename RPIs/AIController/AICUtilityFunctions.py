class AICU_Logger:

    def __init__(self, client):
        self.client = client

    def debug(self, message):
        self.client.send_message(f'LOG_DEBUG#{message}')

    def info(self, message):
        self.client.send_message(f'LOG_INFO#{message}')

    def warning(self, message):
        self.client.send_message(f'LOG_WARNING#{message}')

    def error(self, message):
        self.client.send_message(f'LOG_ERROR#{message}')

    def critical(self, message):
        self.client.send_message(f'LOG_CRITICAL#{message}')

    def exception(self, message):
        self.client.send_message(f'LOG_EXCEPTION#{message}')
