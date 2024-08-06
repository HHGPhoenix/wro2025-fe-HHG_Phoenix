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
        self.drawing = False
        self.lines = []
        self.frame_rate = tk.IntVar(value=50)
        self.show_drawn_line_average = tk.BooleanVar(value=False)

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

        self.draw_line_button = ctk.CTkButton(self.right_frame, text="Draw Line", command=self.toggle_drawing)
        self.draw_line_button.pack(pady=5)

        self.clear_lines_button = ctk.CTkButton(self.right_frame, text="Clear All Lines", command=self.clear_lines)
        self.clear_lines_button.pack(pady=5)

        self.frame_slider = ctk.CTkSlider(self.right_frame, from_=0, to=1, command=self.on_frame_slider_change)
        self.frame_slider.set(0)
        self.frame_slider.pack(pady=5, fill="x")

        self.hsv_label = ctk.CTkLabel(self.right_frame, text="HSV:\n [    ]")
        self.hsv_label.pack(pady=5)

        self.show_drawn_line_average_button = ctk.CTkCheckBox(self.right_frame, text="Show Drawn Line Average", variable=self.show_drawn_line_average)
        self.show_drawn_line_average_button.pack(pady=5)

        self.color_display = ctk.CTkLabel(self.right_frame, text="", width=110, height=110, bg_color="black")
        self.color_display.pack(pady=5)

        self.all_hsv_values = []
        
        self.lowest_hsv_label = ctk.CTkLabel(self.right_frame, text="Lowest HSV:\n [    ]")
        self.lowest_hsv_label.pack(pady=5)

        self.highest_hsv_label = ctk.CTkLabel(self.right_frame, text="Highest HSV:\n [    ]")
        self.highest_hsv_label.pack(pady=5)

        self.frame_rate_label = ctk.CTkLabel(self.right_frame, text=f"Frame Rate: {self.frame_rate.get()}")
        self.frame_rate_label.pack(pady=5)

        self.frame_rate_slider = ctk.CTkSlider(self.right_frame, from_=10, to=120, command=self.on_frame_rate_change)
        self.frame_rate_slider.set(self.frame_rate.get())
        self.frame_rate_slider.pack(pady=5, fill="x")

        self.bind("<Control-o>", self.load_npz)

        self.bind("<Motion>", self.on_mouse_move)
        self.bind("<Control-c>", self.copy_hsv_to_clipboard)

        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.after_id = None
        self.current_hsv = None
        self.line_start = None

    def on_frame_rate_change(self, value):
        self.frame_rate.set(int(value))
        self.frame_rate_label.configure(text=f"Frame Rate: {self.frame_rate.get()}")

    def load_npz(self):
        file_path = filedialog.askopenfilename(filetypes=[("NPZ files", "*.npz")])
        if not file_path:
            return
        
        npz_data = np.load(file_path)
        
        byte_frames = npz_data["raw_frames"]
        
        self.frames.clear()
        for frame in byte_frames:
            frame = np.frombuffer(frame, dtype=np.uint8).reshape((110, 213, 3))
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frames.append(rgb_frame)

        if self.frames:
            self.current_frame_index = 0
            self.show_frame(self.frames[0])
            self.frame_slider.configure(to=len(self.frames) - 1)
        else:
            messagebox.showerror("Error", "No frames found in the file.")

    def play_frames(self):
        if self.playing:
            self.playing = False
            self.play_button.configure(text="Play")
            if self.after_id:
                self.after_cancel(self.after_id)
        else:
            self.playing = True
            self.play_button.configure(text="Pause")
            self.play_next_frame()

    def play_next_frame(self):
        if not self.playing or not self.frames:
            return

        self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
        self.show_frame(self.frames[self.current_frame_index])
        self.frame_slider.set(self.current_frame_index)
        self.after_id = self.after(int(1000 / self.frame_rate.get()), self.play_next_frame)  # Adjust playback speed as needed

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

        # Redraw all lines
        for line in self.lines:
            self.canvas.create_line(line, fill="red", width=2)

    def on_frame_slider_change(self, value):
        self.current_frame_index = int(value)
        self.show_frame(self.frames[self.current_frame_index])

    def on_mouse_move(self, event):
        if not self.frames or not hasattr(self, 'resized_image'):
            return

        x, y = event.x, event.y
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if not self.show_drawn_line_average.get():
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
                        self.hsv_label.configure(text=f"HSV:\n {hsv_pixel}")
                        color = "#{:02x}{:02x}{:02x}".format(*rgb_pixel)
                        self.color_display.configure(bg_color=color)
        else:
            # calculate average HSV value along the drawn lines self.lines

            if not self.lines:
                return
            
            average_hsv = self.calculate_average_hsv()
            if average_hsv is not None:
                self.current_hsv = average_hsv
                self.hsv_label.configure(text=f"Average HSV:\n {average_hsv}")
                color = "#{:02x}{:02x}{:02x}".format(*cv2.cvtColor(np.uint8([[average_hsv]]), cv2.COLOR_HSV2RGB)[0][0])
                self.color_display.configure(bg_color=color)
            
    def calculate_average_hsv(self):
        if not self.all_hsv_values:
            return None
    
        hsv_values = np.array(self.all_hsv_values)
        average_hsv = hsv_values.mean(axis=0)
        rounded_average_hsv = np.round(average_hsv, 2)
    
        return rounded_average_hsv.tolist()

    def copy_hsv_to_clipboard(self, event):
        if self.current_hsv is not None:
            hsv_string = f"{self.current_hsv}"
            self.clipboard_clear()
            self.clipboard_append(hsv_string)
            messagebox.showinfo("HSV Copied", f"Copied HSV value to clipboard: {hsv_string}")

    def toggle_drawing(self):
        self.drawing = not self.drawing
        self.draw_line_button.configure(text="Stop Drawing" if self.drawing else "Draw Line")

    def on_canvas_click(self, event):
        if not self.drawing:
            return

        x, y = event.x, event.y
        if self.line_start is None:
            self.line_start = (x, y)
        else:
            line = (self.line_start[0], self.line_start[1], x, y)
            self.lines.append(line)
            self.canvas.create_line(line, fill="white", width=6)
            self.canvas.create_line(line, fill="red", width=4)
            self.calculate_hsv_along_line(line)
            self.line_start = None

    def calculate_hsv_along_line(self, line):
        if getattr(self, 'frames', None) is None or not self.frames:
            return
        
        x1, y1, x2, y2 = line
        frame_width, frame_height = self.frames[0].shape[1], self.frames[0].shape[0]
        canvas_width, canvas_height = self.canvas.winfo_width(), self.canvas.winfo_height()

        x1_orig = int(x1 * frame_width / canvas_width)
        y1_orig = int(y1 * frame_height / canvas_height)
        x2_orig = int(x2 * frame_width / canvas_width)
        y2_orig = int(y2 * frame_height / canvas_height)

        num_points = max(abs(x2_orig - x1_orig), abs(y2_orig - y1_orig))
        x_values = np.linspace(x1_orig, x2_orig, num_points, dtype=int)
        y_values = np.linspace(y1_orig, y2_orig, num_points, dtype=int)

        frame = self.frames[self.current_frame_index]
        for x, y in zip(x_values, y_values):
            rgb_pixel = frame[y, x]
            hsv_pixel = cv2.cvtColor(np.uint8([[rgb_pixel]]), cv2.COLOR_RGB2HSV)[0][0]
            self.all_hsv_values.append(hsv_pixel)

        self.update_hsv_values()

    def update_hsv_values(self):
        if not self.all_hsv_values:
            return

        hsv_values = np.array(self.all_hsv_values)
        lowest_hsv = hsv_values.min(axis=0)
        highest_hsv = hsv_values.max(axis=0)

        self.lowest_hsv_label.configure(text=f"Lowest HSV:\n {lowest_hsv.tolist()}")
        self.highest_hsv_label.configure(text=f"Highest HSV:\n {highest_hsv.tolist()}")

    def clear_lines(self):
        self.lines.clear()
        self.all_hsv_values.clear()
        self.canvas.delete("all")
        if self.frames:
            self.show_frame(self.frames[self.current_frame_index])
        
        self.lowest_hsv_label.configure(text="Lowest HSV:\n [    ]")
        self.highest_hsv_label.configure(text="Highest HSV:\n [    ]")

if __name__ == "__main__":
    app = FramePlayer()
    app.mainloop()
