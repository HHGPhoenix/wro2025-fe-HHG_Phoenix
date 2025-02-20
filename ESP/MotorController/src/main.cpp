#include <Arduino.h>
#include <limits.h> // For INT_MIN and INT_MAX
#include <Wire.h>
#include <MPU6050_6Axis_MotionApps20.h> // Using this library for raw sensor data

#define ENA 14
#define IN1 12
#define IN2 13
#define encoderA 15
#define encoderB 2

#define MIN_X 86
#define MAX_X 1273
#define MIN_Y -1753
#define MAX_Y -152
#define MIN_Z -10302
#define MAX_Z -10123

volatile long encoderTicks = 0;
int desiredSpeed = 0; // Desired speed in ticks per second
int motorSpeed = 0;	  // Actual motor speed in PWM value
int lastSpeed = 0;	  // Last measured speed
unsigned long lastTime = 0;
unsigned long lastTime_voltage = 0;
unsigned long lastTime_angle = 0;

// Variables for manual sensor fusion
float fusedRoll = 0.0;
float fusedPitch = 0.0;
float fusedYaw = 0.0; // Yaw is integrated from the gyroscope

// PD controller gains
float Kp = 0.3;
float Kd = 0.25;
float Ka = 1;

MPU6050 mpu; // MPU6050 instance

// --- Encoder ISR Variables ---
volatile int lastEncoderA = LOW;
volatile int lastEncoderB = LOW;

void controlMotor(int currentSpeed);
int computeSpeed();

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

	Wire.begin();

	mpu.initialize();
	if (!mpu.testConnection())
	{
		Serial.println("MPU6050 connection failed");
		while (1)
			;
	}
}

void loop()
{
	unsigned long currentTime = millis();

	// --- Motor Control (update every 100 ms) ---
	if (currentTime - lastTime >= 100)
	{
		int currentSpeed = computeSpeed();
		Serial.print("CS: ");
		Serial.println(currentSpeed);
		controlMotor(currentSpeed);
		lastTime = currentTime;
	}

	// --- Voltage Reading (update every 1000 ms) ---
	if (currentTime - lastTime_voltage >= 1000)
	{
		Serial.print("V: ");
		Serial.println(analogRead(A0));
		lastTime_voltage = currentTime;
	}

	// --- Sensor Fusion & Yaw (Angle) Printing (update every 100 ms) ---
	if (currentTime - lastTime_angle >= 100)
	{
		float dt = (currentTime - lastTime_angle) / 1000.0;

		// Read MPU6050 raw data
		int16_t ax, ay, az, gx, gy, gz;
		mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

		// Convert raw data
		float ax_f = ax / 16384.0;
		float ay_f = ay / 16384.0;
		float az_f = az / 16384.0;

		float gyroX = gx / 131.0;
		float gyroY = gy / 131.0;
		float gyroZ = gz / 131.0 - 1.45;

		float rollAcc = atan2(ay_f, az_f) * 180 / PI;
		float pitchAcc = atan2(-ax_f, sqrt(ay_f * ay_f + az_f * az_f)) * 180 / PI;

		// Complementary filter for roll and pitch
		float alpha = 0.98;
		fusedRoll = alpha * (fusedRoll + gyroX * dt) + (1 - alpha) * rollAcc;
		fusedPitch = alpha * (fusedPitch + gyroY * dt) + (1 - alpha) * pitchAcc;

		fusedYaw += gyroZ * dt;

		// Print values
		Serial.print("Raw Gyro yaw: ");
		Serial.print(gyroZ);
		Serial.print("Angle: ");
		Serial.println(fusedYaw);

		lastTime_angle = currentTime;
	}
}

int computeSpeed()
{
	static long lastEncoderTicks = 0;
	static unsigned long lastComputeTime = 0;

	unsigned long currentTime = millis();
	long ticks;

	noInterrupts();
	ticks = encoderTicks;
	interrupts();

	long deltaTicks = ticks - lastEncoderTicks;
	unsigned long deltaTime = currentTime - lastComputeTime;

	// Update for next iteration
	lastEncoderTicks = ticks;
	lastComputeTime = currentTime;

	if (deltaTime == 0)
	{
		return 0; // Prevent division by zero
	}

	if (abs(deltaTicks) > 1000 || deltaTicks == 0)
	{
		return 0;
	}

	long long speed = (static_cast<long long>(deltaTicks) * 1000L) / deltaTime;

	Serial.print("Ticks: ");
	Serial.print(ticks);
	Serial.print("  DeltaTicks: ");
	Serial.print(deltaTicks);
	Serial.print("  DeltaTime: ");
	Serial.print(deltaTime);
	Serial.print("  Speed: ");
	Serial.println(speed);

	if (speed < INT_MIN || speed > INT_MAX)
	{
		return (speed < INT_MIN) ? INT_MIN : INT_MAX;
	}

	return static_cast<int>(speed / 10);
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
	int error = desiredSpeed - currentSpeed;
	int derivative = error - lastError;
	lastError = error;

	// PD control with an acceleration term
	int controlSignal = Kp * error + Kd * derivative + lastSpeed * Ka;
	controlSignal = constrain(controlSignal, -255, 255);
	motorSpeed = controlSignal;

	// Drive motor based on control signal
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

	lastSpeed = motorSpeed;
	Serial.print("Out: ");
	Serial.println(motorSpeed);
}
