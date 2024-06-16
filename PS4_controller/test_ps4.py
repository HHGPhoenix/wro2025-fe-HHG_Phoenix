import evdev
from evdev import InputDevice, categorize, ecodes
import time
from USB_communication_handler import USBCommunication
import RPi.GPIO as GPIO
from RobotCarClasses import Utility

Utils = Utility()
Utils.setupLog()
usb_comm = USBCommunication(Utils)
ESPHoldDistance, ESPHoldSpeed = usb_comm.initNodeMCUs()

# Replace '/dev/input/eventX' with your actual device path
device_path = '/dev/input/event4'
device = InputDevice(device_path)

# Analog stick axis codes for PS4 controller
AXIS_CODES = {
    ecodes.ABS_X: 'left_analog_x',
    ecodes.ABS_Y: 'left_analog_y',
    ecodes.ABS_RX: 'right_analog_x',
    ecodes.ABS_RY: 'right_analog_y'
}

analog_stick_values = {
    'left_analog_x': 0,
    'left_analog_y': 0,
    'right_analog_x': 0,
    'right_analog_y': 0
}

# Set up the GPIO for the servo
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)
pwm = GPIO.PWM(17, 50)  # GPIO 17 for PWM with 50Hz
pwm.start(7.5)  # Initialization at neutral position (7.5% duty cycle corresponds to 90 degrees)

print(f"Reading events from {device_path} (Press Ctrl+C to stop)...")
old_value = 0

try:
    usb_comm.sendMessage("START", ESPHoldSpeed)
    for event in device.read_loop():
        if event.type == ecodes.EV_ABS and event.code in AXIS_CODES:
            analog_stick_values[AXIS_CODES[event.code]] = event.value
            print(analog_stick_values)
            
            # Control the servo based on the left analog stick's x-axis
            if AXIS_CODES[event.code] == 'left_analog_x':
                # Map the value from 0-255 to 5-10 for duty cycle
                value2 = (event.value / 255) * 5 + 5
                pwm.ChangeDutyCycle(value2)
                
            if AXIS_CODES[event.code] == 'left_analog_y':
                # Map the value from 140-255 to 0 - 300
                value = (abs(event.value - 140) / 115) * 300
                 
                if (abs(value - old_value) > 10):
                    usb_comm.sendMessage(f"SPEED {value}", ESPHoldSpeed)
                    old_value = value
                
except KeyboardInterrupt:
    pwm.stop()
    GPIO.cleanup()
    print("\nStopped reading events.")