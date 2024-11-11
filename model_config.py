def create_model(lidar_input_shape):
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, Reshape
    from tensorflow.keras.models import Model
    from tensorflow.keras.regularizers import l2
    
    # LIDAR input model with LSTM layers
    lidar_input = Input(shape=lidar_input_shape, name='lidar_input')
    reshaped_input = Reshape((lidar_input_shape[0], -1))(lidar_input)  # Reshape to (timesteps, features)
    
    # Reduced number of LSTM layers and units
    lidar_lstm1 = LSTM(32, return_sequences=True)(reshaped_input)
    lidar_lstm2 = LSTM(64)(lidar_lstm1)
    
    # Reduced number of dense units
    dense1 = Dense(64, activation='relu', kernel_regularizer=l2(0.001))(lidar_lstm2)
    dropout1 = Dropout(0.3)(dense1)
    dense2 = Dense(32, activation='relu', kernel_regularizer=l2(0.001))(dropout1)
    dropout2 = Dropout(0.3)(dense2)
    
    output = Dense(1, activation='sigmoid')(dropout2)

    model = Model(inputs=lidar_input, outputs=output)

    return model