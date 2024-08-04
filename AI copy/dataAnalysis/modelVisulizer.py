import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import tensorflow as tf
from tensorflow.keras.utils import plot_model
import os


def plot_keras_model(h5_model_path, output_image_path="model.png", show_shapes=False, show_dtype=False, show_layer_names=False, rankdir="TB", expand_nested=False, dpi=200, show_layer_activations=False, show_trainable=False, **kwargs):
    """
    Plots the structure of a Keras model and saves it as an image.
    
    Parameters:
    - h5_model_path (str): Path to the .h5 model file.
    - output_image_path (str): Path to save the plotted model image. Default is "model.png".
    - show_shapes (bool): Whether to display shape information. Default is False.
    - show_dtype (bool): Whether to display data type information. Default is False.
    - show_layer_names (bool): Whether to display layer names. Default is False.
    - rankdir (str): Direction of the graph. Default is "TB" (Top to Bottom).
    - expand_nested (bool): Whether to expand nested models. Default is False.
    - dpi (int): Dots per inch for the image. Default is 200.
    - show_layer_activations (bool): Whether to show layer activations. Default is False.
    - show_trainable (bool): Whether to show trainable parameters. Default is False.
    - **kwargs: Additional keyword arguments for keras.utils.plot_model.
    """
    
    # Load the Keras model from the .h5 file
    model = tf.keras.models.load_model(h5_model_path)
    
    # Plot the model and save to file
    plot_model(
        model,
        to_file=output_image_path,
        show_shapes=show_shapes,
        show_dtype=show_dtype,
        show_layer_names=show_layer_names,
        rankdir=rankdir,
        expand_nested=expand_nested,
        dpi=dpi,
        show_layer_activations=show_layer_activations,
        **kwargs
    )
    print(f"Model structure saved to {output_image_path}")

def browse_file():
    file_path = filedialog.askopenfilename(filetypes=[("H5 files", "*.h5")])
    if file_path:
        entry_model_path.delete(0, tk.END)
        entry_model_path.insert(0, file_path)

def on_submit():
    model_path = entry_model_path.get()
    output_path = entry_output_path.get()
    show_shapes = var_show_shapes.get()
    show_dtype = var_show_dtype.get()
    show_layer_names = var_show_layer_names.get()
    rankdir = combo_rankdir.get()
    expand_nested = var_expand_nested.get()
    dpi = int(entry_dpi.get())
    show_layer_activations = var_show_layer_activations.get()
    show_trainable = var_show_trainable.get()

    if model_path and output_path:
        plot_keras_model(
            model_path, output_path, show_shapes, show_dtype, show_layer_names,
            rankdir, expand_nested, dpi, show_layer_activations, show_trainable
        )
        messagebox.showinfo("Success", f"Model structure saved to {output_path}")
    else:
        messagebox.showwarning("Input Error", "Please provide both model path and output path.")

# Set up the GUI
root = tk.Tk()
root.title("Keras Model Plotter")

frame = ttk.Frame(root, padding=10)
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

ttk.Label(frame, text="Model Path:").grid(row=0, column=0, sticky=tk.W)
entry_model_path = ttk.Entry(frame, width=50)
entry_model_path.grid(row=0, column=1, sticky=(tk.W, tk.E))
ttk.Button(frame, text="Browse", command=browse_file).grid(row=0, column=2, sticky=tk.E)

ttk.Label(frame, text="Output Path:").grid(row=1, column=0, sticky=tk.W)
entry_output_path = ttk.Entry(frame, width=50)
entry_output_path.grid(row=1, column=1, sticky=(tk.W, tk.E))

var_show_shapes = tk.BooleanVar()
ttk.Checkbutton(frame, text="Show Shapes", variable=var_show_shapes).grid(row=2, column=0, sticky=tk.W)

var_show_dtype = tk.BooleanVar()
ttk.Checkbutton(frame, text="Show Dtype", variable=var_show_dtype).grid(row=2, column=1, sticky=tk.W)

var_show_layer_names = tk.BooleanVar()
ttk.Checkbutton(frame, text="Show Layer Names", variable=var_show_layer_names).grid(row=2, column=2, sticky=tk.W)

ttk.Label(frame, text="Rankdir:").grid(row=3, column=0, sticky=tk.W)
combo_rankdir = ttk.Combobox(frame, values=["TB", "LR", "BT", "RL"])
combo_rankdir.grid(row=3, column=1, sticky=(tk.W, tk.E))
combo_rankdir.set("TB")

var_expand_nested = tk.BooleanVar()
ttk.Checkbutton(frame, text="Expand Nested", variable=var_expand_nested).grid(row=4, column=0, sticky=tk.W)

ttk.Label(frame, text="DPI:").grid(row=4, column=1, sticky=tk.W)
entry_dpi = ttk.Entry(frame, width=10)
entry_dpi.grid(row=4, column=2, sticky=tk.W)
entry_dpi.insert(0, "200")

var_show_layer_activations = tk.BooleanVar()
ttk.Checkbutton(frame, text="Show Layer Activations", variable=var_show_layer_activations).grid(row=5, column=0, sticky=tk.W)

var_show_trainable = tk.BooleanVar()
ttk.Checkbutton(frame, text="Show Trainable", variable=var_show_trainable).grid(row=5, column=1, sticky=tk.W)

ttk.Button(frame, text="Submit", command=on_submit).grid(row=6, column=0, columnspan=3)

root.mainloop()
