
class Client:
    def __init__(self, name, ip, port):
        self.name = name
        self.ip = ip
        self.port = port

    def __str__(self):
        return f"Client {self.name} at {self.ip}:{self.port}"

    def __repr__(self):
        return f"Client {self.name} at {self.ip}:{self.port}"