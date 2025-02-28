#include <Arduino.h>
#include <limits.h>
#include <Wire.h>
#include <MPU6050_6Axis_MotionApps20.h>

#define ENA 5
#define IN1 18
#define IN2 19
#define encoderA 15
#define encoderB 2
#define GyroCorrection -1.515

volatile long encoderTicks = 0;
volatile int lastEncoderA = LOW;
volatile int lastEncoderB = LOW;

int desiredSpeed = 0; // ticks per second (desired)
int motorSpeed = 0;	  // PWM output value
int lastSpeed = 0;

unsigned long lastTime = 0;
unsigned long lastTime_voltage = 0;
unsigned long lastTime_angle = 0;

// Variables for sensor fusion
float fusedRoll = 0.0;
float fusedPitch = 0.0;
float fusedYaw = 0.0; // Integrated gyro yaw

// PD controller gains
float Kp = 0.3;
float Kd = 0.5;
float Ka = 1;

MPU6050 mpu;

//
// Encoder ISR (placed in IRAM for faster execution)
//
void IRAM_ATTR encoderISR()
{
	static const int HIGH_STATE = 1;
	static const int LOW_STATE = 0;

	int newA = digitalRead(encoderA);
	int newB = digitalRead(encoderB);

	if (newA != lastEncoderA)
	{
		encoderTicks += (newA == HIGH_STATE) ? ((newB == LOW_STATE) ? 1 : -1) : ((newB == HIGH_STATE) ? 1 : -1);
	}
	lastEncoderA = newA;
	lastEncoderB = newB;
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

	analogWriteFrequency(1000);

	Wire.begin();
	mpu.initialize();
	if (!mpu.testConnection())
	{
		Serial.println(F("MPU6050 connection failed"));
		while (1)
			;
	}
}

//
// Reverted computeSpeed() using the original logic
//
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

	// Serial.print("Ticks: ");
	// Serial.print(ticks);
	// Serial.print("  DeltaTicks: ");
	// Serial.print(deltaTicks);
	// Serial.print("  DeltaTime: ");
	// Serial.print(deltaTime);
	// Serial.print("  Speed: ");
	// Serial.println(speed);

	if (speed < INT_MIN || speed > INT_MAX)
	{
		return (speed < INT_MIN) ? INT_MIN : INT_MAX;
	}

	return static_cast<int>(speed / 10);
}

//
// Motor control using a PD controller with an acceleration term
//
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

	int controlSignal = Kp * error + Kd * derivative + lastSpeed * Ka;
	controlSignal = constrain(controlSignal, -255, 255);
	motorSpeed = controlSignal;
	lastSpeed = motorSpeed;

	// Serial.print(F("Out: "));
	// Serial.println(motorSpeed);

	if (motorSpeed >= 0)
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

void loop()
{
	unsigned long currentTime = millis();

	// Process incoming serial commands (non-blocking)
	if (Serial.available())
	{
		String command = Serial.readStringUntil('\n');
		if (command.startsWith("SPEED "))
		{
			desiredSpeed = command.substring(6).toInt();
			Serial.print(F("Desired Speed: "));
			Serial.println(desiredSpeed);
		}
		else if (command.startsWith("RST"))
		{
			fusedPitch = fusedRoll = fusedYaw = 0;
		}
		else if (command.startsWith("KP "))
		{
			Kp = command.substring(3).toFloat();
		}
		else if (command.startsWith("KD "))
		{
			Kd = command.substring(3).toFloat();
		}
		else if (command.startsWith("KA "))
		{
			Ka = command.substring(3).toFloat();
		}
	}

	// Motor control update every 100 ms
	if (currentTime - lastTime >= 50)
	{
		int currentSpeed = computeSpeed();
		// Serial.print(F("CS: "));
		// Serial.println(currentSpeed);
		controlMotor(currentSpeed);
		lastTime = currentTime;
	}

	// Voltage reading update every 1000 ms
	if (currentTime - lastTime_voltage >= 1000)
	{
		Serial.print(F("V: "));
		Serial.println(analogRead(A0));
		lastTime_voltage = currentTime;
	}

	// Sensor fusion update every 10 ms
	if (currentTime - lastTime_angle >= 10)
	{
		float dt = (currentTime - lastTime_angle) * 0.001f;

		int16_t ax, ay, az, gx, gy, gz;
		mpu.getMotion6(&ax, &ay, &az, &gx, &gy, &gz);

		const float accelScale = 1.0f / 16384.0f;
		const float gyroScale = 1.0f / 131.0f;
		const float radToDeg = 57.29578f; // 180/PI

		float ax_f = ax * accelScale;
		float ay_f = ay * accelScale;
		float az_f = az * accelScale;
		float gyroX = gx * gyroScale;
		float gyroY = gy * gyroScale;
		float gyroZ = gz * gyroScale + GyroCorrection;

		float rollAcc = atan2(ay_f, az_f) * radToDeg;
		float pitchAcc = atan2(-ax_f, sqrt(ay_f * ay_f + az_f * az_f)) * radToDeg;

		const float alpha = 0.98f;
		fusedRoll = alpha * (fusedRoll + gyroX * dt) + (1.0f - alpha) * rollAcc;
		fusedPitch = alpha * (fusedPitch + gyroY * dt) + (1.0f - alpha) * pitchAcc;
		fusedYaw += gyroZ * dt;

		Serial.print(F("IMU: R"));
		Serial.print(fusedRoll);
		Serial.print(F(" P"));
		Serial.print(fusedPitch);
		Serial.print(F(" Y"));
		Serial.println(fusedYaw);

		lastTime_angle = currentTime;
	}
}
