import flask
from flask import Response, jsonify, render_template
import cv2
import numpy as np
import os

class WebServer:
    def __init__(self, shared_frames_list, shared_lidar_lists, port=5000, host='0.0.0.0'):
        self.port = port
        self.host = host
        self.shared_frames_list = shared_frames_list
        self.shared_lidar_list = shared_lidar_lists[0]
        self.interpolated_lidar_list = shared_lidar_lists[1]
        
        self.app = flask.Flask(__name__, static_folder='Website/dist', template_folder='Website/dist', static_url_path='/')
        
        self.app_routes()
        self.start()

        print("Web server initialized")
    
    def start(self):
        print("Web server running")
        self.app.run(host=self.host, port=self.port, debug=True, threaded=True, use_reloader=False)
        print("Web server stopped")
        
    def app_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        @self.app.route('/cam/raw_video_stream')
        def raw_video_stream():
            return Response(self.stream_camera(self.generate_raw_frame), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/cam/simplified_video_stream')
        def simplified_video_stream():
            return Response(self.stream_camera(self.generate_simplified_frame), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/cam/object_video_stream')
        def object_video_stream():
            return Response(self.stream_camera(self.generate_object_frame), mimetype='multipart/x-mixed-replace; boundary=frame')
        
        @self.app.route('/lidar/data')
        def lidar_data():
            if len(self.shared_lidar_list) == 0:
                return jsonify({"error": "No LIDAR data available"})
            
            lidar_data = self.shared_lidar_list[-1]
            
            lidar_data.sort(key=lambda x: x[0])

            return jsonify(lidar_data)
        
        @self.app.route('/lidar/interpolated_data')
        def interpolated_lidar_data():
            if len(self.interpolated_lidar_list) == 0:
                return jsonify({"error": "No interpolated LIDAR data available"})
            
            interpolated_lidar_data = self.interpolated_lidar_list[-1]
            
            print(jsonify(interpolated_lidar_data))
            
            return jsonify(interpolated_lidar_data)
        
        @self.app.route('/log/full_data')
        def log_data():
            logs_folder = 'LOGS'  # Replace with the actual path to the LOGS folder
            log_files = [f for f in os.listdir(logs_folder) if os.path.isfile(os.path.join(logs_folder, f))]
            log_files.sort(key=lambda f: os.path.getmtime(os.path.join(logs_folder, f)), reverse=True)
            if log_files:
                most_recent_file = log_files[0]
                log_data = read_log_file(os.path.join(logs_folder, most_recent_file))
                
                return jsonify(log_data)
            else:
                return jsonify({"error": "No log files found"})
            
        @self.app.route('/log/data/<int:lines>')
        def last_log_data(lines=10):
            # only read the last 10 entries of the most recent log file
            logs_folder = 'LOGS'  # Replace with the actual path to the LOGS folder
            log_files = [f for f in os.listdir(logs_folder) if os.path.isfile(os.path.join(logs_folder, f))]
            log_files.sort(key=lambda f: os.path.getmtime(os.path.join(logs_folder, f)), reverse=True)
            if log_files:
                most_recent_file = log_files[0]
                log_data = read_log_file(os.path.join(logs_folder, most_recent_file))
                
                log_data = log_data.split('\n')[-lines:]
                
                return jsonify(log_data)
            else:
                return jsonify({"error": "No log files found"})

        def read_log_file(file_path):
            with open(file_path, 'r') as file:
                log_data = file.read()
            return log_data
        
    def generate_raw_frame(self):
        frameraw_bytes = self.shared_frames_list[0]
        if frameraw_bytes:
            frame = np.frombuffer(frameraw_bytes, dtype=np.uint8).reshape((480, 853, 3))  # Adjust shape as needed
            return frame
                
    def generate_simplified_frame(self):
        simplified_image_bytes = self.shared_frames_list[1]
        if simplified_image_bytes:
            frame = np.frombuffer(simplified_image_bytes, dtype=np.uint8).reshape((480, 853, 3))  # Adjust shape as needed
            return frame
        
    def generate_object_frame(self):
        object_image_bytes = self.shared_frames_list[2]
        if object_image_bytes:
            frame = np.frombuffer(object_image_bytes, dtype=np.uint8).reshape((480, 853, 3))  # Adjust shape as needed
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
            print("Video closed! 💀")

def compress_image(image):
    height, width = image.shape[:2]
    if height > 360 or width > 630:
        image = cv2.resize(image, (630, 360), interpolation=cv2.INTER_AREA)

    _, encoded_image = cv2.imencode('.jpg', image)
    return encoded_image.tobytes()