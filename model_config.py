def create_model(lidar_input_shape, red_blocks_input_shape, green_blocks_input_shape):
    from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, Reshape, Concatenate, BatchNormalization
    from tensorflow.keras.models import Model
    from tensorflow.keras.regularizers import l2
    
    # LIDAR input model with LSTM layers
    lidar_input = Input(shape=lidar_input_shape, name='lidar_input')
    reshaped_lidar_input = Reshape((lidar_input_shape[0], -1))(lidar_input)  # Reshape to (timesteps, features)
    
    lidar_lstm1 = LSTM(64, return_sequences=True)(reshaped_lidar_input)
    lidar_bn1 = BatchNormalization()(lidar_lstm1)
    lidar_lstm2 = LSTM(128, return_sequences=True)(lidar_bn1)
    lidar_bn2 = BatchNormalization()(lidar_lstm2)
    lidar_lstm3 = LSTM(128)(lidar_bn2)
    
    # Red block data input model with LSTM layers
    red_block_input = Input(shape=red_blocks_input_shape, name='red_block_input')
    reshaped_red_block_input = Reshape((red_blocks_input_shape, -1))(red_block_input)  # Reshape to (timesteps, features)
    
    red_block_lstm1 = LSTM(64, return_sequences=True)(reshaped_red_block_input)
    red_block_bn1 = BatchNormalization()(red_block_lstm1)
    red_block_lstm2 = LSTM(128, return_sequences=True)(red_block_bn1)
    red_block_bn2 = BatchNormalization()(red_block_lstm2)
    red_block_lstm3 = LSTM(128)(red_block_bn2)
    
    # Green block data input model with LSTM layers
    green_block_input = Input(shape=green_blocks_input_shape, name='green_block_input')
    reshaped_green_block_input = Reshape((green_blocks_input_shape, -1))(green_block_input)  # Reshape to (timesteps, features)
    
    green_block_lstm1 = LSTM(64, return_sequences=True)(reshaped_green_block_input)
    green_block_bn1 = BatchNormalization()(green_block_lstm1)
    green_block_lstm2 = LSTM(128, return_sequences=True)(green_block_bn1)
    green_block_bn2 = BatchNormalization()(green_block_lstm2)
    green_block_lstm3 = LSTM(128)(green_block_bn2)
    
    # Concatenate LIDAR and block data
    concatenated_blocks = Concatenate()([red_block_lstm3, green_block_lstm3])
    concatenated = Concatenate()([lidar_lstm3, concatenated_blocks])
    
    # Dense layers
    dense1 = Dense(128, activation='relu', kernel_regularizer=l2(0.001))(concatenated)
    dropout1 = Dropout(0.4)(dense1)
    dense2 = Dense(64, activation='relu', kernel_regularizer=l2(0.001))(dropout1)
    dropout2 = Dropout(0.4)(dense2)
    
    output = Dense(1, activation='sigmoid')(dropout2)

    model = Model(inputs=[lidar_input, red_block_input, green_block_input], outputs=output)

    return model