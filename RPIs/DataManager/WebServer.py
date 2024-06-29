import flask
from flask import Response
import cv2

class WebServer:
    def __init__(self, camera, lidar, port=5000):
        self.port = port
        
        self.app = flask.Flask(__name__)
        
        self.app_routes()
        self.camera = camera
        self.lidar = lidar
        
    def app_routes(self):
        @self.app.route('/raw_video_stream')
        def raw_video_stream():
            return Response(self.stream_camera(self.generate_raw_frame), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/simplified_video_stream')
        def simplified_video_stream():
            return Response(self.stream_camera(self.generate_simplified_frame), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/polar_plot_stream')
        def polar_plot_stream():
            return Response(self.stream_camera(self.generate_polar_plot), mimetype='multipart/x-mixed-replace; boundary=frame')
        
    def process_frames(self):
        while True:
            frameraw, framehsv = self.camera.capture_array()
            
            self.simplified_image = self.camera.simplify_image(framehsv, [0, 255, 0], [255, 0, 0])
            
            # if len(self.lidar.data_arrays) > 0:
            #     self.polar_plot = self.lidar.polar_plot(self.lidar.data_arrays[-1])
            
            self.frameraw = frameraw
        
    def generate_raw_frame(self):
        return self.frameraw
                
    def generate_simplified_frame(self):
        return self.simplified_image
    
    def generate_polar_plot(self):
        # convert byte array to image
        image = cv2.imdecode(np.frombuffer(self.polar_plot, np.uint8), cv2.IMREAD_COLOR)
        return image
        
    def stream_camera(self, image_function):
        try:
            while True:
                frame = image_function()
                
                if frame is not None:
                    encoded_image = compress_image(frame)
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + encoded_image + b'\r\n')
                    
                else:
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
        finally: 
            print("Video wird geschlossen")

def compress_image(image):
    # Assuming 'image' is a NumPy array representing the image.
    # Compress the image to 360p (if needed, adjust the resizing).
    # Note: You might need to adjust the resizing logic based on your requirements.
    height, width = image.shape[:2]
    if height > 360 or width > 630:
        image = cv2.resize(image, (630, 360), interpolation=cv2.INTER_AREA)

    # Encode the image as JPEG
    _, encoded_image = cv2.imencode('.jpg', image)
    
    # Convert the encoded image to a byte string
    return encoded_image.tobytes()


if __name__ == "__main__":
    from RPIs.Devices.Camera.CameraManager import Camera
    from RPIs.Devices.LIDAR.LIDARManager import LidarSensor
    import numpy as np
    import threading
    
    cam = Camera()
    lidar = LidarSensor("/dev/ttyUSB0")
    
    lidar.reset_sensor()
    lidar.start_sensor()
    tlidar = threading.Thread(target=lidar.read_data)
    tlidar.start()
    
    
    webServer = WebServer(cam, lidar)
    
    tprocess = threading.Thread(target=webServer.process_frames)
    tprocess.start()
    
    webServer.app.run(host='0.0.0.0', port=webServer.port)
    
    
    