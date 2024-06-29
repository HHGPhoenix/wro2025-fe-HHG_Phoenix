import flask
from flask import Response

class WebServer:
    def __init__(self, camera, port=5000):
        self.port = port
        
        self.app = flask.Flask(__name__)
        
        self.app_routes()
        self.camera = camera
        
    def app_routes(self):
        @self.app.route('/raw_video_stream')
        def video_stream():
            return Response(self.stream_camera(self.generate_raw_frame), mimetype='multipart/x-mixed-replace; boundary=frame')
        
    def process_frames(self):
        while True:
            frameraw, framehsv = self.camera.capture_array()
            
            self.simplified_image = self.camera.simplify_image(framehsv, [0, 255, 0], [255, 0, 0])
            
            self.frameraw = frameraw
        
    def generate_raw_frame(self):
        yield self.frameraw
                
    def generate_simplified_frame(self):
        yield self.simplified_image
        
    def stream_camera(self, image_function):
        try:
            while True:
                frameraw, framehsv = self.camera.capture_array()
                
                if frameraw is not None:
                    
                    # Setzt die Bildqualität auf 75 für eine moderate Kompression
                    encoded_image_raw = compress_image(imageio.imwrite('<bytes>', frameraw, format='.jpg'))
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + encoded_image_raw + b'\r\n')
                    
                else:
                    yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
        finally: 
            print("Video wird geschlossen")
        
def compress_image(image):
    # compress the image to 360p
    return image