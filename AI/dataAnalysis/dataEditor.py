import numpy as np
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import time
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import signal
import chime

class LiDARCameraVisualizer:
    def __init__(self):
        self.lidar_data = None
        self.camera_data = None
        self.controller_data = None
        self.counter_data = None
        self.current_frame = 0
        self.marked_areas = []
        self.playing = False
        self.fps = 10  # Default FPS value
        self.data_loaded = False
        
        chime.theme('big-sur')

        self.root = ctk.CTk()
        self.root.title("LiDAR and Camera Data Visualizer")
        self.root.minsize(1500, 600)
        self.root.geometry("1600x600")

        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self.control_frame = ctk.CTkFrame(self.main_frame, width=300)  # Increased width
        self.control_frame.pack(side="right", fill="y", padx=10, pady=10)

        self.vis_frame = ctk.CTkFrame(self.main_frame)
        self.vis_frame.pack(side="left", fill="both", expand=True)

        self.plot_frame = ctk.CTkFrame(self.vis_frame)
        self.plot_frame.pack(side="top", fill="both", expand=True)

        self.plot_frame.grid_rowconfigure(0, weight=1)
        self.plot_frame.grid_columnconfigure(0, weight=1)
        self.plot_frame.grid_columnconfigure(1, weight=1)

        self.lidar_frame = ctk.CTkFrame(self.plot_frame, border_color="red", border_width=0)
        self.lidar_frame.grid(row=0, column=0, sticky="nsew")

        self.camera_frame = ctk.CTkFrame(self.plot_frame, border_color="red", border_width=0)
        self.camera_frame.grid(row=0, column=1, sticky="nsew")

        self.timeline_frame = ctk.CTkFrame(self.vis_frame)
        self.timeline_frame.pack(side="bottom", fill="x")
        
        # Added Frame Slider Label
        self.frame_slider_label = ctk.CTkLabel(self.timeline_frame, text="Frame Slider")
        self.frame_slider_label.pack(pady=(5, 0))
        
        # Moved frame_slider to timeline_frame and adjusted size
        self.frame_slider = ctk.CTkSlider(self.timeline_frame, from_=0, to=1, command=self.on_slider_move, orientation="horizontal")
        self.frame_slider.pack(fill="x", padx=20, pady=(0, 5))
        self.frame_slider.set(0)
        
        # Added current frame label
        self.current_frame_label = ctk.CTkLabel(self.timeline_frame, text=f"Current Frame: {self.current_frame}")
        self.current_frame_label.pack(pady=(0, 5))

        self.timeline_canvas = ctk.CTkCanvas(self.timeline_frame, height=50, bg="#8b8f94")
        self.timeline_canvas.pack(fill="x", padx=10, pady=(0, 10))

        self.load_button = ctk.CTkButton(self.control_frame, text="Load .npz File", command=self.load_file)
        self.load_button.pack(pady=10)

        self.play_button = ctk.CTkButton(self.control_frame, text="Play", command=self.play_frames)
        self.play_button.pack(pady=10)

        self.pause_button = ctk.CTkButton(self.control_frame, text="Pause", command=self.pause_frames)
        self.pause_button.pack(pady=10)

        self.fps_label = ctk.CTkLabel(self.control_frame, text=f"FPS: {int(self.fps)}")
        self.fps_label.pack(pady=10)

        self.fps_slider = ctk.CTkSlider(self.control_frame, from_=1, to=60, number_of_steps=59, command=self.on_fps_slider_move)
        self.fps_slider.pack(fill="x", padx=10)
        self.fps_slider.set(self.fps)

        self.mark_start_button = ctk.CTkButton(self.control_frame, text="Mark Start", command=self.mark_start)
        self.mark_start_button.pack(pady=10)

        self.mark_end_button = ctk.CTkButton(self.control_frame, text="Mark End", command=self.mark_end)
        self.mark_end_button.pack(pady=10)

        self.delete_area_button = ctk.CTkButton(self.control_frame, text="Delete Marked Areas", command=self.delete_marked_areas)
        self.delete_area_button.pack(pady=10)

        self.save_button = ctk.CTkButton(self.control_frame, text="Save Edited Data", command=self.save_file)
        self.save_button.pack(pady=10)
        
        self.mode = ctk.StringVar(value="remove")

        # Mode Selection
        self.mode_label = ctk.CTkLabel(self.control_frame, text="Select Mode")
        self.mode_label.pack(pady=(20, 5))

        self.remove_mode = ctk.CTkRadioButton(
            self.control_frame, text="Remove Marked Area", variable=self.mode, value="remove"
        )
        self.remove_mode.pack(pady=5)

        self.delete_mode = ctk.CTkRadioButton(
            self.control_frame, text="Delete Data in Marked Area", variable=self.mode, value="delete"
        )
        self.delete_mode.pack(pady=5)

        self.lidar_fig = Figure(figsize=(5, 4), facecolor='black', edgecolor='black')
        self.lidar_fig.patch.set_facecolor('#222222')

        self.lidar_ax = self.lidar_fig.add_subplot(111, polar=True)
        self.lidar_ax.set_facecolor('#222222')
        self.lidar_ax.tick_params(axis='x', colors='white')
        self.lidar_ax.tick_params(axis='y', colors='white')

        for spine in self.lidar_ax.spines.values():
            spine.set_edgecolor('white')

        self.lidar_canvas = FigureCanvasTkAgg(self.lidar_fig, master=self.lidar_frame)
        self.lidar_canvas.draw()
        self.lidar_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.lidar_canvas.get_tk_widget().configure(bg='#222222', highlightthickness=0, bd=0)

        self.camera_fig = Figure(figsize=(5, 4), facecolor='black', edgecolor='black')
        self.camera_fig.patch.set_facecolor('#222222')

        self.camera_ax = self.camera_fig.add_subplot(111)
        self.camera_ax.set_facecolor('#222222')
        self.camera_ax.tick_params(axis='x', colors='white')
        self.camera_ax.tick_params(axis='y', colors='white')

        for spine in self.camera_ax.spines.values():
            spine.set_edgecolor('white')

        self.camera_canvas = FigureCanvasTkAgg(self.camera_fig, master=self.camera_frame)
        self.camera_canvas.draw()
        self.camera_canvas.get_tk_widget().pack(fill="both", expand=True)
        self.camera_canvas.get_tk_widget().configure(bg='#222222', highlightthickness=0, bd=0)

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        signal.signal(signal.SIGINT, self.on_closing)
        self.root.mainloop()

    def on_slider_move(self, frame):
        if not self.data_loaded:
            return
        self.current_frame = int(float(frame))
        self.update_frame(self.current_frame)
        self.current_frame_label.configure(text=f"Current Frame: {self.current_frame}")

    def on_fps_slider_move(self, value):
        self.fps = float(value)
        self.fps_label.configure(text=f"FPS: {int(round(self.fps))}")

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("NPZ files", "*.npz")])
        if not file_path:
            return

        data = np.load(file_path)
        self.lidar_data = data['lidar_data']
        self.camera_data = data['simplified_frames']
        self.controller_data = data['controller_data']
        self.counter_data = data['counters']
        
        self.data_loaded = True

        self.frame_slider.configure(to=len(self.lidar_data) - 1)
        self.update_frame(0)
        self.draw_timeline()

    def update_frame(self, frame):
        self.current_frame = int(float(frame))
        lidar_points = self.lidar_data[self.current_frame]
        self.display_lidar(lidar_points)
        camera_image = self.camera_data[self.current_frame]
        self.display_camera(camera_image)
        self.frame_slider.set(self.current_frame)
        self.draw_timeline()
        self.current_frame_label.configure(text=f"Current Frame: {self.current_frame}")
        print(f"Controller Data: {self.controller_data[self.current_frame]}")
        print(f"Counter Data: {self.counter_data[self.current_frame]}")

    def display_lidar(self, lidar_points):
        self.lidar_ax.clear()
        angles = lidar_points[:, 0]
        distances = lidar_points[:, 1]
        angles_rad = np.deg2rad(angles)
        mirrored_angles_rad = -angles_rad  # Negate the angles to mirror on the y-axis
        self.lidar_ax.scatter(mirrored_angles_rad, distances, color='#39FF14', s=10)
        self.lidar_ax.set_facecolor('#222222')
        self.lidar_ax.tick_params(axis='x', colors='white')
        self.lidar_ax.tick_params(axis='y', colors='white')
        self.lidar_ax.set_theta_offset(np.pi / 2)
        self.lidar_ax.set_theta_direction(-1)
        self.lidar_ax.set_title(f"LiDAR Frame {self.current_frame}", color='white')
        for spine in self.lidar_ax.spines.values():
            spine.set_edgecolor('white')
        try:
            self.lidar_canvas.draw()
        except AttributeError:
            pass

    def display_camera(self, image):
        self.camera_ax.clear()
        self.camera_ax.imshow(image, cmap="gray")
        self.camera_ax.set_title(f"Camera Frame {self.current_frame}", color='white')
        self.camera_ax.axis("off")
        self.camera_canvas.draw()

    def mark_start(self):
        if not self.data_loaded:
            return
        self.mark_start_frame = self.current_frame
        # messagebox.showinfo("Marking", f"Marked start frame {self.current_frame}.")
        chime.success()

    def mark_end(self):
        if not self.data_loaded:
            return
        if hasattr(self, 'mark_start_frame'):
            start = self.mark_start_frame
            end = self.current_frame
            self.marked_areas.append((min(start, end), max(start, end)))
            self.draw_timeline()
            # messagebox.showinfo("Marking", f"Marked area from frame {min(start, end)} to {max(start, end)}.")
            chime.success()
            del self.mark_start_frame
        else:
            messagebox.showerror("Error", "Please mark a start frame first.")

    def draw_timeline(self):
        self.timeline_canvas.delete("all")
        width = self.timeline_canvas.winfo_width()
        height = self.timeline_canvas.winfo_height()
        total_frames = len(self.lidar_data)
        self.timeline_canvas.create_rectangle(0, 0, width, height, fill="#CCCCCC")
        current_x = (self.current_frame / total_frames) * width
        self.timeline_canvas.create_line(current_x, 0, current_x, height, fill="blue")
        for area in self.marked_areas:
            start_x = (area[0] / total_frames) * width
            end_x = (area[1] / total_frames) * width
            self.timeline_canvas.create_rectangle(start_x, 0, end_x, height, fill="red", stipple="gray25", tags="marked_area")
            self.timeline_canvas.tag_bind("marked_area", "<Button-1>", self.on_marked_area_click)

    def on_marked_area_click(self, event):
        x = event.x
        width = self.timeline_canvas.winfo_width()
        total_frames = len(self.lidar_data)
        clicked_frame = int((x / width) * total_frames)
        for area in self.marked_areas:
            start_x = (area[0] / total_frames) * width
            end_x = (area[1] / total_frames) * width
            if start_x <= x <= end_x:
                if self.mode.get() == "remove":
                    self.marked_areas.remove(area)
                    self.draw_timeline()
                    messagebox.showinfo("Remove Mark", f"Removed marked area from frame {area[0]} to {area[1]}.")
                elif self.mode.get() == "delete":
                    response = messagebox.askyesno("Delete Data", f"Delete data from frame {area[0]} to {area[1]}?")
                    if response:
                        self.delete_frames(area[0], area[1])
                        self.marked_areas.remove(area)
                        self.draw_timeline()
                break

    def delete_frames(self, start, end):
        self.lidar_data = np.delete(self.lidar_data, np.s_[start:end+1], axis=0)
        self.camera_data = np.delete(self.camera_data, np.s_[start:end+1], axis=0)
        self.controller_data = np.delete(self.controller_data, np.s_[start:end+1], axis=0)
        self.counter_data = np.delete(self.counter_data, np.s_[start:end+1], axis=0)
        self.frame_slider.configure(to=len(self.lidar_data) - 1)
        self.update_frame(min(start, len(self.lidar_data) - 1))
        messagebox.showinfo("Delete", f"Deleted frames from {start} to {end}.")

    def delete_marked_areas(self):
        for area in sorted(self.marked_areas, reverse=True):
            self.delete_frames(area[0], area[1])
        self.marked_areas = []
        self.draw_timeline()
        messagebox.showinfo("Delete", "Deleted all marked areas.")

    def save_file(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".npz", filetypes=[("NPZ files", "*.npz")])
        if not save_path:
            return
        np.savez(save_path, lidar_data=self.lidar_data, simplified_frames=self.camera_data,
                 controller_data=self.controller_data, counters=self.counter_data)
        messagebox.showinfo("Save", f"Data saved to {save_path}")

    def _play_frames(self):
        while self.playing and self.current_frame < len(self.lidar_data) - 1:
            self.current_frame += 1
            self.update_frame(self.current_frame)
            self.draw_timeline()
            time.sleep(1.0 / self.fps)  # Adjusted sleep time based on FPS
        self.playing = False

    def play_frames(self):
        if not self.data_loaded:
            return
        if not self.playing:
            self.playing = True
            threading.Thread(target=self._play_frames, daemon=False).start()

    def pause_frames(self):
        self.playing = False

    def on_closing(self, *args):
        self.playing = False
        self.root.destroy()

if __name__ == "__main__":
    LiDARCameraVisualizer()