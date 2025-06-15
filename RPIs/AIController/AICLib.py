import time
import threading

COM_LOCK = threading.Lock()
COM_HANDLE_ACTIVE = False

class AICU_Logger:
    def __init__(self, client):
        self.client = client

    def debug(self, message):
        self.client.send_message(f'LOG_DEBUG#{message}')

    def info(self, message):
        self.client.send_message(f'LOG_INFO#{message}')

    def warning(self, message):
        self.client.send_message(f'LOG_WARNING#{message}')

    def error(self, message):
        self.client.send_message(f'LOG_ERROR#{message}')

    def critical(self, message):
        self.client.send_message(f'LOG_CRITICAL#{message}')

    def exception(self, message):
        self.client.send_message(f'LOG_EXCEPTION#{message}')

class RemoteFunctions:
    def __init__(self, AIController):
        self.AIController = AIController

###########################################################################
    
    def start(self):
        self.AIController.start()

    def raise_keyboard_interrupt(self):
        self.AIController.stop_with_interrupt = True
        self.AIController.running = False
        
    def set_mode(self, mode):
        self.AIController.logger.info(f'Setting mode to {mode}')
        self.AIController.mode = mode

###########################################################################
        
    def send_heartbeat(self):
        global COM_HANDLE_ACTIVE
        with COM_LOCK:
            if COM_HANDLE_ACTIVE:
                return
            
            COM_HANDLE_ACTIVE = True

        while not self.AIController.initialized:
            time.sleep(0.1)

        if self.AIController.running:
            self.AIController.logger.error('AIController already running!')
            self.AIController.client.send_message("ALREADY_RUNNING")
            COM_HANDLE_ACTIVE = False
            return

        self.AIController.client.send_message('BEAT')
        COM_HANDLE_ACTIVE = False
    
    def receive_heartbeat(self):
        self.AIController.communicationestablisher.received_message = True

    def handle_already_running(self):
        self.AIController.logger.error('AIController already running!')

###########################################################################

    def set_analog_stick_values(self, x, y, rx, ry):
        self.AIController.x = x
        self.AIController.y = y
        self.AIController.rx = rx
        self.AIController.ry = ry
        
    def set_lidar_data(self, interpolated_lidar_data):
        self.AIController.interpolated_lidar_data = interpolated_lidar_data
        
    def set_blocks(self, red_block, green_block):
        self.AIController.block_list[0] = red_block
        self.AIController.block_list[1] = green_block
        
    def failsafe(self, mode):
        self.AIController.failsafe_mode = mode
        
    def set_relative_angle(self, angle):
        self.AIController.relative_angle = angle
        
###########################################################################

    def set_wait_for_parking(self):
        self.AIController.wait_for_parking = True
        self.AIController.logger.info(f'Wait for parking set to: {True}')

    def get_out_of_parking_spot(self, stop_angle, speed, steering_angle):
        self.AIController.logger.info(f'Exiting parking spot with stop angle: {stop_angle}, speed: {speed}, steering angle: {steering_angle}')
        self.AIController.servo.setAngle(self.AIController.servo.mapToServoAngle(steering_angle))
        self.AIController.motor_controller.send_speed(speed)
        
        while abs(self.AIController.motor_controller.yaw) < stop_angle:
            time.sleep(0.1)
            
        self.AIController.motor_controller.send_speed(0.5)
        self.AIController.logger.info('Exited parking spot successfully')
        self.AIController.client.send_message('RELEASE_WAIT_FOR_PARKING')

###########################################################################