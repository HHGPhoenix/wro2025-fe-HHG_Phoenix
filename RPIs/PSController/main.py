from psController import PSController
import time
import RPi.GPIO as GPIO

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
        print(f"x: {x:.2f}, y: {y:.2f}, rx: {rx:.2f}, ry: {ry:.2f}")

        servo_value = controller.map_servo_angle(x)
        # Write servo value
        servo_pwm.ChangeDutyCycle(servo_value)

        time.sleep(0.1)

finally:
    servo_pwm.stop()
    GPIO.cleanup()