import serial

# Open the serial port for communication with the RPLidar
ser = serial.Serial('/dev/ttyUSB0', 115200)

# Start the RPLidar
ser.write(b'\xA5\x60')

# Read data from the RPLidar
try:
    while True:
        response = ser.read(9)
        # Process the response data here
        print(response)

except:
    # Stop the RPLidar
    ser.write(b'\xA5\x25')
    ser.close()