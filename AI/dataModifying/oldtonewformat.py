import numpy as np
import pandas as pd

file_path = r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\15.09.25_Dataset_no_blocks\run_data_51a1f119-f9ba-4f30-96bf-5cc83a89d59a_2024-09-15.npz"

data = np.load(file_path)

lidar_dataframe = pd.DataFrame(data['lidar_data'])
lidar_dataframe = lidar_dataframe[(lidar_dataframe["angle"] < 140) | (lidar_dataframe["angle"] > 220)]
lidar_data = lidar_dataframe.to_numpy()

frame_array = np.array()
for frame in data['frame_data']:
    frame = np.frombuffer(frame, dtype=np.uint8).reshape((110, 213, 3))
    frame = frame[10:, :, :]
    frame_array.append(frame)

np.savez(r"C:\Users\felix\OneDrive - Helmholtz-Gymnasium\Flix,Emul Ordner\WRO2025\PrototypeV2\15.09.25_Dataset_no_blocks\run_data_51a1f119-f9ba-4f30-96bf-5cc83a89d59a_2024-09-15.npz", lidar_data=lidar_data, frame_data=frame_array)