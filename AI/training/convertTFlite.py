import tensorflow as tf

# Load the H5 model
h5_model_path = r"D:\Developement\wro2025-fe-HHG_Phoenix\siqmoid_model.h5"
model = tf.keras.models.load_model(h5_model_path)

# Convert the model to TFLite format
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Save the converted model to a file
tflite_model_path = r"D:\Developement\wro2025-fe-HHG_Phoenix\siqmoid_model.tflite"
with open(tflite_model_path, 'wb') as f:
    f.write(tflite_model)

print(f"Model converted and saved to {tflite_model_path}")