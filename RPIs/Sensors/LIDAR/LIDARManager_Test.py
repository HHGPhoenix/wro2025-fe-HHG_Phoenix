from lidarManager import LidarSensor

lidar = LidarSensor()

lidar.start_sensor()

try:
    while True:
        data = lidar.read_data()
        print(data)
        
except:
    lidar.stop_sensor()
    print("Lidar sensor stopped.")