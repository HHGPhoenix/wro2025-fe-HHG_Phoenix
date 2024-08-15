import tkinter as tk
from tkinter import filedialog
import numpy as np
from PIL import Image, ImageTk
import cv2

class ImageLoaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Loader")
        
        self.load_button = tk.Button(root, text="Load File", command=self.load_file)
        self.load_button.pack()
        
        self.canvas1 = tk.Canvas(root)
        self.canvas1.pack(side=tk.LEFT)
        
        self.canvas2 = tk.Canvas(root)
        self.canvas2.pack(side=tk.RIGHT)

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("npz files", "*.npz")])
        if file_path:
            data = np.load(file_path)
            array1 = data['raw_frames']
            array2 = data['simplified_frames']
            
            # Convert frames to RGB
            array1_rgb = [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) for frame in array1]
            array2_rgb = [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) for frame in array2]
            
            self.display_images(array1_rgb, array2_rgb)

    def display_images(self, array1, array2):
        self.frames1 = [ImageTk.PhotoImage(Image.fromarray(frame)) for frame in array1]
        self.frames2 = [ImageTk.PhotoImage(Image.fromarray(frame)) for frame in array2]
        self.current_frame = 0
        self.update_frames()

    def update_frames(self):
        if self.current_frame < len(self.frames1) and self.current_frame < len(self.frames2):
            self.canvas1.create_image(0, 0, anchor=tk.NW, image=self.frames1[self.current_frame])
            self.canvas2.create_image(0, 0, anchor=tk.NW, image=self.frames2[self.current_frame])
            self.current_frame += 1
            self.root.after(100, self.update_frames)  # 33ms delay for ~30fps

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageLoaderApp(root)
    root.mainloop()