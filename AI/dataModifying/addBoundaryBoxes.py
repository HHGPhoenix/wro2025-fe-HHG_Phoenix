import cv2
import numpy as np
import os
import glob

input_folder_path = r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\25.12.24 blocks\old\c"
output_folder_path = r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\25.12.24 blocks\new\c_with_green_boxes"

MIN_AREA = 100  # Minimum area threshold for bounding boxes
MERGE_DISTANCE = 30  # Distance threshold to merge nearby bounding boxes

def add_boundary_boxes(image):
    bounding_boxes_red = []
    bounding_boxes_green = []
    
    # convert image to hsv
    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Define color ranges
    lower_green = np.array([57, 30, 40])
    upper_green = np.array([73, 120, 105])
    lower_red1 = np.array([175, 105, 80])
    upper_red1 = np.array([180, 200, 180])
    lower_red2 = np.array([175, 105, 80])
    upper_red2 = np.array([180, 200, 180])
    
    # Create masks
    mask_green = cv2.inRange(image, lower_green, upper_green)
    mask_red1 = cv2.inRange(image, lower_red1, upper_red1)
    mask_red2 = cv2.inRange(image, lower_red2, upper_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)
    
    # Dilate masks
    kernel = np.ones((5, 5), np.uint8)
    mask_green = cv2.dilate(mask_green, kernel, iterations=1)
    mask_red = cv2.dilate(mask_red, kernel, iterations=1)
    
    # Find contours
    contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Process green contours
    for contour in contours_green:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h >= MIN_AREA:
            bounding_boxes_green.append((x, y, x + w, y + h))
    
    # Process red contours
    for contour in contours_red:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h >= MIN_AREA:
            bounding_boxes_red.append((x, y, x + w, y + h))
    
    bounding_boxes_red = merge_nearby_boxes(bounding_boxes_red)
    bounding_boxes_green = merge_nearby_boxes(bounding_boxes_green)
    
    biggest_box_red = get_biggest_box(bounding_boxes_red)
    biggest_box_green = get_biggest_box(bounding_boxes_green)
    
    if biggest_box_red == (0, 0, 1, 1):
        biggest_box_red = (0, 0, 0, 0)
    if biggest_box_green == (0, 0, 1, 1):
        biggest_box_green = (0, 0, 0, 0)
    
    return biggest_box_red, biggest_box_green

def merge_nearby_boxes(boxes):
    if not boxes:
        return []
    
    boxes = np.array(boxes)
    merged_boxes = []
    
    while len(boxes) > 0:
        box = boxes[0]
        x1, y1, x2, y2 = box
        to_merge = []
        
        for i, (x3, y3, x4, y4) in enumerate(boxes):
            if abs(x1 - x3) <= MERGE_DISTANCE and abs(y1 - y3) <= MERGE_DISTANCE:
                to_merge.append(i)
        
        merged_box = (
            min(boxes[to_merge, 0]),
            min(boxes[to_merge, 1]),
            max(boxes[to_merge, 2]),
            max(boxes[to_merge, 3])
        )
        
        merged_boxes.append(merged_box)
        boxes = np.delete(boxes, to_merge, axis=0)
    
    return merged_boxes

def get_biggest_box(boxes):
    if not boxes:
        return (0, 0, 1, 1)
    return max(boxes, key=lambda box: (box[2] - box[0]) * (box[3] - box[1]))

# Process all npz files in the input folder
for file_path in glob.glob(os.path.join(input_folder_path, '*.npz')):
    npz_data = np.load(file_path)
    simplified_images = npz_data['raw_frames']
    lidar_data = npz_data['lidar_data']
    controller_data = npz_data['controller_data']

    all_bounding_boxes_red = []
    all_bounding_boxes_green = []

    for image in simplified_images:
        bounding_boxes_red, bounding_boxes_green = add_boundary_boxes(image)
        all_bounding_boxes_red.append(bounding_boxes_red)
        all_bounding_boxes_green.append(bounding_boxes_green)
        
    all_bounding_boxes_red = np.array(all_bounding_boxes_red)
    all_bounding_boxes_green = np.array(all_bounding_boxes_green)

    output_file_path = os.path.join(output_folder_path, os.path.basename(file_path))
    np.savez(output_file_path, raw_frames=simplified_images, lidar_data=lidar_data, 
             controller_data=controller_data, bounding_boxes_red=all_bounding_boxes_red, 
             bounding_boxes_green=all_bounding_boxes_green)