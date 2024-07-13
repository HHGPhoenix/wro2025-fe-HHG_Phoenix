import socket
import time

class Messenger:
    def __init__(self, ip_address="127.0.0.1", port=11111):
        self.ip_address = ip_address
        self.port = port
        self.socket = None
        self.connect()

    def connect(self):
            """Attempt to connect to the server."""
            attempt_count = 0  # Initialize the attempt counter
            
            while True:
                attempt_count += 1  # Increment the attempt counter
                try:
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.connect((self.ip_address, self.port))
                    print(f"\rConnection established after {attempt_count} attempts.                      ", end='')
                    return
                except Exception as e:
                    # Print the error message with the attempt count
                    print(f"\rAttempt {attempt_count} failed: {e}                      ", end='')
                    self.socket = None
                    time.sleep(0.5)

    def send_message(self, message, attempts=50):
        """Send a message, attempting to reconnect if necessary."""
        if not self.socket:
            print("No connection. Attempting to reconnect...")
            self.connect()

        if self.socket:
            for attempt in range(attempts):
                try:
                    message = message + "\n"
                    self.socket.sendall(message.encode())
                    # print("Message sent successfully.")
                    # Optionally, receive and return a response here
                    return
                except Exception as e:
                    print(f"Error sending message: {e}. Attempting to reconnect...")
                    self.socket = None
                    self.connect()
            print("Failed to send message after several attempts.")

    def close_connection(self):
        """Close the connection to the server."""
        if self.socket:
            try:
                self.socket.close()
                print("Connection closed.")
            except Exception as e:
                print(f"Error closing connection: {e}")
