
class Messanger:
    def __init__(self, socket):
        self.socket = socket

    def send_message(self, message):
        self.socket.sendall(message.encode('utf-8'))