# import gpiod
import time
import threading
import os, signal, socket
# from gpiozero import CPUTemperature
# import psutil
# import multiprocessing as mp
import logging
# from flask import Flask, render_template, Response, jsonify
# import cv2
# import numpy as np
# from picamera2 import Picamera2
# from libcamera import controls
from USB_communication_handler import USBCommunication
# from I2C_handler import I2Ccommunication
# from sklearn.linear_model import LinearRegression
# from math import tan, radians, cos, atan, degrees
# import json
# import uuid
# import platform


##########################################################
##                                                      ##
##                   GPIO init                          ##
##                                                      ##
##########################################################
# global chip, all_lines

# chip = gpiod.Chip('gpiochip4')

# all_lines = []


##########################################################
##                                                      ##
##                     Classes                          ##
##                                                      ##
##########################################################

# A class that has some necessary tools for calculating, usw.
class Utility():
    # Transfer data so it can be used in other classes
    def transferSensorData(self, StartButton, StopButton, Buzzer1, Cam=None):
        self.setupLog()
        self.usb_communication = USBCommunication(self)
        self.ESPHoldDistance, self.ESPHoldSpeed = self.usb_communication.initNodeMCUs()
        
        # self.I2C_communication = I2Ccommunication(self)
        self.Display = self.I2C_communication.Display
        self.ADC = self.I2C_communication.ADC
        self.Gyro = self.I2C_communication.Gyro
        self.ColorSensor = self.I2C_communication.ColorSensor
        
        self.Cam = Cam
        if self.Cam is not None:
            self.Cam.video_writer = None
        
        self.StartButton = StartButton
        self.StopButton = StopButton
        self.Buzzer1 = Buzzer1
        self.StartTime = time.time()
        
        self.ActivSensor = 0
        self.file_path = "/tmp/StandbyScript.lock"
        
        self.stop_run_callable = True
        
        self.blockPositions = {}
        
        self.StartSpeed = None
        self.StartSensor = None
        self.Distance = None
        self.Kp = None
        self.Kd = None
        self.Ed = None
        self.Mm = None
        self.AngR = None
        self.AngL = None
        self.startMode = None
        self.corners = 0
        self.relative_angle = 0
        
        return self.ESPHoldDistance, self.ESPHoldSpeed
        
        
    # Cleanup after the run is finished or an error occured
    def cleanup(self):
        self.LogDebug("Started cleanup")

        self.I2C_communication.stop_threads()
        
        self.StopButton.stop_StopButton()
        
        if self.Cam is not None:
            if self.Cam.video_writer is not None:
                self.Cam.video_writer.release()
                pass
        
        #Wait a short time to make sure all threads are stopped
        self.Buzzer1.buzz(1000, 80, 0.5)
        
        print("expected: all lines ['gpiochip4:5 /GPIO5/', 'gpiochip4:6 /GPIO6/', 'gpiochip4:12 /GPIO12/']")
        print("all lines", all_lines)
        # Clear all used lines
        for line in all_lines:
            line.release()
            print("line released", line)
        time.sleep(0.2)
        chip.close()
        
        self.running = False
        self.usb_communication.closeNodeMCUs()
        os.kill(os.getpid(), signal.SIGTERM)
    
    
    # Do some init and wait until StartButton is pressed
    def StartRun(self):
        # clear console
        # os.system('cls' if os.name=='nt' else 'clear')
        
        if self.Cam:
            pCam = mp.Process(target=self.Cam.start_processing())
            pCam.start()
        
        pI2C = mp.Process(target=self.I2C_communication.start_threads())
        pI2C.start()

        p2 = mp.Process(target=self.StopButton.start_StopButton())
        p2.start()

        #Wait for StartButton to be pressed
        self.running = True
        self.waiting = True
        
        self.LogDebug("Waiting for Button to be pressed...")
        self.Display.write("Waiting for Button", "to be pressed...")
        
        self.Buzzer1.buzz(1000, 80, 0.1)
        time.sleep(0.1)
        self.Buzzer1.buzz(1000, 80, 0.1)

        
        while self.running and self.waiting:
            time.sleep(0.1)
            if self.StartButton.state() == 1:
        
                self.usb_communication.startNodeMCUs()
                self.Gyro.GyroStart = True

                self.usb_communication.sendMessage(f"D {self.Distance}", self.ESPHoldDistance)
                self.usb_communication.sendMessage(f"KP {self.Kp}", self.ESPHoldDistance)
                self.usb_communication.sendMessage(f"KD {self.Kd}", self.ESPHoldDistance)
                self.usb_communication.sendMessage(f"ED {self.Ed}", self.ESPHoldDistance)
                self.usb_communication.sendMessage(f"MM {self.Mm}", self.ESPHoldDistance)
                self.usb_communication.sendMessage(f"S{self.StartSensor}", self.ESPHoldDistance)
                self.usb_communication.sendMessage(f"ANGR {self.AngR}", self.ESPHoldDistance)
                self.usb_communication.sendMessage(f"ANGL {self.AngL}", self.ESPHoldDistance)

                timeTime = time.time()
                
                self.StartTime = timeTime
                self.LogDebug(f"Run started: {timeTime}")
                self.Display.write("Run started:", f"{timeTime}")  
                self.Buzzer1.buzz(1000, 80, 0.1) 

                self.waiting = False
                
    
    #Stop the run and calculate the time needed            
    def StopRun(self):
        self.StopTime = time.time()
        self.LogDebug(f"Run ended: {self.StopTime}")
        
        #Stop Nodemcu's
        self.usb_communication.sendMessage("STOP", self.ESPHoldDistance)
        time.sleep(0.1)
        self.usb_communication.sendMessage("STOP", self.ESPHoldSpeed)
        
        if self.StartTime:
            seconds = round(self.StopTime - self.StartTime, 2)
        
            #self.Utils.LogError time needed
            minutes = seconds // 60
            hours = minutes // 60
            if hours > 0:
                self.LogDebug(f"{hours} hour(s), {minutes % 60} minute(s), {seconds % 60} second(s) needed")
                self.Display.write("Time needed:", f"{hours}h {minutes % 60}m {seconds % 60}s")
            elif minutes > 0:
                self.LogDebug(f"{minutes} minute(s), {seconds % 60} second(s) needed")
                self.Display.write("Time needed:", f"{minutes}m {seconds % 60}s")
            else:
                self.LogDebug(f"{seconds} second(s) needed")
                self.Display.write("Time needed:", f"{seconds}s")
                
            self.stop_run_callable = False
            self.cleanup()
          
    
    #Setup datalogging
    def setupDataLog(self):
        #Clear DataLog
        #os.remove("DataLog.log")
            
        #Create datalogger
        self.datalogger = logging.getLogger("DataLogger")
        self.datalogger.setLevel(logging.DEBUG)

        
        #Create file handler and set level to debug
        fh = logging.FileHandler("/tmp/DataLog.log", 'w')
        fh.setLevel(logging.DEBUG)
        self.datalogger.addHandler(fh)

    #Log Sensor values
    def LogData(self):
        self.datalogger.debug(f"Angle: {self.relative_angle}, corners: {self.corners}, ColorTemperature: {self.ColorSensor.color_temperature}")
    
    
    #Stop the DataLogger Process
    def StopDataLog(self):
        self.DataLoggerStop = 1
        
        
    #Setup logging
    def setupLog(self, name='Log', filename='Debug.log'):
        #Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        #Create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        #Create file handler and set level to debug
        fh = logging.FileHandler(filename, 'w')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        #Add handlers to logger
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)
        
        
    #Log debug messages
    def LogDebug(self, message):
        self.logger.debug(message)
        
    def LogInfo(self, message):
        self.logger.info(message)
        
    def LogWarning(self, message):
        self.logger.warning(message)
        
    def LogError(self, message):
        self.logger.error(message)
        
    def LogCritical(self, message):
        self.logger.critical(message)

    
    #Convert a number to a specified number of decimal points
    def convert_to_decimal_points(self, number, decimal_points):
        number = float(number)
        formatted_string = f"{number:.{decimal_points}f}"
        return formatted_string


    #Convert a number to a specified number of digits
    def convert_to_specified_digits(self, number, num_digits):
        # Check if the input number is a valid float or int
        if not isinstance(number, (float, int)):
            raise ValueError("The input number must be a valid float or int")
        
        # Convert the number to a string
        num_str = str(number)
        
        # Split the number into its integer and decimal parts
        if '.' in num_str:
            integer_part, decimal_part = num_str.split('.')
        else:
            integer_part, decimal_part = num_str, '0'
        
        # If the integer part has more digits than the specified number, return it as is
        if len(integer_part) >= num_digits:
            return integer_part
        
        # Otherwise, pad the integer part with leading zeros to match the specified number of digits
        padded_integer_part = integer_part.zfill(num_digits)
        
        # Reconstruct the final number with the decimal part
        final_number = f"{padded_integer_part}.{decimal_part}"
        
        return final_number
    
    
    # Collect data from the sensors
    def data_feed(self):
        return {"D1": self.SensorDistance1, "D2": self.SensorDistance2, "angle": self.Gyro.angle, "voltage": self.ADC.voltage, "cpu_usage": psutil.cpu_percent(), "ram_usage": psutil.virtual_memory().percent}
    
    
    # Check for the presence of a key JSON file
    def check_for_key_json(self, json_file_path, key):
        file_path = os.path.join(os.getcwd(), json_file_path)
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as file:
                json.dump({key: 'False'}, file)
        else:
            with open(file_path, 'r+') as file:
                data = json.load(file)
                if key not in data:
                    data[key] = 'False'
                    file.seek(0)
                    json.dump(data, file)
                    file.truncate()
                elif not data:
                    file.seek(0)
                    json.dump({key: 'False'}, file)
                    file.truncate()
                elif data.get(key) == 'True':
                    return True
        return False
    

    # Change a key JSON file
    def change_key_json(self, json_file_path, key, value):
        file_path = os.path.join(os.getcwd(), json_file_path)
        if not os.path.exists(file_path):
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as file:
                json.dump({key: value}, file)
        else:
            with open(file_path, 'r+') as file:
                data = json.load(file)
                data[key] = value
                file.seek(0)
                json.dump(data, file)
                file.truncate()


