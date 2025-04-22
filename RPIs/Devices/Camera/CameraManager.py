import cv2
import numpy as np
import threading
import time
import uuid
from picamera2 import Picamera2 # type: ignore
from libcamera import controls # type: ignore

#A class for detecting red and green blocks in the camera stream           
class Camera():
    def __init__(self):
        """
        Initialize the camera and set up the color ranges for red and green blocks.
        """
        # Variable initialization
        self.freeze = False
        self.frame = None
        
        self.red_counter = []
        self.green_counter = []
        
        self.picam = Picamera2()
        # Configure and start the camera
        config = self.picam.create_still_configuration(main={"size": (1280, 720)}, raw={"size": (1280, 720)}, controls={"FrameRate": 34})
        self.picam.configure(config)
        self.picam.start()
        self.picam.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        self.picam.set_logging(Picamera2.ERROR)
        
        self.lower_green = np.array([54, 97, 77])
        self.upper_green = np.array([65, 170, 180])

        self.lower_red1 = np.array([0, 142, 95])
        self.upper_red1 = np.array([5, 207, 140])

        self.lower_red2 = np.array([0, 142, 95])
        self.upper_red2 = np.array([5, 207, 140])

        # Define the kernel for morphological operations
        self.kernel = np.ones((5, 5), np.uint8)
        
    def capture_array(self):
        """
        Capture an image from the camera and convert it to RGB and HSV color spaces.

        Returns:
            np.ndarray: The captured image in RGB color space.
            np.ndarray: The captured image in HSV color space.
        """
        frame = self.picam.capture_array()
        frameraw = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        framehsv = cv2.cvtColor(frameraw, cv2.COLOR_BGR2HSV)        
        return frameraw, framehsv

    def draw_blocks(self, frameraw, framehsv):
        """
        Draw rectangles around green and red blocks in the camera stream.
    
        Args:
            frameraw (np.ndarray): The image in RGB color space.
            framehsv (np.ndarray): The image in HSV color space.
    
        Returns:
            tuple: The image with rectangles drawn around green and red blocks, 
                   list of green bounding boxes, list of red bounding boxes.
        """
        # Create a mask of pixels within the green color range
        mask_green = cv2.inRange(framehsv, self.lower_green, self.upper_green)
    
        # Create a mask of pixels within the red color range
        mask_red1 = cv2.inRange(framehsv, self.lower_red1, self.upper_red1)
        mask_red2 = cv2.inRange(framehsv, self.lower_red2, self.upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    
        # Dilate the masks to merge nearby areas
        mask_green = cv2.dilate(mask_green, self.kernel, iterations=1)
        mask_red = cv2.dilate(mask_red, self.kernel, iterations=1)
    
        # Find contours in the masks
        contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
        # Process each green contour
        green_boxes = []
        for contour in contours_green:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 5 and h > 10:  # Only consider boxes larger than 50x50
                cv2.rectangle(frameraw, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frameraw, 'Green Object', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
                # cv2.line(frameraw, (640, 720), (int(x+w/2), int(y+h/2)), (0, 255, 0), 2)
                
                green_boxes.append((x + w // 2, y + h // 2, w, h))
    
        # Process each red contour
        red_boxes = []
        for contour in contours_red:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 5 and h > 10:  # Only consider boxes larger than 50x50
                cv2.rectangle(frameraw, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frameraw, 'Red Object', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
                # cv2.line(frameraw, (640, 720), (int(x+w/2), int(y+h/2)), (0, 0, 255), 2)
                
                red_boxes.append((x + w // 2, y + h // 2, w, h))
                
        if len(red_boxes) > 1:
            red_boxes = self.merge_boxes(red_boxes)
            # print(f"merged_red_boxes: {red_boxes}")
            # Fix: sort the list and assign the result back to red_boxes
            red_boxes.sort(key=lambda x: x[2] * x[3], reverse=True)
            # print(f"sorted_red_boxes: {red_boxes}")
            if red_boxes and len(red_boxes) > 0:
                self.red_blocks = (red_boxes[0], red_boxes[1])
            else:
                self.red_blocks = ((0, 0, 0, 0), (0, 0, 0, 0))
        elif len(red_boxes) == 1:
            self.red_blocks = (red_boxes[0], (0, 0, 0, 0))
        else:
            self.red_blocks = ((0, 0, 0, 0), (0, 0, 0, 0))
        
        if len(green_boxes) > 1:
            green_boxes = self.merge_boxes(green_boxes)
            green_boxes.sort(key=lambda x: x[2] * x[3], reverse=True)
            if green_boxes and len(green_boxes) > 0:
                self.green_blocks = (green_boxes[0], green_boxes[1])
            else:
                self.green_blocks = ((0, 0, 0, 0), (0, 0, 0, 0))
        elif len(green_boxes) == 1:
            self.green_blocks = (green_boxes[0], (0, 0, 0, 0))
        else:
            self.green_blocks = ((0, 0, 0, 0), (0, 0, 0, 0))
            
        # print(f"red_blocks: {self.red_blocks}, green_blocks: {self.green_blocks}")
            
        return frameraw
    
    def merge_boxes(self, boxes):
        """
        Merge overlapping boxes.
    
        Args:
            boxes (list): The list of boxes to merge.
    
        Returns:
            list: The list of merged boxes.
        """
        if not boxes:
            return []
    
        merged_boxes = []
        for box in boxes:
            if not merged_boxes:
                merged_boxes.append(box)
            else:
                for i, merged_box in enumerate(merged_boxes):
                    if self.iou(box, merged_box) > 0.5:
                        merged_boxes[i] = self.merge_box(box, merged_box)
                        break
                else:
                    merged_boxes.append(box)
        return merged_boxes
    
    def merge_box(self, box1, box2):
        """
        Merge two boxes.
    
        Args:
            box1 (tuple): The first box in (x1, y1, w, h) format.
            box2 (tuple): The second box in (x1, y1, w, h) format.
    
        Returns:
            tuple: The merged box in (x1, y1, w, h) format.
        """
        x1_1, y1_1, w1, h1 = box1
        x1_2, y1_2, w2, h2 = box2
        
        x1_1 = x1_1 - w1 // 2
        y1_1 = y1_1 - h1 // 2
    
        x2_1 = x1_1 + w1
        y2_1 = y1_1 + h1
        x2_2 = x1_2 + w2
        y2_2 = y1_2 + h2
    
        x1 = min(x1_1, x1_2)
        y1 = min(y1_1, y1_2)
        x2 = max(x2_1, x2_2)
        y2 = max(y2_1, y2_2)
    
        w = x2 - x1
        h = y2 - y1
    
        return (x1, y1, w, h)
    
    def iou(self, box1, box2):
        """
        Calculate the intersection over union (IoU) of two boxes.
    
        Args:
            box1 (tuple): The first box in (x1, y1, w, h) format.
            box2 (tuple): The second box in (x1, y1, w, h) format.
    
        Returns:
            float: The IoU of the two boxes.
        """
        x1_1, y1_1, w1, h1 = box1
        x1_2, y1_2, w2, h2 = box2
        
        x1_1 = x1_1 - w1 // 2
        y1_1 = y1_1 - h1 // 2
    
        x2_1 = x1_1 + w1
        y2_1 = y1_1 + h1
        x2_2 = x1_2 + w2
        y2_2 = y1_2 + h2
    
        x1 = max(x1_1, x1_2)
        y1 = max(y1_1, y1_2)
        x2 = min(x2_1, x2_2)
        y2 = min(y2_1, y2_2)
    
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
    
        return intersection / union if union > 0 else 0
    
    # Compress the video frames for the webstream    
    def compress_frame(self, frame, new_height=120):
        """
        Compress the frame to a specified height while maintaining the aspect ratio.

        Args:
            frame (np.ndarray): The frame to compress.
            new_height (int, optional): The height to compress the frame to. Defaults to 480.

        Raises:
            ValueError: If the number of dimensions in the frame is not 2 or 3.

        Returns:
            np.ndarray: The compressed frame.
        """
        dimensions = len(frame.shape)
        if dimensions == 3:
            height, width, _ = frame.shape
        elif dimensions == 2:
            height, width = frame.shape
        else:
            raise ValueError(f"Unexpected number of dimensions in frame: {dimensions}")
        new_width = int(new_height * width / height)
        frame = cv2.resize(frame, (new_width, new_height))
        
        return frame