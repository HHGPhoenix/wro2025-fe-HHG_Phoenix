import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('192.168.1.2', 11111))

while True:
    server.listen(1)
    conn, addr = server.accept()
    
    try:
        while True:
            data = conn.recv(1024)

            
    finally:
        conn.close()
        break