import socket
import time
import threading  # Step 1: Import threading module

class Messenger:
    def __init__(self, ip_address="127.0.0.1", port=11111):
        self.ip_address = ip_address
        self.port = port
        self.socket = None
        self.connection_attempt_active = False
        self.connection_lock = threading.Lock()
        self.connect_wrapper()

    def connect(self):
        """Attempt to connect to the server in a separate thread, ensuring only one attempt is made."""
        with self.connection_lock:
            if self.connection_attempt_active:
                print("Connection attempt already in progress.")
                while self.connection_attempt_active:
                    time.sleep(0.1)
                return
            self.connection_attempt_active = True

        attempt_count = 0

        while True:
            attempt_count += 1
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.ip_address, self.port))
                print(f"\rConnection established after {attempt_count} attempts.")
                break
            except KeyboardInterrupt:
                raise KeyboardInterrupt  # Pass the exception to the main thread
            except Exception as e:
                print(f"\rAttempt {attempt_count} failed: {e}", end='')
                self.socket = None
                time.sleep(0.5)

        self.connection_attempt_active = False

    def connect_wrapper(self):
        """Start the connection attempt in a new thread."""
        connection_thread = threading.Thread(target=self.connect)
        connection_thread.start()

    def send_message(self, message, attempts=5):
        """Send a message, attempting to reconnect if necessary."""
        if not self.socket:
            print("No connection. Attempting to reconnect...")
            self.connect()

        while self.connection_attempt_active:
            time.sleep(0.1)

        if self.socket:
            for attempt in range(attempts):
                try:
                    message = message + "\n"
                    self.socket.sendall(message.encode())
                    return
                except (socket.error, Exception) as e:
                    print(f"Error sending message: {e}. Attempting to reconnect...")
                    self.close_socket()
                    self.connect()
            print("Failed to send message after several attempts.")
        else:
            print("Unable to establish connection.")

    def close_socket(self):
        """Close the socket safely."""
        if self.socket:
            try:
                self.socket.close()
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:
                print(f"Error closing socket: {e}")
            finally:
                self.socket = None
