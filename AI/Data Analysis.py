import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import pandas as pd  # Assuming controller data is in a format pandas can read

def analyze_controller_data(controller_data):
    plt.hist(controller_data, bins=30)
    plt.title('Distribution of Controller Commands')
    plt.xlabel('Controller Command')
    plt.ylabel('Frequency')
    plt.show()

def load_and_analyze_data():
    file_path = filedialog.askopenfilename()  # Show an "Open" dialog box and return the path to the selected file
    if file_path:  # If a file was selected
        controller_data = pd.read_csv(file_path)  # Assuming the data is in CSV format
        analyze_controller_data(controller_data)

# Set up the main application window
root = tk.Tk()
root.title("Controller Data Analysis")

# Add a button that calls load_and_analyze_data when clicked
analyze_button = tk.Button(root, text="Load and Analyze Controller Data", command=load_and_analyze_data)
analyze_button.pack()

# Start the Tkinter event loop
root.mainloop()