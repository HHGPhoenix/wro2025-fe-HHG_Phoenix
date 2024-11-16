import numpy as np
import matplotlib.pyplot as plt
import cv2
import os
import glob

input_path = r"D:\Onedrive HHG\OneDrive - Helmholtz-Gymnasium\Dokumente\.Libery\Code\Flix,Emul Ordner\WRO2025\PrototypeV2\03.11.24_Dataset_blocks\blocks_pos2"
output_path = r"D:\Onedrive HHG\OneDrive - Helmholtz-Gymnasium\Dokumente\.Libery\Code\Flix,Emul Ordner\WRO2025\PrototypeV2\CNN_block_detection\16.11._more_data - unfinished"

# Check if the input path is a directory or a file
if os.path.isdir(input_path):
    # Get all .npz files in the folder
    npz_files = glob.glob(os.path.join(input_path, "*.npz"))
elif os.path.isfile(input_path) and input_path.endswith('.npz'):
    # Single .npz file
    npz_files = [input_path]
else:
    raise ValueError("The input path must be a directory or a .npz file")

for npz_file in npz_files:
    npz_data = np.load(npz_file)
    raw_frame_bytes = npz_data["raw_frames"]
    raw_frames = np.array([np.frombuffer(frame, dtype=np.uint8).reshape((100, 213, 3)) for frame in raw_frame_bytes])
    
    # Get the base file name without extension
    base_name = os.path.splitext(os.path.basename(npz_file))[0]
    
    # Convert BGR to RGB and save the frames as individual images
    for i, frame in enumerate(raw_frames):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_name = f"{base_name}-{i}.png"
        image_path = os.path.join(output_path, image_name)
        plt.imsave(image_path, rgb_frame)