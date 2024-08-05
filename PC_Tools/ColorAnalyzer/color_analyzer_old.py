import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import cv2

class FramePlayer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Frame Player")
        self.geometry("800x600")

        self.frames = []
        self.current_frame_index = 0
        self.playing = False

        self.canvas = tk.Canvas(self, width=640, height=480)
        self.canvas.pack()

        self.load_button = tk.Button(self, text="Load NPZ", command=self.load_npz)
        self.load_button.pack()

        self.play_button = tk.Button(self, text="Play", command=self.play_frames)
        self.play_button.pack()

        self.canvas.bind("<Motion>", self.on_mouse_move)

        self.hsv_label = tk.Label(self, text="HSV: ")
        self.hsv_label.pack()

        self.color_display = tk.Label(self, text="", width=10, height=2, bg="black")
        self.color_display.pack()

        self.after_id = None

    def load_npz(self):
        file_path = filedialog.askopenfilename(filetypes=[("NPZ files", "*.npz")])
        if not file_path:
            return
        
        npz_data = np.load(file_path)
        
        byte_frames = npz_data["raw_frames"]
        
        self.frames.clear()
        for frame in byte_frames:
            frame = np.frombuffer(frame, dtype=np.uint8).reshape((120, 213, 3))
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frames.append(rgb_frame)

        if self.frames:
            self.current_frame_index = 0
            self.show_frame(self.frames[0])
        else:
            messagebox.showerror("Error", "No frames found in the file.")

    def play_frames(self):
        if self.playing:
            self.playing = False
            self.play_button.config(text="Play")
            if self.after_id:
                self.after_cancel(self.after_id)
        else:
            self.playing = True
            self.play_button.config(text="Pause")
            self.play_next_frame()

    def play_next_frame(self):
        if not self.playing or not self.frames:
            return

        self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
        self.show_frame(self.frames[self.current_frame_index])

        self.after_id = self.after(50, self.play_next_frame)  # Adjust playback speed as needed

        # ctrg c copy

    
    def show_frame(self, frame):
        # Convert BGR to RGB
        image = Image.fromarray(frame)

        # Get current canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Resize the image to fit the canvas size
        self.resized_image = image.resize((canvas_width, canvas_height), Image.LANCZOS)

        self.tk_image = ImageTk.PhotoImage(self.resized_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)

    def on_mouse_move(self, event):
        if not self.frames or not hasattr(self, 'resized_image'):
            return

        x, y = event.x, event.y
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Ensure x and y are within bounds of the canvas
        if 0 <= x < canvas_width and 0 <= y < canvas_height:
            # Scale the coordinates to match the original frame size
            frame_width, frame_height = self.frames[0].shape[1], self.frames[0].shape[0]
            orig_x = int(x * frame_width / canvas_width)
            orig_y = int(y * frame_height / canvas_height)

            if 0 <= orig_x < frame_width and 0 <= orig_y < frame_height:
                frame = self.frames[self.current_frame_index]
                if len(frame.shape) == 3 and frame.shape[2] == 3:  # Check if the frame is RGB
                    rgb_pixel = frame[orig_y, orig_x]
                    hsv_pixel = cv2.cvtColor(np.uint8([[rgb_pixel]]), cv2.COLOR_RGB2HSV)[0][0]
                    self.hsv_label.config(text=f"HSV: {hsv_pixel}")
                    color = "#{:02x}{:02x}{:02x}".format(*rgb_pixel)
                    self.color_display.config(bg=color)


if __name__ == "__main__":
    app = FramePlayer()
    app.mainloop()
