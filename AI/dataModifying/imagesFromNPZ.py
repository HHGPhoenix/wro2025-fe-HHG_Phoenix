import numpy as np
import matplotlib.pyplot as plt
import cv2

npz_path = r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\03.11.24_Dataset_blocks\blocks_pos2\run_data_cc_ro_go.npz"
output_path = r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\CNN_block_detection\testing_data"

npz_data = np.load(npz_path)
raw_frame_bytes = npz_data["raw_frames"]
raw_frames = np.array([np.frombuffer(frame, dtype=np.uint8).reshape((100, 213, 3)) for frame in raw_frame_bytes])

# Convert BGR to RGB and save the frames as individual images
for i, frame in enumerate(raw_frames):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image_path = f"{output_path}/frame_{i}.png"
    plt.imsave(image_path, rgb_frame)