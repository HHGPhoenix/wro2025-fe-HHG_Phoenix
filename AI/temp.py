import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import numpy as np

# Define the synthetic dataset with sequences of video frames
class MultiModalDataset(Dataset):
    def __init__(self, num_samples=1000, sequence_length=10):
        self.num_samples = num_samples
        self.sequence_length = sequence_length
        # Synthetic LiDAR data (100-element vector)
        self.lidar_data = np.random.rand(num_samples, 100).astype(np.float32)
        # Synthetic video data (sequence_length x 3x64x64 image)
        self.video_data = np.random.rand(num_samples, sequence_length, 3, 64, 64).astype(np.float32)
        # Synthetic servo target values
        self.servo_data = np.random.rand(num_samples, 1).astype(np.float32)

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        lidar_sample = torch.tensor(self.lidar_data[idx])
        video_sample = torch.tensor(self.video_data[idx])
        servo_value = torch.tensor(self.servo_data[idx])
        return lidar_sample, video_sample, servo_value

# Define the model with RNN for video data
class MultiInputNet(nn.Module):
    def __init__(self, sequence_length=10):
        super(MultiInputNet, self).__init__()
        self.sequence_length = sequence_length
        # LiDAR input processing layers
        self.lidar_fc1 = nn.Linear(100, 64)
        
        # Video input processing layers
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=2, padding=1)
        self.conv3 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1)
        self.fc1 = nn.Linear(64 * 8 * 8, 128)  # Adjust if input size changes
        
        # RNN for processing video sequences
        self.rnn = nn.LSTM(input_size=128, hidden_size=128, num_layers=1, batch_first=True)
        
        # Combined processing layers
        self.combined_fc1 = nn.Linear(192, 64)  # 64 from LiDAR + 128 from RNN output
        self.combined_fc2 = nn.Linear(64, 1)    # Output a single value for the servo
    
    def forward(self, lidar_input, video_input):
        # Process LiDAR input
        lidar_out = torch.relu(self.lidar_fc1(lidar_input))
        
        # Process video input sequence frame-by-frame
        batch_size, seq_len, C, H, W = video_input.size()
        video_input = video_input.view(batch_size * seq_len, C, H, W)
        
        x = torch.relu(self.conv1(video_input))
        x = torch.relu(self.conv2(x))
        x = torch.relu(self.conv3(x))
        x = x.view(x.size(0), -1)  # Flatten the tensor
        video_out = torch.relu(self.fc1(x))
        
        # Reshape for RNN: (batch_size, seq_len, feature_dim)
        video_out = video_out.view(batch_size, seq_len, -1)
        
        # Process video sequence with RNN
        rnn_out, _ = self.rnn(video_out)
        
        # Take the output of the last time step
        rnn_out_last = rnn_out[:, -1, :]
        
        # Combine the processed inputs
        combined_input = torch.cat((lidar_out, rnn_out_last), dim=1)
        combined_out = torch.relu(self.combined_fc1(combined_input))
        servo_out = self.combined_fc2(combined_out)
        
        return servo_out

# Instantiate the model
net = MultiInputNet(sequence_length=10)
print(net)

# Define the loss function and optimizer
criterion = nn.MSELoss()
optimizer = optim.Adam(net.parameters(), lr=0.001)

# Create the dataset and data loader
dataset = MultiModalDataset(num_samples=1000, sequence_length=10)
dataloader = DataLoader(dataset, batch_size=16, shuffle=True)

# Training loop
num_epochs = 10
for epoch in range(num_epochs):
    running_loss = 0.0
    for i, (lidar_inputs, video_inputs, servo_targets) in enumerate(dataloader):
        
        # Zero the parameter gradients
        optimizer.zero_grad()
        
        # Forward pass
        outputs = net(lidar_inputs, video_inputs)
        
        # Compute the loss
        loss = criterion(outputs, servo_targets)
        
        # Backward pass and optimization
        loss.backward()
        optimizer.step()
        
        # Print statistics
        running_loss += loss.item()
        if i % 10 == 9:  # Print every 10 batches
            print(f'Epoch [{epoch + 1}/{num_epochs}], Batch [{i + 1}], Loss: {running_loss / 10:.4f}')
            running_loss = 0.0

print('Finished Training')

# Validation (optional)
net.eval()  # Switch to evaluation mode

validation_dataset = MultiModalDataset(num_samples=200, sequence_length=10)  # Create a validation dataset
validation_loader = DataLoader(validation_dataset, batch_size=16, shuffle=False)

validation_loss = 0.0
with torch.no_grad():
    for lidar_inputs, video_inputs, servo_targets in validation_loader:
        outputs = net(lidar_inputs, video_inputs)
        loss = criterion(outputs, servo_targets)
        validation_loss += loss.item()

print(f'Validation Loss: {validation_loss / len(validation_loader):.4f}')
