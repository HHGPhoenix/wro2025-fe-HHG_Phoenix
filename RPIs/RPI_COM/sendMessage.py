import socket
import time
import threading  # Step 1: Import threading module

class Messenger:
    def __init__(self, ip_address="127.0.0.1", port=11111):
        self.ip_address = ip_address
        self.port = port
        self.socket = None
        connection_thread = threading.Thread(target=self.connect_wrapper)  # Step 3: Start the thread
        connection_thread.start()
        self.connection_attempt_active = False
        self.connection_lock = threading.Lock()

    def connect(self):  # Step 2: Define the method to run in a thread
        """Attempt to connect to the server in a separate thread, ensuring only one attempt is made."""
        with self.connection_lock:  # Acquire the lock
            if self.connection_attempt_active:
                print("Connection attempt already in progress.")
                while self.connection_attempt_active:
                    time.sleep(0.1)
                return
            self.connection_attempt_active = True
    
        attempt_count = 0  # Initialize the attempt counter
    
        while True:  # Ensure only one attempt is made
            attempt_count += 1  # Increment the attempt counter
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.ip_address, self.port))
                print(f"\rConnection established after {attempt_count} attempts.", end='')
                break  # Exit the loop after a successful connection
            except KeyboardInterrupt:
                raise KeyboardInterrupt # Pass the exception to the main thread
            
            except Exception as e:
                # Print the error message with the attempt count
                print(f"\rAttempt {attempt_count} failed: {e}", end='')
                self.socket = None
                time.sleep(0.5)
    
        self.connection_attempt_active = False  # Reset the flag after the attempt

    def connect_wrapper(self):
        """Start the connection attempt in a new thread."""
        connection_thread = threading.Thread(target=self.connect)  # Step 3: Start the thread
        connection_thread.start()

    def send_message(self, message, attempts=50):
        """Send a message, attempting to reconnect if necessary."""
        if not self.socket:
            # print("No connection. Attempting to reconnect...")
            self.connect()
        
        while self.connection_attempt_active:
            time.sleep(0.1)

        if self.socket:
            for attempt in range(attempts):
                try:
                    message = message + "\n"
                    self.socket.sendall(message.encode())
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