#A class for reading a Button; A Button that instantly stops the program if pressed            
class Button(Utility):
    def __init__(self, SignalPin, Utils):
        #Variables
        self.SignalPin = SignalPin
        self.Utils = Utils
        
        #GPIO setup
        self.button_line = chip.get_line(SignalPin)
        
        try:
            self.button_line.request(consumer='Button', type=gpiod.LINE_REQ_DIR_IN, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP)
        finally:
            self.button_line.release()
        
            try:
                self.button_line.request(consumer='Button', type=gpiod.LINE_REQ_DIR_IN, flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP)
            except OSError:
                print("!!!! REBOOT !!!!")
                print("OS Error in Button class")
                print("!!!! REBOOT !!!!")

                time.sleep(1)

                # restart the rpi (linux)
                os.system('sudo reboot')

        all_lines.append(self.button_line)
        
    
    #Read the state of the Button -- 1 if pressed, 0 if not    
    def state(self): 
        #Read button state
        if self.button_line.get_value() == 0:
            return 1
        elif self.button_line.get_value() == 1:
            return 0
      
    
    #Start the Thread for reading the StopButton    
    def start_StopButton(self):
        self.threadStop = 0
        self.thread = threading.Thread(target=self.read_StopButton, daemon=True)
        self.thread.start()
  
    
    #Function that kills the program if the StopButton is pressed    
    def read_StopButton(self):
        #Stop program if stopbutton is pressed
        while self.threadStop == 0:
            time.sleep(0.1)
            if self.state() == 1:
                self.Utils.LogError("StopButton pressed")
                self.Utils.running = False
                
                
    #Stop the Thread for reading the StopButton      
    def stop_StopButton(self):
        self.threadStop = 1

          
