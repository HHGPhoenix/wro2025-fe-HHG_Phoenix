import socket
import ast
import json
import threading

class MessageReceiver:
    def __init__(self, mappings_file, port, handler_class, ip='0.0.0.0'):
        self.handler_instance = handler_class()
        self.message_handler_map = {}
        self.load_mappings_from_json(mappings_file)
        self.ip = ip
        self.port = port

    def load_mappings_from_json(self, file_path):
        with open(file_path, 'r') as file:
            mappings = json.load(file)
            self.message_handler_map = {code: getattr(self.handler_instance, f"execute_{code}") for code in mappings}

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
                self.message_handler_map[command](*values)
                return f"Success: {command} executed with arguments {values}"
            except Exception as e:
                return f"LOG: Error executing {command} with arguments {values} - {str(e)}"
        else:
            return f"LOG: No handler found for command: {command}"

    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.ip, self.port))
        server_socket.listen(5)
        print(f"Server listening on {self.ip}:{self.port}")

        try:
            while True:
                client_socket, client_address = server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, client_address)).start()
        except KeyboardInterrupt:
            print("Server is shutting down...")
        finally:
            server_socket.close()

    def handle_client(self, client_socket, client_address):
        print(f"Connection from {client_address}")
        
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if data:
                print(f"Received message: {data}")
                response = self.handle_message(data)
                client_socket.sendall(response.encode('utf-8'))
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
