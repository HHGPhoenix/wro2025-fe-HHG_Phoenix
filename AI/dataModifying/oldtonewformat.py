import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import time
import os
import argparse
from pathlib import Path
from tqdm import tqdm

def process_file(input_file, output_file, visualize=False):
    print(f"Processing: {input_file}")
    data = np.load(input_file)

    controller_data = data['controller_data']
    lidar_data = data['lidar_data']
    raw_frames = data['raw_frames']
    bounding_boxes_green = data['bounding_boxes_green']
    bounding_boxes_red = data['bounding_boxes_red']

    # Keep a copy of the original full lidar_data before modifying it
    original_lidar_data = data['lidar_data'].copy()

    # get image size from your first frame
    H, W, _ = raw_frames[0].shape
    lidar_data = lidar_data[..., :2]  # Extract only angle and distance for processing
    F, P, _ = lidar_data.shape

    # initialise coloured array
    colored = np.zeros((F, P, 3), dtype=float)
    colored[..., :2] = lidar_data
    colored[..., 2]  = 0.5   # no‐block default

    # Camera center offset angle (adjust based on your hardware setup)
    camera_center_offset = 0  # degrees - change if camera isn't aligned with LiDAR 0°

    # define your camera's horizontal FOV in degrees
    cam_fov_deg = 120.0

    # Calculate camera FOV bounds with the offset
    cam_min = camera_center_offset - cam_fov_deg/2
    cam_max = camera_center_offset + cam_fov_deg/2

    # pull out the beam angles (deg) from the LiDAR
    # (we assume every frame uses the same beam angles, so grab frame 0)
    lidar_angles = lidar_data[0, :, 0]  
    # normalize to [-180, 180)
    lidar_angles = (lidar_angles + 180) % 360 - 180
    valid_beams = (lidar_angles >= cam_min) & (lidar_angles <= cam_max)

    # Create a more precise mapping function for angles to pixels
    def map_angle_to_pixel(angle, min_angle, max_angle, image_width):
        """Map angle more precisely to pixel coordinate using improved interpolation"""
        # Normalize angle to [0,1] range within FOV
        normalized = (angle - min_angle) / (max_angle - min_angle)
        # Convert to pixel coordinate - reversed to fix mirroring
        return int(round((1 - normalized) * (image_width - 1)))

    # Map beam angles to image pixels with improved function
    u_center = np.full(P, -1, dtype=int)
    for i in np.where(valid_beams)[0]:
        u_center[i] = map_angle_to_pixel(lidar_angles[i], cam_min, cam_max, W)

    # Save the original beam count before calculating parameters
    beam_count = P
    valid_count = valid_beams.sum()

    # Use a fixed pixel width for each beam for more consistent mapping
    pixel_width = 3  # Adjust based on testing for best results
    u_min_arr = np.full(P, -1, dtype=int)
    u_max_arr = np.full(P, -1, dtype=int)
    # Only set min/max for valid beams
    for i in np.where(valid_beams)[0]:
        u_min_arr[i] = max(0, u_center[i] - pixel_width//2)
        u_max_arr[i] = min(W-1, u_center[i] + pixel_width//2)

    print(f"  Valid beams: {valid_count} out of {beam_count} total beams")
    print(f"  lidar_angles: {lidar_angles[valid_beams].min():.1f}..{lidar_angles[valid_beams].max():.1f} degrees")

    # Improved algorithm for beam-box intersection
    for f in range(F):
        # Reset all points to default (no block)
        colored[f, :, 0] = 0.0
        colored[f, :, 1] = 0.0
        colored[f, :, 2] = 0.5
        
        # GREEN boxes
        for xmid, ymid, bw, bh in bounding_boxes_green[f]:
            if bw <= 0 or bh <= 0: continue
            # Use box coordinates directly without mirroring
            # since the beam positions are already mirrored
            xmin = int(xmid - bw/2)
            xmax = int(xmid + bw/2)
            
            # Check for beam-box overlap using improved algorithm
            for i in np.where(valid_beams)[0]:
                if max(u_min_arr[i], xmin) <= min(u_max_arr[i], xmax):
                    # There is overlap between beam and box
                    colored[f, i, 2] = 0.0

        # RED boxes - similar improved algorithm
        for xmid, ymid, bw, bh in bounding_boxes_red[f]:
            if bw <= 0 or bh <= 0: continue
            # Use box coordinates directly without mirroring
            xmin = int(xmid - bw/2)
            xmax = int(xmid + bw/2)
            
            # Check for overlap with each valid beam
            for i in np.where(valid_beams)[0]:
                if max(u_min_arr[i], xmin) <= min(u_max_arr[i], xmax):
                    # There is overlap between beam and box
                    colored[f, i, 2] = 1.0

    # First determine how many channels the original data had
    original_channels = original_lidar_data.shape[2]

    # Create the merged dataset with one additional channel for color
    merged_lidar_data = np.zeros((F, P, original_channels + 1), dtype=float)
    merged_lidar_data[..., :original_channels] = original_lidar_data  # Copy all original channels
    merged_lidar_data[..., original_channels] = colored[..., 2]      # Add the color channel

    if visualize:
        # Create figure outside the loop (only once)
        plt.figure(figsize=(10,5))
        ax_img = plt.subplot(1,2,1)
        ax_lidar = plt.subplot(1,2,2, projection='polar')

        # Loop through all frames
        for f in range(F):
            img = raw_frames[f]
            merged_frame = merged_lidar_data[f]  # Get complete data for this frame
            print(f"Analyzing Frame {f}/{F}")

            # Use data from the merged dataset
            angles = np.deg2rad(merged_frame[:, 0]) + np.deg2rad(90)  # First channel is still angle
            dists = merged_frame[:, 1]                               # Second channel is still distance
            vals = merged_frame[:, -1]                               # Last channel is our calculated color

            # map 0→green, 0.5→gray, 1→red
            cmap = np.array(['green', 'gray', 'red'])
            idx = (vals * 2).astype(int)      # 0→0, .5→1, 1→2
            pcs = cmap[idx]

            # Clear the previous frame's content
            ax_img.clear()
            ax_lidar.clear()

            # plot the image with bounding boxes overlay
            ax_img.imshow(img)
            ax_img.set_title(f'RGB Frame {f}/{F}')
            ax_img.axis('off')

            # Draw red bounding boxes
            for xmiddle, ymiddle, width, height in bounding_boxes_red[f]:
                xmiddle_px = xmiddle
                ymiddle_px = ymiddle
                width_px = width
                height_px = height
                xmin_px = xmiddle_px - width_px // 2
                ymin_px = ymiddle_px - height_px // 2
                rect = patches.Rectangle((xmin_px, ymin_px),
                                        width_px, height_px,
                                        linewidth=2, edgecolor='red', facecolor='none')
                ax_img.add_patch(rect)

            # Draw green bounding boxes
            for xmiddle, ymiddle, width, height in bounding_boxes_green[f]:
                xmiddle_px = xmiddle
                ymiddle_px = ymiddle
                width_px = width
                height_px = height
                xmin_px = xmiddle_px - width_px // 2
                ymin_px = ymiddle_px - height_px // 2
                rect = patches.Rectangle((xmin_px, ymin_px),
                                        width_px, height_px,
                                        linewidth=2, edgecolor='green', facecolor='none')
                ax_img.add_patch(rect)

            # Plot LiDAR data
            ax_lidar.scatter(angles, dists, c=pcs, s=5)
            ax_lidar.set_title('LiDAR Polar Plot (+90° rotated)')
            
            plt.suptitle(f'Frame {f}/{F}')
            plt.tight_layout()
            plt.draw()  # Update the plot
            plt.pause(0.1)  # Short pause to update the display
            
            time.sleep(0.1)  # Allow time for the plot to update

        # After the loop finishes, show the final plot (optional)
        plt.show()

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Save out with the new channel
    np.savez(
        output_file,
        lidar_data=merged_lidar_data,
        lidar_data_colored=colored,
        raw_frames=raw_frames,
        controller_data=controller_data,
        bounding_boxes_green=bounding_boxes_green,
        bounding_boxes_red=bounding_boxes_red
    )
    print(f"  Saved processed data to: {output_file}")

def main():
    input_dir = Path(r"/mnt/6df1213e-09b3-4ece-aad7-5db3749c9296/RunData/26.01.25_blocks_new_bounding_boxes")
    output_dir = Path(r"/mnt/6df1213e-09b3-4ece-aad7-5db3749c9296/RunData/26.01.25_blocks_colored_data")
    visualize = False

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all .npz files in input directory (recursively)
    npz_files = list(input_dir.glob("**/*.npz"))
    print(f"Found {len(npz_files)} NPZ files to process")
    
    for input_file in tqdm(npz_files):
        # Create the same directory structure in output_dir
        rel_path = input_file.relative_to(input_dir)
        output_file = output_dir / rel_path.with_name(f"{input_file.stem}_processed.npz")
        
        # Process the file
        try:
            process_file(input_file, output_file, visualize=visualize)
        except Exception as e:
            print(f"Error processing {input_file}: {e}")
            
    print(f"Processing complete. Results saved to {output_dir}")

if __name__ == "__main__":
    main()