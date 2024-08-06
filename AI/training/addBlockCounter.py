import numpy as np
import customtkinter as ctk
import cv2
from tkinter import filedialog
import os
import tkinter.messagebox
import tkinter as tk

def set_ranges(self):
    self.lower_green = np.array([55, 50, 50])
    self.upper_green = np.array([75, 120, 83])

    self.lower_red1 = np.array([0, 120, 90])
    self.upper_red1 = np.array([1, 225, 185])

    self.lower_red2 = np.array([175, 120, 90])
    self.upper_red2 = np.array([180, 225, 185])
    
    self.lower_black = np.array([15, 0, 0])
    self.upper_black = np.array([165, 85, 60])

class AddBlockCounter(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.output_file_path = None
        self.output_file_uuid = None
        self.data_loaded = False
        self.automatic_assign_var = tk.BooleanVar()
        self.frame_file_dir = None
        
        set_ranges(self)
        
        self.kernel = np.ones((5, 5), np.uint8)
        
        self.title('Add Block Counter')
        self.geometry('1000x600')
        self.configure(fg_color="#2e2e2e")

        self.main_frame = ctk.CTkFrame(self, width=1000, height=600)
        self.main_frame.pack(side = 'top', anchor = 'n', fill = 'both', expand = True)
        
        self.open_frame_file_button = ctk.CTkButton(self.main_frame, text='Open File', command=self.open_file_dialog)
        self.open_frame_file_button.pack(side = 'top', pady = 10)

        self.file_path_label = ctk.CTkLabel(self.main_frame, text='No file selected')
        self.file_path_label.pack(side = 'top', pady = 10)

        self.process_frames_button = ctk.CTkButton(self.main_frame, text='Process Frames', command=self.process_frames_wrapper)
        self.process_frames_button.pack(side = 'top', pady = 10)

        self.select_output_file_button = ctk.CTkButton(self.main_frame, text='Select Output File', command=self.select_output_file)
        self.select_output_file_button.pack(side = 'top', pady = 10)

        self.output_file_path_label = ctk.CTkLabel(self.main_frame, text='No output file selected')
        self.output_file_path_label.pack(side = 'top', pady = 10)

        self.automatic_assign_checkbox = ctk.CTkCheckBox(self.main_frame, text='Automatic Output File Assign', variable=self.automatic_assign_var, command=self.toggle_automatic_assign)
        self.automatic_assign_checkbox.pack(side = 'top', pady = 10)

        self.mainloop()
        
    def load_data(self, file_path):
        frame_arrays = np.load(file_path)
        self.raw_frames = frame_arrays['raw_frames']
        file_name = os.path.basename(file_path)
        self.file_path_label.configure(text=file_name)
        self.output_file_uuid = file_name.split('_', 1)[1].replace('.npz', '')
        self.data_loaded = True
        self.output_file_path = None
        self.output_file_path_label.configure(text='No output file selected')
        self.frame_file_dir = os.path.dirname(file_path)
        if self.automatic_assign_var.get():
            self.output_file_path_label.configure(text=f'Automatic output file assign enabled')

    def process_frames_wrapper(self):
        if not self.data_loaded:
            tkinter.messagebox.showerror('Error', 'Please load a file before processing frames')
            return
        if self.output_file_path is None and self.output_file_uuid is not None:
            if not self.automatic_assign_var.get():
                output_file_dir = filedialog.askdirectory()
                output_file_basename = f'counters_{self.output_file_uuid}.npz'
                self.output_file_path = os.path.join(output_file_dir, output_file_basename)
                self.output_file_path_label.configure(text=output_file_basename)
            else:
                self.output_file_path = os.path.join(self.frame_file_dir, f'counters_{self.output_file_uuid}.npz')
                self.output_file_path_label.configure(text=f'counters_{self.output_file_uuid}.npz')
                
        elif self.output_file_uuid is None:
            tkinter.messagebox.showerror('Error', 'Please press the Process Frames button before selecting an output file (uuid)')
            return
        if self.output_file_path:
            self.process_frames(self.output_file_path)
        
    def process_frames(self, output_file_path):
        red_counter = []
        green_counter = []
        
        for i, frameraw in enumerate(self.raw_frames):
            framehsv = cv2.cvtColor(frameraw, cv2.COLOR_BGR2HSV)
            
            # Create a mask of pixels within the green color range
            mask_green = cv2.inRange(framehsv, self.lower_green, self.upper_green)

            # Create a mask of pixels within the red color range
            mask_red1 = cv2.inRange(framehsv, self.lower_red1, self.upper_red1)
            mask_red2 = cv2.inRange(framehsv, self.lower_red2, self.upper_red2)
            mask_red = cv2.bitwise_or(mask_red1, mask_red2)

            # Dilate the masks to merge nearby areas
            mask_green = cv2.dilate(mask_green, self.kernel, iterations=1)
            mask_red = cv2.dilate(mask_red, self.kernel, iterations=1)

            # Find contours in the green mask
            contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Find contours in the red mask
            contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Process each green contour
            for contour in contours_green:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 5 and h > 10 and i != 0:  # Only consider boxes larger than 50x50
                    green_counter.append(-1)
                    break  
            else:
                last_green_counter = green_counter[-1] if green_counter else 0
                if last_green_counter > 0 and last_green_counter < 30:
                    green_counter.append(last_green_counter + 1)
                
                elif last_green_counter == -1:
                    green_counter.append(1)    
                
                else:
                    green_counter.append(0)

            # Process each red contour
            for contour in contours_red:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 5 and h > 10 and i != 0:  # Only consider boxes larger than 50x50
                    red_counter.append(-1)
                    break
            else:
                last_red_counter = red_counter[-1] if red_counter else 0
                if last_red_counter > 0 and last_red_counter < 30:
                    red_counter.append(last_red_counter + 1)
                    
                elif last_red_counter == -1:
                    red_counter.append(1)
                    
                else:
                    red_counter.append(0)
                    
            print(f"Frame {i}: Red: {red_counter[-1]}, Green: {green_counter[-1]}")
                    
        np.savez(output_file_path, red_counter=red_counter, green_counter=green_counter)
                    
    def open_file_dialog(self):
        file_path = filedialog.askopenfilename()
        self.load_data(file_path)

    def select_output_file(self):
        if self.output_file_uuid is None:
            tkinter.messagebox.showerror('Error', 'Please press the Process Frames button before selecting an output file (uuid)')
            return
        if self.automatic_assign_var.get():
            tkinter.messagebox.showerror('Error', 'Automatic output file assign is enabled')
            return
        
        output_file_dir = filedialog.askdirectory()
        output_file_basename = f'counters_{self.output_file_uuid}.npz'
        self.output_file_path = os.path.join(output_file_dir, output_file_basename)
        self.output_file_path_label.configure(text=output_file_basename)

    def toggle_automatic_assign(self):
        if self.automatic_assign_var.get():
            self.output_file_path = None
            self.output_file_path_label.configure(text='Automatic output file assign enabled')
        else:
            self.output_file_path = None
            self.output_file_path_label.configure(text='No output file selected')

if __name__ == '__main__':
    app = AddBlockCounter()