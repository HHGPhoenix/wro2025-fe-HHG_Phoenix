# Also copy old code and make it better. 
# This should be able to handle up to two cameras and run at stable 10 - 20 fps. 
# It should give out line data, as well as block data for the AI model.

#A class for detecting red and green blocks in the camera stream           
class Camera():
    def __init__(self, video_stream=False, enable_video_writer=False, Utils=None):
        # Variable initialization
        self.freeze = False
        self.frame = None
        self.frame_lock_1 = threading.Lock()
        self.frame_lock_2 = threading.Lock()
        self.video_stream = video_stream
        self.picam2 = Picamera2()
        self.Utils = Utils
        self.enable_video_writer = enable_video_writer
        
        # Configure and start the camera
        config = self.picam2.create_still_configuration(main={"size": (1280, 720)}, raw={"size": (1280, 720)}, controls={"FrameRate": 34})
        self.picam2.configure(config)
        self.picam2.start()
        self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        
        # Define the color ranges for green and red in HSV color space
        self.lower_green = np.array([53, 100, 40])
        self.upper_green = np.array([93, 220, 150])

        self.lower_red1 = np.array([0, 160, 120])
        self.upper_red1 = np.array([5, 220, 200])

        self.lower_red2 = np.array([173, 160, 100])
        self.upper_red2 = np.array([180, 220, 200])

        # Define the kernel for morphological operations
        self.kernel = np.ones((7, 7), np.uint8)
        self.desired_distance_wall = -1
        self.block_distance = -1
        
        self.edge_distances = []
        self.avg_edge_distance = 0
        
        self.focal_length = 373.8461538461538
        self.known_height = 0.1
        self.camera_angle = 15
        self.distance_multiplier = 2.22
    
    #Get the coordinates of the blocks in the camera stream
    def get_coordinates(self):
        frameraw = self.picam2.capture_array()
        
        frameraw = cv2.cvtColor(frameraw, cv2.COLOR_BGR2RGB)
        frame = frameraw.copy()
        
        # cutoff frames
        frame = frame[250:, :]

        # Convert the image from BGR to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Create a mask of pixels within the green color range
        mask_green = cv2.inRange(hsv, self.lower_green, self.upper_green)

        # Create a mask of pixels within the red color range
        mask_red1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask_red2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        # Dilate the masks to merge nearby areas
        mask_green = cv2.dilate(mask_green, self.kernel, iterations=1)
        mask_red = cv2.dilate(mask_red, self.kernel, iterations=1)

        # Find contours in the green mask
        contours_green, _ = cv2.findContours(mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Find contours in the red mask
        contours_red, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        #print(f"middle hsv: {hsv[0, 360]}, inverted: {hsv[300, 1000]}")
        
        cv2.circle(frame, (640, 720), 10, (255, 0, 0), -1)
        cv2.putText(frame, f"{self.desired_distance_wall}", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 4)
        cv2.putText(frame, f"Freeze: {self.freeze}", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 4)
        cv2.putText(frame, f"Distance: {self.block_distance}", (700, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 4)
        #cv2.circle(frame, (1000, 300), 10, (255, 0, 0), -1)
        
        block_array = []

        # Process each green contour
        for contour in contours_green:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 20 and h > 50:  # Only consider boxes larger than 50x50
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, 'Green Object', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
                block_array.append({'color': 'green', 'x': x, 'y': y, 'w': w, 'h': h, 'mx': x+w/2, 'my': y+h/2, 'size': w*h, 'distance': self.get_distance_to_block({'x': x, 'y': y, 'w': w, 'h': h})})
                cv2.line(frame, (640, 720), (int(x+w/2), int(y+h/2)), (0, 255, 0), 2)

        # Process each red contour
        for contour in contours_red:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 20 and h > 50:  # Only consider boxes larger than 50x50
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, 'Red Object', (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,0,255), 2)
                block_array.append({'color': 'red', 'x': x, 'y': y, 'w': w, 'h': h, 'mx': x+w/2, 'my': y+h/2, 'size': w*h, 'distance': self.get_distance_to_block({'x': x, 'y': y, 'w': w, 'h': h})})
                cv2.line(frame, (640, 720), (int(x+w/2), int(y+h/2)), (0, 0, 255), 2)
            
        return block_array, frame, frameraw
    
    
    def get_distance_to_block(self, block):
        # Calculate the distance to the block
        image_distance = (self.focal_length * self.known_height * cos(radians(self.camera_angle))) / block['h']
        self.real_distance = image_distance * self.distance_multiplier
        
        self.block_distance = self.real_distance * 100
        return self.real_distance * 100
        
         
    # Function running in a new thread that constantly updates the coordinates of the blocks in the camera stream
    def process_blocks(self):
        self.video_writer = None
        self.frames = [None] * 3

        while True:
            self.block_array, framenormal, frameraw = self.get_coordinates()
            framebinary = self.get_edges(frameraw)

            self.frames[0] = framenormal
            self.frames[1] = framebinary
            self.frames[2] = frameraw

            if self.video_writer is None and self.enable_video_writer:
                # Create a VideoWriter object to save the frames as an mp4 file
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                self.video_writer = cv2.VideoWriter(f'./videos/output_{str(uuid.uuid4())}.mp4', fourcc, 20, (frameraw.shape[1], frameraw.shape[0]), True)

            # Write the frame to the video file
            if self.enable_video_writer:
                self.video_writer.write(frameraw)


    # Start a new thread for processing the camera stream
    def start_processing(self):
        thread = threading.Thread(target=self.process_blocks)
        thread.daemon = False
        thread.start()
    
    
    # Compress the video frames for the webstream    
    def compress_frame(self, frame):
        dimensions = len(frame.shape)
        if dimensions == 3:
            height, width, _ = frame.shape
        elif dimensions == 2:
            height, width = frame.shape
        else:
            raise ValueError(f"Unexpected number of dimensions in frame: {dimensions}")
        new_height = 180
        new_width = int(new_height * width / height)
        frame = cv2.resize(frame, (new_width, new_height))
        return frame


    # Generate the frames for the webstream
    def video_frames(self, frame_type):
        if self.video_stream:
            while True:
                if frame_type == 'type1' and self.frames[0] is not None:
                    with self.frame_lock_1:
                        frame = self.compress_frame(self.frames[0])
                        (flag, encodedImage) = cv2.imencode(".jpg", frame)
                        yield (b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')
                elif frame_type == 'type2' and self.frames[1] is not None:
                    with self.frame_lock_2:
                        frame = self.compress_frame(self.frames[1])
                        (flag, encodedImage) = cv2.imencode(".jpg", frame)
                        yield (b'--frame\r\n'
                            b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')