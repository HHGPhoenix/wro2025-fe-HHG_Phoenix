from rpi_hardware_pwm import HardwarePWM #type: ignore

class Servo:
    def __init__(self, pin, minPulse=500, maxPulse=2500, minAngle=0, middleAngle=90, maxAngle=180):
        self.pin = pin
        
        self.minPulse = minPulse
        self.maxPulse = maxPulse
        
        self.minAngle = minAngle
        self.middleAngle = middleAngle
        self.maxAngle = maxAngle
        
        self.normalMinAngle = 0
        self.normalMiddleAngle = 90
        self.normalMaxAngle = 180
        
        # Initialize PWM with the specified pin
        self.pwm = HardwarePWM(pwm_channel=0, hz=50, chip=0)
        self.pwm.start(17)  # 7.5% duty cycle corresponds to 1.5ms pulse width (90 degrees)
        
        self.angle = None  # Initialize to None

    def setAngle(self, angle):
        # print(f"angle: {angle:.2f}", end=' ')
        if angle < self.minAngle:
            angle = self.minAngle
        elif angle > self.maxAngle:
            angle = self.maxAngle
            
        self.angle = angle
        
        # Calculate the pulse width in microseconds based on the angle
        pulseWidthMicroseconds = self.minPulse + ((self.maxPulse - self.minPulse) * (angle - self.normalMinAngle) / (self.normalMaxAngle - self.normalMinAngle))
        
        # Correctly calculate the duty cycle based on the pulse width
        dutyCycle = (pulseWidthMicroseconds / 10000) * 100
        
        self.pwm.change_duty_cycle(duty_cycle=dutyCycle)
        

        
    def mapToServoAngle(self, value):
        if value <= 0.5:
            # map the servo from 0-0.5 to minAngle-middleAngle
            return (value * 2) * (self.middleAngle - self.minAngle) + self.minAngle
        else:
            # map the servo from 0.5-1 to middleAngle-maxAngle
            return ((value - 0.5) * 2) * (self.maxAngle - self.middleAngle) + self.middleAngle

    def getAngle(self):
        return self.angle

    def stop(self):
        self.pwm.stop()
