import customtkinter as ctk
from tkinter import filedialog, messagebox
import os

# Initialize the customtkinter theme
ctk.set_appearance_mode("System")  # Options: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Options: "blue" (default), "green", "dark-blue"

# Function to convert file to .tflite format
def convert_to_tflite(input_file):
    # Example of conversion process - replace this with actual conversion logic
    output_file = os.path.splitext(input_file)[0] + ".tflite"
    with open(input_file, 'rb') as f_in, open(output_file, 'wb') as f_out:
        f_out.write(f_in.read())  # Example of copying content (replace with actual conversion logic)
    return output_file

# Function to open file dialog and select a file
def select_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        file_label.configure(text=f"Selected File: {file_path}")
        convert_button.configure(state=ctk.NORMAL)
        selected_file.set(file_path)

# Function to perform conversion on button click
def convert():
    input_file = selected_file.get()
    if input_file:
        try:
            output_file = convert_to_tflite(input_file)
            messagebox.showinfo("Conversion Success", f"File converted successfully: {output_file}")
        except Exception as e:
            messagebox.showerror("Conversion Error", f"An error occurred: {e}")

# Create the main application window
app = ctk.CTk()
app.title("File Converter")
app.geometry("800x200")


# Selected file path
selected_file = ctk.StringVar()

# Select File Button
select_button = ctk.CTkButton(app, text="Select File", command=select_file)
select_button.pack(pady=10)

# Label to show the selected file
file_label = ctk.CTkLabel(app, text="No file selected")
file_label.pack()

# Convert Button (initially disabled)
convert_button = ctk.CTkButton(app, text="Convert", command=convert, state=ctk.DISABLED)
convert_button.pack(pady=10)

# Run the application
app.mainloop()
