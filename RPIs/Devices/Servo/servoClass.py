import RPi.GPIO as GPIO

class Servo:
    def __init__(self, pin, minPulse=500, maxPulse=2500, minAngle=0, middleAngle=90, maxAngle=180):
        self.pin = pin
        
        self.minPulse = minPulse
        self.maxPulse = maxPulse
        
        self.minAngle = minAngle
        self.middleAngle = middleAngle
        self.maxAngle = maxAngle
        
        self.pwm = GPIO.PWM(pin, 50)
        self.pwm.start(0)
        
        self.angle = 0

    def setAngle(self, angle):
        if angle < 0:
            angle = 0
        elif angle > 180:
            angle = 180
            
        self.angle = angle
        pulseWidth = self.minPulse + (self.maxPulse - self.minPulse) * angle / 180
        self.pwm.ChangeDutyCycle(pulseWidth / 10)
        
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