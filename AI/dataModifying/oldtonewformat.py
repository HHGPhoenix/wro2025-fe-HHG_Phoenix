import numpy as np
import pandas as pd

file_path = r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\15.09.25_Dataset_no_blocks\run_data_b7f2b4a9-78e9-490e-9ff4-14152423a012_2024-09-15.npz"

data = np.load(file_path)

controller_data = data['controller_data']
counters = data['counters']

new_lidar_data = []
for lidar_array in data['lidar_data']:
    angles = lidar_array[:, 0]
    distances = lidar_array[:, 1]
    lidar_dataframe = pd.DataFrame({"angle": angles, "distance": distances})
    lidar_dataframe = lidar_dataframe[(lidar_dataframe["angle"] < 135) | (lidar_dataframe["angle"] > 237)]
    lidar_data = lidar_dataframe.to_numpy()
    new_lidar_data.append(lidar_data)
new_lidar_data = np.array(new_lidar_data)

raw_frame_array = []
for frame in data['raw_frames']:
    frame = np.frombuffer(frame, dtype=np.uint8).reshape((110, 213, 3))
    frame = frame[10:, :, :]
    raw_frame_array.append(frame)
raw_frame_array = np.array(raw_frame_array)

simplified_frame_array = []
for frame in data['simplified_frames']:
    frame = np.frombuffer(frame, dtype=np.uint8).reshape((110, 213, 3))
    frame = frame[10:, :, :]
    print(frame.shape)
    simplified_frame_array.append(frame)
simplified_frame_array = np.array(simplified_frame_array)

np.savez(r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\15.09.25_Dataset_no_blocks\run_data_b7f2b4a9-78e9-490e-9ff4-14152423a012_2024-09-15_new_format.npz", 
         lidar_data=new_lidar_data, raw_frames=raw_frame_array, simplified_frames=simplified_frame_array, controller_data=controller_data, counters=counters)