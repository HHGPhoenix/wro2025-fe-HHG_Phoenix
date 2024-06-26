import socket
import ast
import json
import threading

class MessageReceiver:
    def __init__(self, mappings_file, port, handler_instance, ip='0.0.0.0'):
        self.handler_instance = handler_instance
        self.message_handler_map = {}
        self.load_mappings_from_json(mappings_file)
        self.ip = ip
        self.port = port

    def load_mappings_from_json(self, file_path):
        with open(file_path, 'r') as file:
            mappings = json.load(file)
            for command, function_name in mappings.items():
                self.message_handler_map[command] = getattr(self.handler_instance, function_name)

    def parse_message(self, message):
        parts = message.split('#')
        command = parts[0]
        values = [self.parse_value(part) for part in parts[1:]]
        return command, values

    def parse_value(self, value):
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return value

    def handle_message(self, message):
        command, values = self.parse_message(message)
        
        if command in self.message_handler_map:
            try:
                print(f"Executing {command} with arguments {values}")
                self.message_handler_map[command](*values)
                return f"Success: {command} executed with arguments {values}"
            except Exception as e:
                return f"LOG: Error executing {command} with arguments {values} - {str(e)}"
        else:
            return f"LOG: No handler found for command: {command}"

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Add this line
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.ip}:{self.port}")

        try:
            while True:
                client_socket, client_address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()
        except KeyboardInterrupt:
            print("Server is shutting down...")
        finally:
            self.server_socket.close()

    def handle_client(self, client_socket, client_address):
        print(f"Connection from {client_address}")
        
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if data:
                print(f"Received message: {data}")
                response = self.handle_message(data)
                print(f"Response: {response}")
                # client_socket.sendall(response.encode('utf-8'))
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
