def create_model(lidar_input_shape, frame_input_shape, counter_input_shape, tf):
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import Input, Conv2D, MaxPooling2D, Flatten, Dense, Dropout, concatenate
    from tensorflow.keras.layers import GlobalAveragePooling2D, BatchNormalization
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.regularizers import l2
    print("lidar_input_shape: ", lidar_input_shape, "frame_input_shape: ", frame_input_shape, "counter_input_shape: ", counter_input_shape)
    # LIDAR input model with optimized Conv2D layers
    lidar_input = Input(shape=lidar_input_shape, name='lidar_input')
    lidar_conv1 = Conv2D(32, (3, 3), padding='same', activation='relu')(lidar_input)
    lidar_bn1 = BatchNormalization()(lidar_conv1)
    lidar_pool1 = MaxPooling2D((2, 1))(lidar_bn1)  # Adjusted to (2, 1) to avoid dimension issues
    lidar_conv2 = Conv2D(64, (3, 3), padding='same', activation='relu')(lidar_pool1)
    lidar_bn2 = BatchNormalization()(lidar_conv2)
    lidar_pool2 = MaxPooling2D((2, 1))(lidar_bn2)  # Adjusted to (2, 1)
    lidar_conv3 = Conv2D(128, (3, 3), padding='same', activation='relu')(lidar_pool2)
    lidar_bn3 = BatchNormalization()(lidar_conv3)
    lidar_pool3 = MaxPooling2D((2, 1))(lidar_bn3)  # Adjusted to (2, 1)
    lidar_flatten = Flatten()(lidar_pool3)

    # Frame input model using MobileNetV2
    frame_input = Input(shape=frame_input_shape, name='frame_input')
    base_model = MobileNetV2(include_top=False, input_tensor=frame_input, weights='imagenet')
    frame_flatten = GlobalAveragePooling2D()(base_model.output)

    # Counter input model
    counter_input = Input(shape=counter_input_shape, name='counter_input')
    counter_dense1 = Dense(32, activation='relu')(counter_input)
    counter_bn1 = BatchNormalization()(counter_dense1)
    counter_dense2 = Dense(32, activation='relu')(counter_bn1)
    counter_bn2 = BatchNormalization()(counter_dense2)

    # Combine LIDAR, Frame, and Counter inputs
    combined = concatenate([lidar_flatten, frame_flatten, counter_bn2])
    dense1 = Dense(128, activation='relu', kernel_regularizer=l2(0.001))(combined)
    dropout1 = Dropout(0.5)(dense1)
    dense2 = Dense(64, activation='relu', kernel_regularizer=l2(0.001))(dropout1)
    dropout2 = Dropout(0.5)(dense2)
    output = Dense(1, activation='sigmoid')(dropout2)

    model = Model(inputs=[lidar_input, frame_input, counter_input], outputs=output)

    return model