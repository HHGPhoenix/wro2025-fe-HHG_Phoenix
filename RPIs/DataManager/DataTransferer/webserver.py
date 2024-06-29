import flask
from flask import Response
import cv2
import numpy as np

class WebServer:
    def __init__(self, shared_list, port=5000, host='0.0.0.0'):
        self.port = port
        self.host = host
        self.shared_list = shared_list
        
        self.app = flask.Flask(__name__)
        
        self.app_routes()

        print("Web server initialized")

        self.run()
    
    def run(self):
        print("Web server running")
        self.app.run(host=self.host, port=self.port, debug=True, threaded=True, use_reloader=False)
        print("Web server stopped")
        
    def app_routes(self):
        @self.app.route('/raw_video_stream')
        def raw_video_stream():
            return Response(self.stream_camera(self.generate_raw_frame), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/simplified_video_stream')
        def simplified_video_stream():
            return Response(self.stream_camera(self.generate_simplified_frame), mimetype='multipart/x-mixed-replace; boundary=frame')
        
    def generate_raw_frame(self):
        frameraw_bytes = self.shared_list[0]
        if frameraw_bytes:
            frame = np.frombuffer(frameraw_bytes, dtype=np.uint8).reshape((480, 640, 3))  # Adjust shape as needed
            return frame
                
    def generate_simplified_frame(self):
        simplified_image_bytes = self.shared_list[1]
        if simplified_image_bytes:
            frame = np.frombuffer(simplified_image_bytes, dtype=np.uint8).reshape((480, 640, 3))  # Adjust shape as needed
            return frame
    
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
            print("Video closed 💀")

def compress_image(image):
    height, width = image.shape[:2]
    if height > 360 or width > 630:
        image = cv2.resize(image, (630, 360), interpolation=cv2.INTER_AREA)

    _, encoded_image = cv2.imencode('.jpg', image)
    return encoded_image.tobytes()
