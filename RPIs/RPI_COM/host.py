import socket
import time

class Host:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))
        self.socket.setblocking(0)

    def send_message(self, message):
        self.socket.sendall(message.encode('utf-8'))

    def receive_message(self):
        try:
            return self.socket.recv(1024).decode('utf-8')
        except:
            return None

    def close(self):
        self.socket.close()

    def is_connected(self):
        return self.socket.fileno() != -1

    def wait_for_connection(self):
        while not self.is_connected():
            time.sleep(0.1)
        return True

    def wait_for_message(self):
        while True:
            message = self.receive_message()
            if message:
                return message
            time.sleep(0.1)

    def send_and_receive(self, message):
        self.send_message(message)
        return self.wait_for_message()