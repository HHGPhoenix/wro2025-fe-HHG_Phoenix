#include <Arduino.h>

#define ENA 14
#define IN1 12
#define IN2 13
#define encoderA 5
#define encoderB 4

volatile long encoderTicks = 0;
int desiredSpeed = 0; // Desired speed in ticks per second
int motorSpeed = 0;	  // Actual motor speed in PWM value
int lastSpeed = 0;	  // Last measured speed
unsigned long lastTime = 0;

// Adjust PD controller gains
float Kp = 2;	// Reduced Proportional gain
float Kd = 0.5; // Reduced Derivative gain
float Ka = 0;	// Acceleration gain

void controlMotor(int currentSpeed);
int computeSpeed();

volatile int lastEncoderA = LOW;
volatile int lastEncoderB = LOW;

void IRAM_ATTR encoderISR()
{
	static unsigned long lastInterruptTime = 0;
	unsigned long interruptTime = millis();

	// Debounce encoder signal
	if (interruptTime - lastInterruptTime > 5)
	{ // 5 ms debounce period
		int newEncoderA = digitalRead(encoderA);
		int newEncoderB = digitalRead(encoderB);

		if (newEncoderA != lastEncoderA)
		{
			if (newEncoderA == HIGH)
			{
				encoderTicks += (newEncoderB == LOW) ? 1 : -1;
			}
			else
			{
				encoderTicks += (newEncoderB == HIGH) ? 1 : -1;
			}
		}

		lastEncoderA = newEncoderA;
		lastEncoderB = newEncoderB;
		lastInterruptTime = interruptTime;
	}
}

void setup()
{
	Serial.begin(921600);

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
		if (command.startsWith("SPEED "))
		{
			desiredSpeed = command.substring(6).toInt();
			// Serial.print("Desired Speed: ");
			// Serial.println(desiredSpeed);
		}
	}

	unsigned long currentTime = millis();
	if (currentTime - lastTime >= 100)
	{ // Adjust speed every 100 ms
		int currentSpeed = computeSpeed();
		Serial.print("DS: ");
		Serial.println(desiredSpeed);
		Serial.print("CS: ");
		Serial.println(currentSpeed);
		controlMotor(currentSpeed);
		lastTime = currentTime;
	}
}

int computeSpeed()
{
	static long lastEncoderTicks = 0;
	static unsigned long lastComputeTime = 0;

	unsigned long currentTime = millis();
	long ticks;

	// Read encoderTicks atomically
	noInterrupts();
	ticks = encoderTicks;
	interrupts();

	long deltaTicks = ticks - lastEncoderTicks;
	unsigned long deltaTime = currentTime - lastComputeTime;

	// Update for the next iteration
	lastEncoderTicks = ticks;
	lastComputeTime = currentTime;

	if (deltaTime == 0)
	{
		return 0; // Prevent division by zero
	}

	// Detecting overflow or invalid deltaTicks values
	if (abs(deltaTicks) > 1000 || deltaTicks == 0)
	{
		return 0;
	}

	int speed = ((deltaTicks * 1000) / (int)deltaTime); // Speed in ticks per second

	// Debugging information
	// Serial.print("Ticks: ");
	// Serial.print(ticks);
	// Serial.print(" DeltaTicks: ");
	// Serial.print(deltaTicks);
	// Serial.print(" DeltaTime: ");
	// Serial.print(deltaTime);
	// Serial.print(" Speed: ");
	// Serial.println(speed);

	return speed;
}

void controlMotor(int currentSpeed)
{
	static int lastError = 0;
	static int lastSpeed = 0; // Ensure lastSpeed is initialized if not already
	int error = desiredSpeed - currentSpeed;
	int derivative = error - lastError;
	lastError = error;

	// PD control with acceleration component
	int controlSignal = Kp * error + Kd * derivative + lastSpeed * Ka;

	// Saturate control signal to -255 to 255
	controlSignal = constrain(controlSignal, -255, 255);

	motorSpeed = controlSignal;

	// Control motor based on motorSpeed
	if (motorSpeed >= 0)
	{
		analogWrite(ENA, motorSpeed);
		digitalWrite(IN1, HIGH);
		digitalWrite(IN2, LOW);
	}
	else
	{
		analogWrite(ENA, -motorSpeed); // Use absolute value for PWM
		digitalWrite(IN1, LOW);
		digitalWrite(IN2, HIGH);
	}

	lastSpeed = currentSpeed; // Update lastSpeed for the next iteration
}
