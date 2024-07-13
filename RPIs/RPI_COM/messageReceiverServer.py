import socket
import ast
import json
import threading

class MessageReceiver:
    def __init__(self, mappings_file, port, handler_instance, ip='127.0.0.1'):
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
        #print message if command starts with 'ANALOG'
        # if command.startswith('ANALOG'):
            # print(f"Received message: {message}")
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
                # print(f"Executing {command} with arguments {values}")
                t_handler = threading.Thread(target=self.message_handler_map[command], args=(*values,), daemon=True)
                t_handler.start()
                return f"Success: {command} executed with arguments {values}"
            except Exception as e:
                return f"LOG: Error executing {command} with arguments {values} - {str(e)}"
        else:
            return f"LOG: No handler found for command: {command}"

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.ip, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.ip}:{self.port}")
    
        while True:
            # Check if the server_socket is still a valid socket
            if not self.server_socket.fileno() == -1:
                client_socket, client_address = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(client_socket, client_address), daemon=True).start()
            else:
                print("Socket is no longer valid.")
                break

    def handle_client(self, client_socket, client_address):
        print(f"Connection from {client_address}")

        buffer = ""
        
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                
                if data:
                    data = data.split('\n')
                    
                    if buffer:
                        data[0] = buffer + data[0]
                        buffer = ""
                    
                    if not "\n" in data[-1]:
                        buffer = data.pop(-1)
                    
                    for message in data:
                        message = message.strip()
                        if message:
                            # print(f"Received message: {message}")
                            response = self.handle_message(message)
                            # print(f"Response: {response}")
                            # client_socket.sendall(response.encode('utf-8'))
                    
        except Exception as e:
            print(f"Error handling client {client_address}: {e}")
        finally:
            client_socket.close()
