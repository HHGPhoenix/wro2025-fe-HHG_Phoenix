import matplotlib.pyplot as plt
import numpy as np

def plot_polar(data):
    # Convert angles from degrees to radians
    angles = [np.deg2rad(d[0]) for d in data]
    distances = [d[1] for d in data]

    plt.ion()  # Turn on interactive mode
    plt.clf()  # Clear the current figure
    ax = plt.subplot(111, polar=True)
    ax.scatter(angles, distances)
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    plt.draw()  # Draw the figure
    plt.pause(0.001)  # Pause for a short period, allowing the figure to update

# Example data
with open("LIDAR_Data_Test\lidar_data.txt", "r") as f:
    lines = f.readlines()
    
    for line in lines:
        data = eval(line)
        
        plot_polar(data)