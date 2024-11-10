import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import tensorflow as tf

# Initialize the customtkinter theme
ctk.set_appearance_mode("System")  # Options: "System" (default), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Options: "blue" (default), "green", "dark-blue"

def convert_to_tflite(input_file, quantization_type="dynamic_range"):
    output_file = os.path.splitext(input_file)[0] + ".tflite"
    model = tf.keras.models.load_model(input_file)
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # Set the converter settings to handle TensorList ops
    converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS, tf.lite.OpsSet.SELECT_TF_OPS]
    converter._experimental_lower_tensor_list_ops = False

    # Apply quantization based on the selected type
    if quantization_type == "dynamic_range":
        # Dynamic range quantization
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
    elif quantization_type == "float16":
        # Float16 quantization
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.target_spec.supported_types = [tf.float16]
    elif quantization_type == "full_integer":
        # Full integer quantization
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        # You need to provide a representative dataset for full integer quantization
        def representative_dataset():
            for _ in range(100):
                # Generate a representative dataset sample
                # Replace with actual input data from your dataset
                yield [tf.random.normal([1, *model.input_shape[1:]])]
        converter.representative_dataset = representative_dataset
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.uint8
        converter.inference_output_type = tf.uint8

    # Convert the model
    tflite_model = converter.convert()

    with open(output_file, 'wb') as f:
        f.write(tflite_model)

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
            # Choose quantization type here: "dynamic_range", "float16", or "full_integer"
            quantization_type = "dynamic_range"
            output_file = convert_to_tflite(input_file, quantization_type)
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
