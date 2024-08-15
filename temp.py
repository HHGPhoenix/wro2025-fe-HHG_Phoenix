import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import importlib.util
import os

class PythonFileLoaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Python File Loader")

        # Scrolled text widget for code input
        self.text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=15)
        self.text_area.pack(padx=10, pady=10)

        # Button to select Python file
        self.select_file_button = tk.Button(root, text="Select Python File", command=self.load_python_file)
        self.select_file_button.pack(pady=5)

        # Button to run the code
        self.run_button = tk.Button(root, text="Run Code", command=self.run_code)
        self.run_button.pack(pady=5)

        # Label to display the output
        self.output_label = tk.Label(root, text="", wraplength=500, justify="left", anchor="w")
        self.output_label.pack(pady=10)

        # Variable to hold the loaded module
        self.loaded_module = None

    def load_python_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python Files", "*.py")])
        if file_path:
            try:
                module_name = os.path.splitext(os.path.basename(file_path))[0]
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.loaded_module = module
                messagebox.showinfo("Success", f"Module {module_name} loaded successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load module: {str(e)}")
                self.loaded_module = None

    def run_code(self):
        if not self.loaded_module:
            messagebox.showwarning("Warning", "No module loaded.")
            return

        code = self.text_area.get("1.0", tk.END)
        try:
            exec_locals = {}
            exec(code, globals(), exec_locals)
            output = exec_locals.get('output', 'No output variable defined.')
            self.output_label.config(text=str(output))
        except Exception as e:
            self.output_label.config(text=f"Error: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PythonFileLoaderApp(root)
    root.mainloop()
