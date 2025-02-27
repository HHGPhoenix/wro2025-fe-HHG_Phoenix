import cv2
import numpy as np
import os
import glob

input_folder_path = r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\V3\Datasets\blocks\26.01.25_blocks"
output_folder_path = r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\V3\Datasets\blocks\26.01.25_blocks_new_bounding_boxes"

MIN_AREA = 100  # Minimum area threshold for bounding boxes
MERGE_DISTANCE = 30  # Distance threshold to merge nearby bounding boxes

def add_boundary_boxes(image):
    bounding_boxes_red = []
    bounding_boxes_green = []
    
    # convert image to hsv
    image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    lower_green = np.array([54, 139, 77])
    upper_green = np.array([59, 170, 113])

    lower_red1 = np.array([0, 142, 95])
    upper_red1 = np.array([5, 207, 112])

    lower_red2 = np.array([0, 142, 95])
    upper_red2 = np.array([5, 207, 112])

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
            bounding_boxes_green.append((x + w // 2, y + h // 2, w, h))
    
    # Process red contours
    for contour in contours_red:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h >= MIN_AREA:
            bounding_boxes_red.append((x + w // 2, y + h // 2, w, h))
    
    bounding_boxes_red = merge_nearby_boxes(bounding_boxes_red)
    bounding_boxes_green = merge_nearby_boxes(bounding_boxes_green)
    
    biggest_boxes_red = get_biggest_boxes(bounding_boxes_red)
    biggest_boxes_green = get_biggest_boxes(bounding_boxes_green)
    
    cv2.rectangle(image, (biggest_boxes_red[0][0], biggest_boxes_red[0][1]), (biggest_boxes_red[0][2], biggest_boxes_red[0][3]), (0, 0, 255), 2)
    cv2.rectangle(image, (biggest_boxes_red[1][0], biggest_boxes_red[1][1]), (biggest_boxes_red[1][2], biggest_boxes_red[1][3]), (0, 0, 255), 2)
    cv2.rectangle(image, (biggest_boxes_green[0][0], biggest_boxes_green[0][1]), (biggest_boxes_green[0][2], biggest_boxes_green[0][3]), (0, 255, 0), 2)
    cv2.rectangle(image, (biggest_boxes_green[1][0], biggest_boxes_green[1][1]), (biggest_boxes_green[1][2], biggest_boxes_green[1][3]), (0, 255, 0), 2)
    
    # cv2.imshow('image', cv2.cvtColor(image, cv2.COLOR_HSV2BGR))
    # cv2.waitKey(0)
        
    return biggest_boxes_red, biggest_boxes_green

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

def get_biggest_boxes(boxes):
    if not boxes:
        return [(0, 0, 0, 0), (0, 0, 0, 0)]
    sorted_boxes = sorted(boxes, key=lambda box: (box[2] - box[0]) * (box[3] - box[1]), reverse=True)
    return sorted_boxes[:2] if len(sorted_boxes) >= 2 else sorted_boxes + [(0, 0, 0, 0)]

# Process all npz files in the input folder and its subfolders
for root, _, files in os.walk(input_folder_path):
    for file in files:
        if file.endswith('.npz'):
            file_path = os.path.join(root, file)
            print(f'Processing {file_path}...')
            npz_data = np.load(file_path)
            raw_frames = npz_data['raw_frames']
            lidar_data = npz_data['lidar_data']
            controller_data = npz_data['controller_data']

            all_bounding_boxes_red = []
            all_bounding_boxes_green = []

            for image in raw_frames:
                bounding_boxes_red, bounding_boxes_green = add_boundary_boxes(image)
                all_bounding_boxes_red.append(bounding_boxes_red)
                all_bounding_boxes_green.append(bounding_boxes_green)
                
            all_bounding_boxes_red = np.array(all_bounding_boxes_red)
            all_bounding_boxes_green = np.array(all_bounding_boxes_green)

            # Create corresponding subfolder in the output folder
            relative_path = os.path.relpath(root, input_folder_path)
            output_subfolder_path = os.path.join(output_folder_path, relative_path)
            os.makedirs(output_subfolder_path, exist_ok=True)

            output_file_path = os.path.join(output_subfolder_path, file)
            np.savez(output_file_path, raw_frames=raw_frames, lidar_data=lidar_data, 
                     controller_data=controller_data, bounding_boxes_red=all_bounding_boxes_red, 
                     bounding_boxes_green=all_bounding_boxes_green)