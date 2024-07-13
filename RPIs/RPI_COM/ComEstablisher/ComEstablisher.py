import time

class CommunicationEstablisher():
    def __init__(self, pi):
        self.pi = pi
        self.received_message = None

    def establish_communication(self):
        print("Spamming started...")
        print(f"self.received_message: {self.received_message}")
        while self.received_message == None:
            self.pi.client.send_message("HEART")
            time.sleep(0.1)