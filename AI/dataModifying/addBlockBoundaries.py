import os
import numpy as np
import cv2

class BlockDetector:
    def __init__(self, lower_green, upper_green, lower_red1, upper_red1, lower_red2, upper_red2, kernel):
        self.lower_green = lower_green
        self.upper_green = upper_green
        self.lower_red1 = lower_red1
        self.upper_red1 = upper_red1
        self.lower_red2 = lower_red2
        self.upper_red2 = upper_red2
        self.kernel = kernel
        self.green_counter = []
        self.red_counter = []
        self.green_block = None
        self.red_block = None

    def draw_blocks(self, frameraw, framehsv, counter_frames=30):
        """
        Draw rectangles around green and red blocks in the camera stream.

        Args:
            frameraw (np.ndarray): The image in RGB color space.
            framehsv (np.ndarray): The image in HSV color space.

        Returns:
            np.ndarray: The image with rectangles drawn around green and red blocks.
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

        # Find contours in the green mask
        contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Find contours in the red mask
        contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        cv2.circle(frameraw, (640, 720), 10, (255, 0, 0), -1)

        green_counter_set = False
        red_counter_set = False

        # Process each green contour
        green_boxes = []
        for contour in contours_green:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 5 and h > 10:  # Only consider boxes larger than 50x50
                # cv2.rectangle(frameraw, (x, y), (x+w, y+h), (0, 255, 0), 2)
                # cv2.putText(frameraw, 'Green Object', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
                # cv2.line(frameraw, (640, 720), (int(x+w/2), int(y+h/2)), (0, 255, 0), 2)
                
                green_boxes.append((x, y, x + w, y + h))
                
                if green_counter_set == False:
                    self.green_counter.append(1)
                    green_counter_set = True
        else:
            last_green_counter = self.green_counter[-1] if self.green_counter else 0
            if last_green_counter - 1 / counter_frames > 0 and last_green_counter <= 1 and not green_counter_set:
                self.green_counter.append(round(last_green_counter - 1 / counter_frames, 5))
                green_counter_set = True
                
            elif not green_counter_set:
                self.green_counter.append(0)
                green_counter_set = True
                
        if len(self.green_counter) > 10:
            self.green_counter.pop(0)

        # Process each red contour
        red_boxes = []
        for contour in contours_red:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 5 and h > 10:  # Only consider boxes larger than 50x50
                # cv2.rectangle(frameraw, (x, y), (x+w, y+h), (0, 0, 255), 2)
                # cv2.putText(frameraw, 'Red Object', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
                # cv2.line(frameraw, (640, 720), (int(x+w/2), int(y+h/2)), (0, 0, 255), 2)
                
                red_boxes.append((x, y, x + w, y + h))
                
                if red_counter_set == False:
                    self.red_counter.append(1)
                    red_counter_set = True
        else:
            last_red_counter = self.red_counter[-1] if self.red_counter else 0
            if last_red_counter - 1 / counter_frames > 0 and last_red_counter <= 1 and not red_counter_set:
                self.red_counter.append(round(last_red_counter - 1 / counter_frames, 5))
                red_counter_set = True
                
            elif not red_counter_set:
                self.red_counter.append(0)
                red_counter_set = True
                
        if len(red_boxes) > 1:
            red_boxes = self.merge_boxes(red_boxes)
            red_boxes = sorted(red_boxes, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]), reverse=True)
            print(f"Red Boxes: {red_boxes}")
            if red_boxes and len(red_boxes) > 0:
                self.red_block = red_boxes[0]
            else:
                self.red_block = [0, 0, 0, 0]
        elif len(red_boxes) == 1:
            self.red_block = red_boxes[0]
        else:
            self.red_block = [0, 0, 0, 0]
        
        if len(green_boxes) > 1:
            green_boxes = self.merge_boxes(green_boxes)
            # sort by area
            green_boxes = sorted(green_boxes, key=lambda x: (x[2] - x[0]) * (x[3] - x[1]), reverse=True)
            print(f"Green Boxes: {green_boxes}")
            if green_boxes and len(green_boxes) > 0:
                self.green_block = green_boxes[0]
            else:
                self.green_block = [0, 0, 0, 0]
        elif len(green_boxes) == 1:
            self.green_block = green_boxes[0]
        else:
            self.green_block = [0, 0, 0, 0]
            
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
                    iou_value = self.iou(box, merged_box)
                    print(f"Box: {box}, Merged Box: {merged_box}, IoU: {iou_value}")
                    if iou_value > 0.1:
                        merged_boxes[i] = self.merge_box(box, merged_box)
                        break
                else:
                    merged_boxes.append(box)
        print(f"Merged Boxes: {merged_boxes}")
        return merged_boxes
    
    def merge_box(self, box1, box2):
        """
        Merge two boxes.

        Args:
            box1 (tuple): The first box to merge.
            box2 (tuple): The second box to merge.

        Returns:
            tuple: The merged box.
        """
        x1 = min(box1[0], box2[0])
        y1 = min(box1[1], box2[1])
        x2 = max(box1[2], box2[2])
        y2 = max(box1[3], box2[3])
        return (x1, y1, x2, y2)
    
    def iou(self, box1, box2):
        """
        Calculate the intersection over union (IoU) of two boxes.

        Args:
            box1 (tuple): The first box.
            box2 (tuple): The second box.

        Returns:
            float: The IoU of the two boxes.
        """
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        union = area1 + area2 - intersection
        return intersection / union if union > 0 else 0

def generate_block_data(folder_path, block_detector):
    for filename in os.listdir(folder_path):
        if filename.endswith('.npz'):
            file_path = os.path.join(folder_path, filename)
            data = np.load(file_path)
            
            lidar_data = data['lidar_data']
            controller_data = data['controller_data']
            frameraw = data['raw_frames']
            simplified_frames = data['simplified_frames']
            counters = data['counters']
            
            red_blocks = []
            green_blocks = []
            for i, frame in enumerate(frameraw):
                framehsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                processed_frame = block_detector.draw_blocks(frame, framehsv)
                red_blocks.append(block_detector.red_block)
                green_blocks.append(block_detector.green_block)
                
                # Show every 10th image with final box result
                if i % 10 == 0:
                    # Draw final red block
                    if block_detector.red_block != [0, 0, 0, 0]:
                        x, y, x2, y2 = block_detector.red_block
                        cv2.rectangle(frame, (x, y), (x2, y2), (0, 0, 255), 2)
                        cv2.putText(frame, 'Final Red Block', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                    
                    # Draw final green block
                    if block_detector.green_block != [0, 0, 0, 0]:
                        x, y, x2, y2 = block_detector.green_block
                        cv2.rectangle(frame, (x, y), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, 'Final Green Block', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    
                    # cv2.imshow('Frame', frame)
                    # cv2.waitKey(0)  # Wait for a key press to proceed

            filename = filename.replace('.npz', '')
            save_path = os.path.join(folder_path, f'{filename}_modified.npz')
            
            np.savez(save_path, lidar_data=lidar_data, controller_data=controller_data, raw_frames=frameraw, simplified_frames=simplified_frames, counters=counters, block_data=np.array([red_blocks, green_blocks]))

# Define the color ranges for green and red in HSV color space
lower_green = np.array([57, 30, 40])
upper_green = np.array([73, 120, 105])

lower_red1 = np.array([175, 105, 80])
upper_red1 = np.array([180, 200, 180])

lower_red2 = np.array([175, 105, 80])
upper_red2 = np.array([180, 200, 180])

lower_black = np.array([15, 0, 0])
upper_black = np.array([170, 55, 70])

# Define the kernel for morphological operations
kernel = np.ones((5, 5), np.uint8)

block_detector = BlockDetector(lower_green, upper_green, lower_red1, upper_red1, lower_red2, upper_red2, kernel)
generate_block_data(r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\03.11.24_Dataset_blocks\blocks_pos2", block_detector)

cv2.destroyAllWindows()