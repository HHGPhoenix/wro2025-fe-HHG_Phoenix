import tkinter as tk
import threading
import tensorflow as tf

# Global flag to control training stop
stop_training = False

# Callback to stop training
class StopTrainingCallback(tf.keras.callbacks.Callback):
    def on_batch_end(self, batch, logs=None):
        if stop_training:
            self.model.stop_training = True
            print("Training stopped by user.")

# Dummy TensorFlow model for demonstration
def create_model():
    model = tf.keras.models.Sequential([
        tf.keras.layers.Dense(10, activation='relu', input_shape=(5,)),
        tf.keras.layers.Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

# Function to start the training
def train_model():
    global stop_training
    stop_training = False  # Reset the stop flag
    model = create_model()
    
    # Dummy data for training
    data = tf.random.normal((100, 5))
    labels = tf.random.normal((100, 1))

    # Start training with the callback to stop when requested
    model.fit(data, labels, epochs=1000, callbacks=[StopTrainingCallback()])
    
    print("Training completed.")

# Start training in a separate thread
def start_training():
    training_thread = threading.Thread(target=train_model)
    training_thread.start()

# Stop training by setting the flag
def stop_training_func():
    global stop_training
    stop_training = True

# Tkinter UI setup
root = tk.Tk()
root.title("TensorFlow Training Control")

start_button = tk.Button(root, text="Start Training", command=start_training)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="Stop Training", command=stop_training_func)
stop_button.pack(pady=10)

root.mainloop()
