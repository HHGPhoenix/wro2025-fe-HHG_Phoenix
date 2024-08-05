import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import cv2

class FramePlayer(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Frame Player")
        self.geometry("1000x600")

        self.frames = []
        self.current_frame_index = 0
        self.playing = False

        # Create main frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create left frame for canvas
        self.left_frame = ctk.CTkFrame(self.main_frame)
        self.left_frame.pack(side="left", fill="both", expand=True)

        # Create right frame for controls
        self.right_frame = ctk.CTkFrame(self.main_frame)
        self.right_frame.pack(side="right", fill="y", padx=10, pady=10)

        self.canvas = tk.Canvas(self.left_frame, width=640, height=480)
        self.canvas.pack(fill="both", expand=True)

        self.load_button = ctk.CTkButton(self.right_frame, text="Load NPZ", command=self.load_npz)
        self.load_button.pack(pady=5)

        self.play_button = ctk.CTkButton(self.right_frame, text="Play", command=self.play_frames)
        self.play_button.pack(pady=5)

        self.hsv_label = ctk.CTkLabel(self.right_frame, text="HSV: ")
        self.hsv_label.pack(pady=5)

        self.color_display = ctk.CTkLabel(self.right_frame, text="", width=20, height=10, bg_color="black")
        self.color_display.pack(pady=5)

        self.bind("<Motion>", self.on_mouse_move)
        self.bind("<Control-c>", self.copy_hsv_to_clipboard)

        self.after_id = None
        self.current_hsv = None

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
                    self.current_hsv = hsv_pixel  # Store the current HSV value
                    self.hsv_label.config(text=f"HSV: {hsv_pixel}")
                    color = "#{:02x}{:02x}{:02x}".format(*rgb_pixel)
                    self.color_display.config(bg=color)

    def copy_hsv_to_clipboard(self, event):
        if self.current_hsv is not None:
            hsv_string = f"{self.current_hsv}"
            self.clipboard_clear()
            self.clipboard_append(hsv_string)
            messagebox.showinfo("HSV Copied", f"Copied HSV value to clipboard: {hsv_string}")


if __name__ == "__main__":
    app = FramePlayer()
    app.mainloop()
