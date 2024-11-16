import cv2
import numpy as np

file_path = r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\03.11.24_Dataset_blocks\blocks_pos2\run_data_c_ro_go.npz"
output_file_path = r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\03.11.24_Dataset_blocks\blocks_pos2_with_boxes\run_data_c_ro_go_with_boxes.npz"
npz_data = np.load(file_path)
simplified_images = npz_data['simplified_frames']
lidar_data = npz_data['lidar_data']
controller_data = npz_data['controller_data']
counters = npz_data['counters']

MIN_AREA = 100  # Minimum area threshold for bounding boxes
MERGE_DISTANCE = 30  # Distance threshold to merge nearby bounding boxes

def add_boundary_boxes(image):
    bounding_boxes_red = []
    bounding_boxes_green = []
    
    # Find red and green contours
    red = np.array([0, 0, 255])
    green = np.array([0, 255, 0])
    red_mask = cv2.inRange(image, red, red)
    green_mask = cv2.inRange(image, green, green)
    red_contours, _ = cv2.findContours(red_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    green_contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Save bounding boxes
    for contour in red_contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h >= MIN_AREA:
            bounding_boxes_red.append((x, y, w, h))
    
    for contour in green_contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h >= MIN_AREA:
            bounding_boxes_green.append((x, y, w, h))
    
    bounding_boxes_red = merge_nearby_boxes(bounding_boxes_red)
    bounding_boxes_green = merge_nearby_boxes(bounding_boxes_green)
    
    return bounding_boxes_red, bounding_boxes_green

def merge_nearby_boxes(boxes):
    if not boxes:
        return []
    
    boxes = np.array(boxes)
    merged_boxes = []
    
    while len(boxes) > 0:
        box = boxes[0]
        x1, y1, w1, h1 = box
        to_merge = []
        
        for i, (x2, y2, w2, h2) in enumerate(boxes):
            if abs(x1 - x2) <= MERGE_DISTANCE and abs(y1 - y2) <= MERGE_DISTANCE:
                to_merge.append(i)
        
        merged_box = (
            min(boxes[to_merge, 0]),
            min(boxes[to_merge, 1]),
            max(boxes[to_merge, 0] + boxes[to_merge, 2]) - min(boxes[to_merge, 0]),
            max(boxes[to_merge, 1] + boxes[to_merge, 3]) - min(boxes[to_merge, 1])
        )
        
        merged_boxes.append(merged_box)
        boxes = np.delete(boxes, to_merge, axis=0)
    
    return merged_boxes

# Process all images and collect bounding boxes
all_bounding_boxes_red = []
all_bounding_boxes_green = []

for image in simplified_images:
    bounding_boxes_red, bounding_boxes_green = add_boundary_boxes(image)
    all_bounding_boxes_red.append(bounding_boxes_red)
    all_bounding_boxes_green.append(bounding_boxes_green)

# Convert lists to object arrays
all_bounding_boxes_red = np.array(all_bounding_boxes_red, dtype=object)
all_bounding_boxes_green = np.array(all_bounding_boxes_green, dtype=object)

# Save the bounding boxes once after processing all images
np.savez(output_file_path, simplified_frames=simplified_images, lidar_data=lidar_data, 
         controller_data=controller_data, counters=counters, bounding_boxes_red=all_bounding_boxes_red, 
         bounding_boxes_green=all_bounding_boxes_green)