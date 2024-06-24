from psController import PSController
import time
import serial
import RPi.GPIO as GPIO

# Connect to the available USB via serial
ser = serial.Serial('/dev/ttyUSB0', 921600)
ser.write('START\n'.encode())

# Set up GPIO
GPIO.setmode(GPIO.BCM)
servo_pin = 17
GPIO.setup(servo_pin, GPIO.OUT)
servo_pwm = GPIO.PWM(servo_pin, 50)  # 50 Hz frequency
servo_pwm.start(6.7)  # 7.5% duty cycle

try:
    # Create PSController instance
    controller = PSController(servo_middle_angle=6.7, servo_min_angle=5.5, servo_max_angle=8.4)

    controller.calibrate_analog_sticks()

    while True:
        x, y, rx, ry = controller.get_analog_stick_values()
        # print(f"x: {x:.2f}, y: {y:.2f}, rx: {rx:.2f}, ry: {ry:.2f}")

        servo_value = controller.map_servo_angle(x)
        # Write servo value
        servo_pwm.ChangeDutyCycle(servo_value)
        
        speed_value = controller.map_speed_value(ry)
        ser.write(f'SPEED {speed_value}\n'.encode())
        print(f"Speed value: {speed_value:.2f}")

        time.sleep(0.1)

finally:
    ser.write('STOP\n'.encode())
    ser.close()
    servo_pwm.stop()
    GPIO.cleanup()