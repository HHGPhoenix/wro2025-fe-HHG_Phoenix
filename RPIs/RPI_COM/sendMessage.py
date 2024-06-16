import socket

class Messenger:
    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port

    def send_message(self, message):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.ip_address, self.port))
                s.sendall(message.encode())
                response = s.recv(1024)
                return response.decode()
        except Exception as e:
            print(f"Error: {e}")
            return None