#A class for making sounds with a Buzzer
class Buzzer(Utility):
    def __init__(self, SignalPin, Utils):

        self.Utils = Utils
        self.SignalPinLine = chip.get_line(SignalPin)
        
        try:
            self.SignalPinLine.request(consumer='buzzer', type=gpiod.LINE_REQ_DIR_OUT)
        finally:
            self.SignalPinLine.release()
            try:
                self.SignalPinLine.request(consumer='buzzer', type=gpiod.LINE_REQ_DIR_OUT)
            except OSError:
                print("!!!! REBOOT !!!!")
                print("OS Error in Buzzer class")
                print("!!!! REBOOT !!!!")

                time.sleep(1)

                # restart the rpi (linux)
                os.system('sudo reboot')
        
        all_lines.append(self.SignalPinLine)

    def buzz(self, frequency, volume, duration):
        try:
            # Check if the volume value is greater than the frequency
            if volume > frequency:
                volume = frequency

            period = 1.0 / frequency  # Calculate the period of the frequency
            on_time = period * volume / 100  # Calculate the time the signal should be on
            off_time = period - on_time  # Calculate the time the signal should be off

            end_time = time.time() + duration
            while time.time() < end_time:
                self.SignalPinLine.set_value(1)
                time.sleep(on_time)
                self.SignalPinLine.set_value(0)
                time.sleep(off_time)
                
        except PermissionError:
            self.Utils.LogDebug("Buzzer already in use, skipping")
            return
            

