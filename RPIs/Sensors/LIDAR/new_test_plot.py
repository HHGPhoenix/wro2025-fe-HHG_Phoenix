import matplotlib.pyplot as plt
import numpy as np
from LIDARManager import LidarSensor
import time
import threading
import queue

# Initialize the LIDAR sensor
lidar = LidarSensor(usb_address="COM4")
data_queue = queue.Queue()  # Create a queue to hold the data


try:
    lidar.start_sensor(mode="normal")
    # lidar.set_motor_speed(600)
    
    tLIDAR = threading.Thread(target=lidar.read_data)
    tLIDAR.start()
    
    time.sleep(1)  # Wait for the sensor to start

    plt.ion()  # Turn on interactive mode
    fig = plt.figure()
    ax = fig.add_subplot(111, polar=True)  # Create a polar subplot

    while True:
        if lidar.data_arrays:
            data_queue.put(lidar.data_arrays[-1])
        
        if not data_queue.empty():
            ax.clear()  # Clear the previous plot
            ax.set_xlim(0, 2 * np.pi)  # Set the angular limits
            data = data_queue.get()  # Get the latest data array from the queue

            # Convert the angles and distances to numpy arrays
            angles = np.array([item[0] for item in data])
            distances = np.array([item[1] for item in data])

            # Convert the angles from degrees to radians
            angles = np.deg2rad(angles)

            # Plot the data
            ax.scatter(angles, distances, s=3)

            # Set the radial limits
            ax.set_rlim(0, max(distances))

            # Draw the plot
            plt.draw()
            plt.pause(0.1)

finally:
    lidar.stop_sensor()
    plt.ioff()  # Turn off interactive mode
    plt.show()