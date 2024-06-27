#include <Arduino.h>

#define ENA 5
#define IN1 4
#define IN2 0
#define encoderA 2
#define encoderB 15

volatile long encoderTicks = 0;
int lastEncoderA = LOW;
int lastEncoderB = LOW;
int desiredSpeed = 0; // Desired speed in ticks per second
int motorSpeed = 0;	  // Actual motor speed in PWM value
unsigned long lastTime = 0;

// PD controller gains
float Kp = 2.0; // Proportional gain
float Kd = 1.0; // Derivative gain

void IRAM_ATTR encoderISR()
{
	int newEncoderA = digitalRead(encoderA);
	int newEncoderB = digitalRead(encoderB);

	if (newEncoderA == HIGH && lastEncoderA == LOW)
	{
		if (newEncoderB == LOW)
		{
			encoderTicks++;
		}
		else
		{
			encoderTicks--;
		}
	}

	lastEncoderA = newEncoderA;
	lastEncoderB = newEncoderB;
}

void setup()
{
	Serial.begin(115200);

	pinMode(ENA, OUTPUT);
	pinMode(IN1, OUTPUT);
	pinMode(IN2, OUTPUT);
	pinMode(encoderA, INPUT);
	pinMode(encoderB, INPUT);

	attachInterrupt(digitalPinToInterrupt(encoderA), encoderISR, CHANGE);
	attachInterrupt(digitalPinToInterrupt(encoderB), encoderISR, CHANGE);

	analogWriteFreq(1000); // Set PWM frequency to 1kHz
}

void loop()
{
	if (Serial.available() > 0)
	{
		String command = Serial.readStringUntil('\n');
		if (command.startsWith("SPEED"))
		{
			desiredSpeed = command.substring(6).toInt();
		}
	}

	unsigned long currentTime = millis();
	if (currentTime - lastTime >= 100)
	{ // Adjust speed every 100 ms
		int currentSpeed = computeSpeed();
		controlMotor(currentSpeed);
		lastTime = currentTime;
	}
}

int computeSpeed()
{
	static long lastEncoderTicks = 0;
	long ticks = encoderTicks;
	long deltaTicks = ticks - lastEncoderTicks;
	lastEncoderTicks = ticks;

	int speed = (deltaTicks * 1000) / (millis() - lastTime); // Speed in ticks per second
	return speed;
}

void controlMotor(int currentSpeed)
{
	static int lastError = 0;
	int error = desiredSpeed - currentSpeed;
	int derivative = error - lastError;
	lastError = error;

	// PD control
	int controlSignal = Kp * error + Kd * derivative;

	motorSpeed = controlSignal;

	if (motorSpeed > 255)
		motorSpeed = 255;
	if (motorSpeed < -255)
		motorSpeed = -255;

	if (desiredSpeed == 0)
	{
		// Active braking
		if (currentSpeed > 0)
		{
			analogWrite(ENA, 255);
			digitalWrite(IN1, LOW);
			digitalWrite(IN2, HIGH);
		}
		else if (currentSpeed < 0)
		{
			analogWrite(ENA, 255);
			digitalWrite(IN1, HIGH);
			digitalWrite(IN2, LOW);
		}
		else
		{
			digitalWrite(IN1, LOW);
			digitalWrite(IN2, LOW);
			analogWrite(ENA, 0);
		}
	}
	else if (motorSpeed >= 0)
	{
		analogWrite(ENA, motorSpeed);
		digitalWrite(IN1, HIGH);
		digitalWrite(IN2, LOW);
	}
	else
	{
		analogWrite(ENA, -motorSpeed);
		digitalWrite(IN1, LOW);
		digitalWrite(IN2, HIGH);
	}
}
