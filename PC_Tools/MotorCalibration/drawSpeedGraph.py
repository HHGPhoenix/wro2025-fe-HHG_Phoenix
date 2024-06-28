import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Open the serial port
ser = serial.Serial('COM5', 921600)

# Send START message
# ser.write(b'START\n')
ser.write('SPEED 100\n'.encode())
# ser.write(b'KD1.1\n')
# ser.write(b'KP1.6\n')

# Initialize a list to store CS values and Out values
cs_values = []
out_values = []

# Initialize the figure and two subplots
fig, (ax1, ax2) = plt.subplots(2, sharex=True)

# Initialize two empty lines
line1, = ax1.plot([], [], color='blue')
line2, = ax2.plot([], [], color='red')

# Function to update the graph
def update(i):
    # Read a line from the serial port
    line = ser.readline().decode().strip()

    if "CS" in line:
        # Split the line into CS value and time stamp
        cs = line.split(': ')[1]

        # Convert CS value to integer
        cs = float(cs)

        if cs > 6000:
            return

        # Append CS value to the list
        cs_values.append(cs)

        # Clear the first line and redraw it with the updated CS values
        line1.set_data(range(len(cs_values)), cs_values)

    elif "Out" in line:
        out = line.split(': ')[1]
        out = float(out)
        if out < 0:
            out = 0

        out_values.append(out)

        # Clear the second line and redraw it with the updated Out values
        line2.set_data(range(len(out_values)), out_values)
        
    elif "D" in line:
        print(line)

    # Adjust the x-axis limit to accommodate the new data
    ax1.set_xlim(0, max(len(cs_values), len(out_values)))

    # Adjust the y-axis limits for each subplot
    if cs_values:
        ax1.set_ylim(0, max(cs_values) + 20)
    else:
        ax1.set_ylim(0, 1)  # Default value
    
    if out_values:
        ax2.set_ylim(0, max(out_values) + 20)
    else:
        ax2.set_ylim(0, 1)  # Default value

    ax1.set_ylabel('CS Value')
    ax2.set_ylabel('Out Value')
    ax1.grid(True)
    ax2.grid(True)

# Use FuncAnimation to update the graph every 1ms
ani = FuncAnimation(fig, update, interval=1)

plt.show()