#A class for detecting red and green blocks in the camera stream           
class Camera():
    def __init__(self, video_stream=False, enable_video_writer=False, Utils=None):
        # Variable initialization
        self.freeze = False
        self.frame = None
        self.frame_lock_1 = threading.Lock()
        self.frame_lock_2 = threading.Lock()
        self.video_stream = video_stream
        self.picam2 = Picamera2()
        self.Utils = Utils
        self.enable_video_writer = enable_video_writer
        
        # Configure and start the camera
        config = self.picam2.create_still_configuration(main={"size": (1280, 720)}, raw={"size": (1280, 720)}, controls={"FrameRate": 34})
        self.picam2.configure(config)
        self.picam2.start()
        self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        
        # Define the color ranges for green and red in HSV color space
        self.lower_green = np.array([53, 100, 40])
        self.upper_green = np.array([93, 220, 150])

        self.lower_red1 = np.array([0, 160, 120])
        self.upper_red1 = np.array([5, 220, 200])

        self.lower_red2 = np.array([173, 160, 100])
        self.upper_red2 = np.array([180, 220, 200])

        # Define the kernel for morphological operations
        self.kernel = np.ones((7, 7), np.uint8)
        self.desired_distance_wall = -1
        self.block_distance = -1
        
        self.edge_distances = []
        self.avg_edge_distance = 0
        
        self.focal_length = 373.8461538461538
        self.known_height = 0.1
        self.camera_angle = 15
        self.distance_multiplier = 2.22
        
    
    # Get distance to the wall
    def get_edges(self, frame):
        frame = frame[250:, 300:980]
        
        # Convert the frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        gray = cv2.dilate(gray, self.kernel, iterations=1)
        # Threshold the grayscale image to get a binary image
        binary = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)[1]
        
        binary = cv2.dilate(binary, self.kernel, iterations=2)

       # Perform Canny edge detection
        edges = cv2.Canny(binary, 50, 120, apertureSize=3)

        # Perform Probabilistic Hough Line Transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=30)

        # Initialize an empty list to store the groups of lines
        line_groups = []

        # Define a function to calculate the slope and intercept of a line
        def get_slope_intercept(line):
            x1, y1, x2, y2 = line[0]
            try:
                if x2 - x1 != 0:
                    slope = (y2 - y1) / (x2 - x1)
                else:
                    slope = float('inf')
            except:
                slope = 0
                
            intercept = y1 - slope * x1
            return slope, intercept

        # Define a threshold for the difference in slopes and intercepts
        slope_threshold = 0.1
        intercept_threshold = 10.0

        # Group the lines
        try:
            for line in lines:
                slope1, intercept1 = get_slope_intercept(line)
                for group in line_groups:
                    slope2, intercept2 = get_slope_intercept(group[0])
                    if abs(slope1 - slope2) < slope_threshold and abs(intercept1 - intercept2) < intercept_threshold:
                        group.append(line)
                        break
                else:
                    line_groups.append([line])

            # Initialize a Linear Regression model
            model = LinearRegression()

            # Initialize a dictionary to store the lines grouped by their angles
            lines_by_angle = {}

            for group in line_groups:
                # Prepare the data for Linear Regression
                x = np.array([val for line in group for val in line[0][::2]]).reshape(-1, 1)
                y = np.array([val for line in group for val in line[0][1::2]])

                # Fit the model to the data
                model.fit(x, y)

                # Get the slope and intercept of the line
                slope = model.coef_[0]
                intercept = model.intercept_

                # Flatten the array
                x_flat = x.flatten()
                
                # Calculate the start and end points of the line
                x1 = int(min(x_flat))
                y1 = int(slope * x1 + intercept)
                x2 = int(max(x_flat))
                y2 = int(slope * x2 + intercept)

                # Calculate the angle of the line
                try:
                    angle = atan((y2 - y1) / (x2 - x1))
                except:
                    angle = 0
                    
                angle = degrees(angle)

                # Group the lines by their angles with a 5 degree tolerance
                grouped = False
                for existing_angle in lines_by_angle.keys():
                    if abs(angle - existing_angle) <= 5:
                        lines_by_angle[existing_angle].append(((x1, y1), (x2, y2)))
                        grouped = True
                        break
                if not grouped:
                    lines_by_angle[angle] = [((x1, y1), (x2, y2))]

                # Draw the line
                cv2.line(binary, (x1, y1), (x2, y2), (125, 125, 125), 4)
            
            for angle, lines in lines_by_angle.items():
                avg_ycoord_bottom = 0
                
                if len(lines) > 1:
                    avg_ycoord_1 = (lines[0][0][1] + lines[0][1][1]) / 2
                    avg_ycoord_2 = (lines[1][0][1] + lines[1][1][1]) / 2
                    
                    if avg_ycoord_1 > avg_ycoord_2:
                        avg_ycoord_bottom = avg_ycoord_1
                    else:
                        avg_ycoord_bottom = avg_ycoord_2   
                else:
                    avg_ycoord_bottom = (lines[0][0][1] + lines[0][1][1]) / 2

                self.real_distance = 0
                if avg_ycoord_bottom != 0:
                    self.real_distance =  7193 * (avg_ycoord_bottom ** -0.917)
                    
                    
                    cv2.putText(binary, f"{round(self.real_distance, 3)} cm", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (125, 125, 125), 4)
                    
                    break
                    
                elif avg_ycoord_bottom == 0:
                    self.real_distance = 0 
                    
        except TypeError:
            self.real_distance = 0
                    
        if self.real_distance != 0:
            if self.real_distance > 30 and self.real_distance < 300:
                #print(self.edge_distances)
                if len(self.edge_distances) > 3:
                    self.edge_distances.pop(0)
                    
                self.edge_distances.append(round(self.real_distance, 3))
                self.avg_edge_distance = np.mean(self.edge_distances)
                #print(self.avg_edge_distance)   
        
        return binary
    
    
    #Get the coordinates of the blocks in the camera stream
    def get_coordinates(self):
        frameraw = self.picam2.capture_array()
        
        frameraw = cv2.cvtColor(frameraw, cv2.COLOR_BGR2RGB)
        frame = frameraw.copy()
        
        # cutoff frames
        frame = frame[250:, :]

        # Convert the image from BGR to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Create a mask of pixels within the green color range
        mask_green = cv2.inRange(hsv, self.lower_green, self.upper_green)

        # Create a mask of pixels within the red color range
        mask_red1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask_red2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        # Dilate the masks to merge nearby areas
        mask_green = cv2.dilate(mask_green, self.kernel, iterations=1)
        mask_red = cv2.dilate(mask_red, self.kernel, iterations=1)

        # Find contours in the green mask
        contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Find contours in the red mask
        contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        #print(f"middle hsv: {hsv[0, 360]}, inverted: {hsv[300, 1000]}")
        
        cv2.circle(frame, (640, 720), 10, (255, 0, 0), -1)
        cv2.putText(frame, f"{self.desired_distance_wall}", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 4)
        cv2.putText(frame, f"Freeze: {self.freeze}", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 4)
        cv2.putText(frame, f"Distance: {self.block_distance}", (700, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 4)
        #cv2.circle(frame, (1000, 300), 10, (255, 0, 0), -1)
        
        block_array = []

        # Process each green contour
        for contour in contours_green:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 20 and h > 50:  # Only consider boxes larger than 50x50
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, 'Green Object', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
                block_array.append({'color': 'green', 'x': x, 'y': y, 'w': w, 'h': h, 'mx': x+w/2, 'my': y+h/2, 'size': w*h, 'distance': self.get_distance_to_block({'x': x, 'y': y, 'w': w, 'h': h})})
                cv2.line(frame, (640, 720), (int(x+w/2), int(y+h/2)), (0, 255, 0), 2)

        # Process each red contour
        for contour in contours_red:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 20 and h > 50:  # Only consider boxes larger than 50x50
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, 'Red Object', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
                block_array.append({'color': 'red', 'x': x, 'y': y, 'w': w, 'h': h, 'mx': x+w/2, 'my': y+h/2, 'size': w*h, 'distance': self.get_distance_to_block({'x': x, 'y': y, 'w': w, 'h': h})})
                cv2.line(frame, (640, 720), (int(x+w/2), int(y+h/2)), (0, 0, 255), 2)
            
        return block_array, frame, frameraw
    
    
    def get_distance_to_block(self, block):
        # Calculate the distance to the block
        image_distance = (self.focal_length * self.known_height * cos(radians(self.camera_angle))) / block['h']
        self.real_distance = image_distance * self.distance_multiplier
        
        self.block_distance = self.real_distance * 100
        return self.real_distance * 100
        
         
    # Function running in a new thread that constantly updates the coordinates of the blocks in the camera stream
    def process_blocks(self):
        self.video_writer = None
        self.frames = [None] * 3

        while True:
            self.block_array, framenormal, frameraw = self.get_coordinates()
            framebinary = self.get_edges(frameraw)

            self.frames[0] = framenormal
            self.frames[1] = framebinary
            self.frames[2] = frameraw

            if self.video_writer is None and self.enable_video_writer:
                # Create a VideoWriter object to save the frames as an mp4 file
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(f'./videos/output_{str(uuid.uuid4())}.mp4', fourcc, 20, (frameraw.shape[1], frameraw.shape[0]), True)

            # Write the frame to the video file
            if self.enable_video_writer:
                self.video_writer.write(frameraw)


    # Start a new thread for processing the camera stream
    def start_processing(self):
        thread = threading.Thread(target=self.process_blocks)
        thread.daemon = False
        thread.start()
    
    
    # Compress the video frames for the webstream    
    def compress_frame(self, frame):
        dimensions = len(frame.shape)
        if dimensions == 3:
            height, width, _ = frame.shape
        elif dimensions == 2:
            height, width = frame.shape
        else:
            raise ValueError(f"Unexpected number of dimensions in frame: {dimensions}")
        new_height = 180
        new_width = int(new_height * width / height)
        frame = cv2.resize(frame, (new_width, new_height))
        return frame


    # Generate the frames for the webstream
    def video_frames(self, frame_type):
        if self.video_stream:
            while True:
                if frame_type == 'type1' and self.frames[0] is not None:
                    with self.frame_lock_1:
                        frame = self.compress_frame(self.frames[0])
                        (flag, encodedImage) = cv2.imencode(".jpg", frame)
                        yield (b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')
                elif frame_type == 'type2' and self.frames[1] is not None:
                    with self.frame_lock_2:
                        frame = self.compress_frame(self.frames[1])
                        (flag, encodedImage) = cv2.imencode(".jpg", frame)
                        yield (b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')
