import json
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy import stats
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

with open("LIDAR_Data_Test\lidar_data.txt", "r") as f:
    lines = f.readlines()
    
    for line in lines:
        # Line is an array not json [(angle, distance, intensity), ...]
        data = eval(line)
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(data, columns=["angle", "distance", "intensity"])

        # Filter out invalid points (distance and intensity zero)
        df = df[(df["distance"] != 0)]
        df["angle"] = (df["angle"] - 90) % 360

        # # Remove outliers based on Z-score
        # df = df[(np.abs(stats.zscore(df)) < 3).all(axis=1)]

        # Sort the data by angle
        df = df.sort_values("angle")

        # Define the desired angles (one point per angle from 0 to 359)
        desired_angles = np.arange(0, 360, 0.5)

        # Interpolate distance and intensity for missing angles, use nearest for fill_value
        interp_distance = interp1d(df["angle"], df["distance"], kind="linear", bounds_error=False, fill_value=(df["distance"].iloc[0], df["distance"].iloc[-1]))
        interp_intensity = interp1d(df["angle"], df["intensity"], kind="linear", bounds_error=False, fill_value=(df["intensity"].iloc[0], df["intensity"].iloc[-1]))

        # Generate the interpolated values
        interpolated_distances = interp_distance(desired_angles)
        interpolated_intensities = interp_intensity(desired_angles)

        # Create the new list with interpolated data
        interpolated_data = list(zip(desired_angles, interpolated_distances, interpolated_intensities))

        # Convert to DataFrame for easier manipulation
        df_interpolated = pd.DataFrame(interpolated_data, columns=["angle", "distance", "intensity"])

        # Remove data from 110 to 250 degrees
        df_interpolated = df_interpolated[(df_interpolated["angle"] < 110) | (df_interpolated["angle"] > 250)]

        # Plot the filtered interpolated data
        plot_polar(df_interpolated.values.tolist())