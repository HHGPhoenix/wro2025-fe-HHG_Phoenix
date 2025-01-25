#include <Arduino.h>
#include <limits.h> // For INT_MIN and INT_MAX

#define ENA 14
#define IN1 12
#define IN2 13
#define encoderA 5
#define encoderB 4

volatile long encoderTicks = 0;
int desiredSpeed = 0; // Desired speed in ticks per second
int motorSpeed = 0;	  // Actual motor speed in PWM value
int lastSpeed = 0;	  // Last measured speed
int lastError = 0;
unsigned long lastTime = 0;
unsigned long lastTime_voltage = 0;

// Adjust PD controller gains
float Kp = 0.9;	  // Reduced Proportional gain
float Kd = 0.025; // Reduced Derivative gain
float Ka = 1;	  // Acceleration gain
float Ki = 0.5;

void controlMotor(int currentSpeed);
int computeSpeed();

volatile int lastEncoderA = LOW;
volatile int lastEncoderB = LOW;

void IRAM_ATTR encoderISR()
{
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
			Serial.print("Desired Speed: ");
			Serial.println(desiredSpeed);
		}
	}

	unsigned long currentTime = millis();
	if (currentTime - lastTime >= 100)
	{
		int currentSpeed = computeSpeed();
		Serial.print("CS: ");
		Serial.println(currentSpeed);
		controlMotor(currentSpeed);
		lastTime = currentTime;
	}

	if (currentTime - lastTime_voltage >= 1000)
	{
		Serial.print("V: ");
		Serial.println(analogRead(A0));
		lastTime_voltage = currentTime;
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

	long long speed = (static_cast<long long>(deltaTicks) * 1000L) / deltaTime; // Use long long for calculation

	// Debugging information
	Serial.print("Ticks: ");
	Serial.print(ticks);
	Serial.print(" DeltaTicks: ");
	Serial.print(deltaTicks);
	Serial.print(" DeltaTime: ");
	Serial.print(deltaTime);
	Serial.print(" Speed: ");
	Serial.println(speed);

	// Check if speed is within the int range
	if (speed < INT_MIN || speed > INT_MAX)
	{
		// Handle overflow, e.g., by clamping to INT_MAX or INT_MIN
		return (speed < INT_MIN) ? INT_MIN : INT_MAX;
	}

	return static_cast<int>(speed / 10); // Cast back to int
}

void controlMotor(int currentSpeed)
{
	if (currentSpeed == 0 && desiredSpeed == 0)
	{
		analogWrite(ENA, 0);
		digitalWrite(IN1, LOW);
		digitalWrite(IN2, LOW);
		return;
	}

	static int lastError = 0;
	static double integral = 0.0;
	static unsigned long lastTime = 0;

	unsigned long now = millis();
	double dt = (now - lastTime) / 1000.0; // Convert ms to seconds
	lastTime = now;

	int error = desiredSpeed - currentSpeed;

	// Integrate over time
	integral += error * dt;
	// Prevent integral runaway if needed
	integral = constrain(integral, -255 / Ki, 255 / Ki);

	// Derivative
	double derivative = 0;
	if (dt > 0)
	{
		derivative = (error - lastError) / dt;
	}

	// Real PID control
	double controlSignal = Kp * error + Ki * integral + Kd * derivative;

	// Saturate control signal to -255 to 255
	controlSignal = constrain(controlSignal, -255, 255);

	motorSpeed = (int)controlSignal;

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

	lastError = error;
	lastSpeed = motorSpeed;

	Serial.print("Out: ");
	Serial.println(motorSpeed);
}
