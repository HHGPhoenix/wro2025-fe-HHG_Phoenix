from RPIs.Devices.Camera.CameraManager import Camera
from RPIs.Devices.LIDAR.LIDARManager import LidarSensor
import threading
import socket

cam = Camera()

lidar = LidarSensor("/dev/ttyAMA0")

lidar.reset_sensor()
lidar.start_sensor()

tlidar = threading.Thread(target=lidar.read_data)
tlidar.start()

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('192.168.1.2', 11111))

try:
    while True:
            output = {}
            
            frameraw, framehsv = cam.capture_array()
            simplified_image = cam.simplify_image(framehsv, [255, 0, 0], [0, 255, 0])
            
            if len(lidar.data_arrays) > 0:
                lidar_data = lidar.data_arrays[-1]
                
                lidar_data = lidar.interpolate_data(lidar_data)
                
                output.update({"simplified_image": simplified_image, "lidar_data": lidar_data})
                
                client.sendall(str(output).encode())
        
finally:
    lidar.stop_sensor()