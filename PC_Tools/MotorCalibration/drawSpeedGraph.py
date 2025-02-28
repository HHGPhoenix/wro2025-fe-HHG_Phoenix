import serial
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
import threading

class MotorCalibrationApp:
    def __init__(self):
        # Initialize serial connection
        self.ser = serial.Serial('COM4', 921600)
        time.sleep(2)
        self.ser.write('SPEED 0\n'.encode())
        
        # Data storage
        self.cs_values = []
        self.out_values = []
        self.running = True
        
        # Configure customtkinter appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create the main window
        self.root = ctk.CTk()
        self.root.title("Motor Calibration Tool")
        self.root.geometry("1200x800")
        
        # Create frames
        self.graph_frame = ctk.CTkFrame(self.root)
        self.graph_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.control_frame = ctk.CTkFrame(self.root)
        self.control_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Create matplotlib figure and canvas
        self.create_plots()
        
        # Create control elements
        self.create_controls()
        
        # Start the animation
        self.ani = FuncAnimation(self.fig, self.update_plot, interval=1, blit=True)
        
        # Start a separate thread for reading serial data
        self.data_thread = threading.Thread(target=self.read_serial_data)
        self.data_thread.daemon = True
        self.data_thread.start()
        
        # Set up close event handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_plots(self):
        # Create matplotlib figure
        self.fig = plt.figure(figsize=(10, 6))
        
        # Create subplots
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212, sharex=self.ax1)
        
        # Initialize plot lines
        self.line1, = self.ax1.plot([], [], color='#3a7ebf', linewidth=2)
        self.line2, = self.ax2.plot([], [], color='#bf3a3a', linewidth=2)
        
        # Configure axes
        self.ax1.set_ylabel('CS Value')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_facecolor('#2b2b2b')
        
        self.ax2.set_ylabel('Out Value')
        self.ax2.set_xlabel('Samples')
        self.ax2.grid(True, alpha=0.3)
        self.ax2.set_facecolor('#2b2b2b')
        
        self.fig.patch.set_facecolor('#1a1a1a')
        for ax in [self.ax1, self.ax2]:
            ax.spines['bottom'].set_color('#555555')
            ax.spines['top'].set_color('#555555')
            ax.spines['left'].set_color('#555555')
            ax.spines['right'].set_color('#555555')
            ax.tick_params(colors='#cccccc')
            ax.yaxis.label.set_color('#cccccc')
            ax.xaxis.label.set_color('#cccccc')
        
        # Embed the figure in the tkinter window
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Add figure toolbar
        self.fig.tight_layout()
    
    def create_controls(self):
        # Parameter input area
        param_frame = ctk.CTkFrame(self.control_frame)
        param_frame.pack(side="left", padx=20, pady=20, fill="y")
        
        # Title for parameters
        ctk.CTkLabel(param_frame, text="Controller Parameters", font=("Roboto", 16, "bold")).pack(pady=(0, 10))
        
        # KP input
        kp_frame = ctk.CTkFrame(param_frame)
        kp_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(kp_frame, text="KP:", width=30).pack(side="left", padx=5)
        self.kp_entry = ctk.CTkEntry(kp_frame, width=100)
        self.kp_entry.pack(side="left", padx=5)
        self.kp_entry.insert(0, "0.3")
        
        # KD input
        kd_frame = ctk.CTkFrame(param_frame)
        kd_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(kd_frame, text="KD:", width=30).pack(side="left", padx=5)
        self.kd_entry = ctk.CTkEntry(kd_frame, width=100)
        self.kd_entry.pack(side="left", padx=5)
        self.kd_entry.insert(0, "0.5")
        
        # KA input
        ka_frame = ctk.CTkFrame(param_frame)
        ka_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(ka_frame, text="KA:", width=30).pack(side="left", padx=5)
        self.ka_entry = ctk.CTkEntry(ka_frame, width=100)
        self.ka_entry.pack(side="left", padx=5)
        self.ka_entry.insert(0, "1.0")
        
        # Speed control area
        speed_frame = ctk.CTkFrame(self.control_frame)
        speed_frame.pack(side="right", padx=20, pady=20, fill="y")
        
        # Title for speed control
        ctk.CTkLabel(speed_frame, text="Speed Control", font=("Roboto", 16, "bold")).pack(pady=(0, 10))
        
        # Speed input
        speed_input_frame = ctk.CTkFrame(speed_frame)
        speed_input_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(speed_input_frame, text="Speed:", width=50).pack(side="left", padx=5)
        self.speed_entry = ctk.CTkEntry(speed_input_frame, width=100)
        self.speed_entry.pack(side="left", padx=5)
        self.speed_entry.insert(0, "100")
        
        # Speed slider
        self.speed_slider = ctk.CTkSlider(speed_frame, from_=0, to=255, number_of_steps=255)
        self.speed_slider.pack(fill="x", padx=10, pady=10)
        self.speed_slider.set(100)
        self.speed_slider.configure(command=self.update_speed_from_slider)
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(self.control_frame)
        buttons_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        # Control buttons
        self.send_button = ctk.CTkButton(
            buttons_frame, 
            text="Send Parameters", 
            command=self.send_parameters,
            fg_color="#2b5278",
            hover_color="#3a7ebf"
        )
        self.send_button.pack(side="left", padx=10, pady=10)
        
        self.stop_button = ctk.CTkButton(
            buttons_frame, 
            text="EMERGENCY STOP", 
            command=self.stop_motor,
            fg_color="#782b2b",
            hover_color="#bf3a3a"
        )
        self.stop_button.pack(side="right", padx=10, pady=10)
        
        # Clear plot button
        self.clear_button = ctk.CTkButton(
            buttons_frame,
            text="Clear Plot",
            command=self.clear_plot,
            fg_color="#2b5c2b",
            hover_color="#3abf3a"
        )
        self.clear_button.pack(side="left", padx=10, pady=10)
    
    def update_speed_from_slider(self, value):
        self.speed_entry.delete(0, "end")
        self.speed_entry.insert(0, str(int(value)))
    
    def send_parameters(self):
        try:
            kp = float(self.kp_entry.get())
            kd = float(self.kd_entry.get())
            ka = float(self.ka_entry.get())
            speed = int(self.speed_entry.get())
            
            # Send parameters to controller
            self.ser.write(f'KP {kp}\n'.encode())
            print(f"Sent KP: {kp}")
            time.sleep(0.1)
            
            self.ser.write(f'KD {kd}\n'.encode())
            print(f"Sent KD: {kd}")
            time.sleep(0.1)
            
            self.ser.write(f'KA {ka}\n'.encode())
            print(f"Sent KA: {ka}")
            time.sleep(0.1)
            
            self.ser.write(f'SPEED {speed}\n'.encode())
            print(f"Sent Speed: {speed}")
            
        except ValueError:
            print("Invalid parameter value. Please enter numeric values only.")
    
    def stop_motor(self):
        self.ser.write('SPEED 0\n'.encode())
        print("EMERGENCY STOP: Sent SPEED 0")
        self.speed_entry.delete(0, "end")
        self.speed_entry.insert(0, "0")
        self.speed_slider.set(0)
    
    def clear_plot(self):
        self.cs_values = []
        self.out_values = []
    
    def read_serial_data(self):
        while self.running:
            if self.ser.in_waiting > 0:
                try:
                    line = self.ser.readline().decode().strip()
                    
                    if "CS" in line:
                        cs = float(line.split(': ')[1])
                        if cs <= 6000:
                            self.cs_values.append(cs)
                    
                    elif "Out" in line:
                        out = float(line.split(': ')[1])
                        if out < 0:
                            out = 0
                        self.out_values.append(out)
                    
                    elif "D" in line:
                        print(line)
                except:
                    pass
            time.sleep(0.001)
    
    def update_plot(self, i):
        # Update plot data
        self.line1.set_data(range(len(self.cs_values)), self.cs_values)
        self.line2.set_data(range(len(self.out_values)), self.out_values)
        
        # Adjust axis limits
        max_len = max(len(self.cs_values), len(self.out_values))
        if max_len > 0:
            self.ax1.set_xlim(0, max_len)
            
            if self.cs_values:
                self.ax1.set_ylim(0, max(self.cs_values) + 20)
            else:
                self.ax1.set_ylim(0, 1)
            
            if self.out_values:
                self.ax2.set_ylim(0, max(self.out_values) + 20)
            else:
                self.ax2.set_ylim(0, 1)
        
        return self.line1, self.line2,
    
    def on_close(self):
        print("Closing application...")
        self.running = False
        self.stop_motor()
        time.sleep(0.5)
        self.ser.close()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MotorCalibrationApp()
    app.run()