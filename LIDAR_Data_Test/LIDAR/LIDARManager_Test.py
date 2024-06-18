import serial
import threading
import matplotlib.pyplot as plt
import numpy as np
import time

# Open serial connection
ser = serial.Serial('COM4', 460800)  # replace 'COM4' with your port

angle = 0

# reset_cmd = b'\xA5\x40'
# ser.write(reset_cmd)

# time.sleep(1)  # Wait for the sensor to reset

# while ser.in_waiting < 15:
#     pass

# ser.read(15)  # Read the first 15 bytes

# Send SCAN command
scan_cmd = b'\xA5\x20'
ser.write(scan_cmd)

# Initialize the scans dictionary
scans = {}

# Create a new figure and a polar subplot
fig, ax = plt.subplots(subplot_kw={'projection': 'polar'})

# Set the range of your plot
ax.set_rlim(0, 1000)  # replace 1000 with the maximum expected distance

# Create a scatter object
scatter = ax.scatter([], [], s=3)

# Thread-safe queue for data
data_queue = []

def read_data():
    while True:
        if ser.in_waiting >= 5:
            data = ser.read(5)
            quality = data[0] >> 2  # Extracts the quality from the first byte
            angle = ((data[2] << 7) + (data[1] >> 1)) / 64.0  # Extracts the angle from the second and third bytes
            distance = ((data[3]) + (data[4] << 7)) / 4.0  # Extracts the distance from the fourth and fifth bytes

            data_queue.append((angle, distance, quality))
            
            # Remove the oldest data if the queue size exceeds 360
            if len(data_queue) > 520:
                data_queue.pop(0)

while ser.in_waiting < 7:
    pass

# Read the first 7 bytes
data = ser.read(7)

# Start the data reading thread
thread = threading.Thread(target=read_data)
thread.daemon = True
thread.start()

try:
    while True:
        if not data_queue:
            continue
        
        sorted_data = sorted(data_queue, key=lambda x: x[0])
        
        print(sorted_data)
        # Convert angle to radians and distance to radial distance
        r = [item[1] for item in sorted_data]
        theta = [np.radians(item[0]) for item in sorted_data]


        # Set the data for the scatter object
        scatter.set_offsets(np.c_[theta, r])

        # Redraw the plot
        plt.draw()
        plt.pause(0.001)
    
    
    
    # theta = []
    # r = []
    # old_angle = 0

    # # while not data_queue:
    # #     pass

    # for _ in range(1000):  # Continue until manually stopped
    #     run_running = True
    #     old_angle = 0
    #     startTime = time.time()
            
    #     while run_running:
    #         if data_queue:
    #             angle, distance, quality = data_queue.pop(0)
                
    #             theta.append(np.radians(angle))
    #             r.append(distance)
                
    #             print(f'Angle: {angle}, Distance: {distance}, Quality: {quality}')
                
    #             if angle < old_angle:
    #                 run_running = False
    #                 break
                
    #             old_angle = angle
                
    #     if theta[1] > 2:
    #         continue
            
    #     else:
    #         stopTime = time.time()
    #         if stopTime - startTime != 0:
    #             print(f'Hz: {1/(stopTime - startTime)}')

    #         # Set the data for the scatter object
    #         scatter.set_offsets(np.c_[theta, r])

    #         data_queue.clear()
    #         # # Redraw the plot
    #         plt.draw()
    #         plt.pause(0.001)  # Pause for a short time to update the plot

    #         # Reset the lists for the next revolution
    #         theta = []
    #         r = []
    #         angle = 0

finally:
    stop_cmd = b'\xA5\x25'
    ser.write(stop_cmd)
    
    # Close connection
    ser.close()
