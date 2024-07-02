import json
import gpiod
import time

class Seven_Segment:
    def __init__(self, digit_pins, segment_pins, dot_pin, Mapping_path="RPIs/Devices/4digit_7segment/NumberMapping.json"):
        """
        Initialize the 4-digit 7-segment display using gpiod for Raspberry Pi 5. When finished using call cleanup to release the GPIO pins.

        Args:
            digit_pins (list): The GPIO pins connected to the digits of the display.
            segment_pins (list): The GPIO pins connected to the segments of the display.
            dot_pin (int): The GPIO pin connected to the dot of the display.
            Mapping_path (str, optional): The path to the number mapping file. Defaults to "NumberMapping.json".
        """
        self.chip = gpiod.Chip('gpiochip4')  # Assuming the GPIO chip is 'chip4'
        self.digit_lines = [self.chip.get_line(pin) for pin in digit_pins]
        self.segment_lines = [self.chip.get_line(pin) for pin in segment_pins]

        print(f"Digit lines: {digit_pins}, Segment lines: {segment_pins}, Dot line: {dot_pin}")

        print(f"Digit lines: {self.digit_lines}, Segment lines: {self.segment_lines}")

        self.dot_line = self.chip.get_line(dot_pin)
        
        with open(Mapping_path) as f:
            self.number_mapping = json.load(f)
            
        for line in self.digit_lines + self.segment_lines + [self.dot_line]:
            line.request(consumer='7seg', type=gpiod.LINE_REQ_DIR_OUT)
            
        for digit_line in self.digit_lines:
            digit_line.set_value(1)

    def write_digit(self, digit, number, activate_dot=False):
        """
        Write a number to a digit on the 4-digit 7-segment display using gpiod.

        Args:
            digit (int): The digit to write the number to.
            number (int): The number to be displayed.
            activate_dot (bool, optional): Whether to activate the dot. Defaults to False.
        """
        if digit < 0 or digit > 3:
            raise ValueError("Digit must be between 0 and 3")
        if number < 0 or number > 9:
            raise ValueError("Number must be between 0 and 9")
        
        if digit == 0:
            self.digit_lines[3].set_value(1)
            self.digit_lines[2].set_value(1)
            self.digit_lines[1].set_value(1)
            self.digit_lines[0].set_value(0)
        elif digit == 1:
            self.digit_lines[3].set_value(1)
            self.digit_lines[2].set_value(1)
            self.digit_lines[1].set_value(0)
            self.digit_lines[0].set_value(1)
        elif digit == 2:
            self.digit_lines[3].set_value(1)
            self.digit_lines[2].set_value(0)
            self.digit_lines[1].set_value(1)
            self.digit_lines[0].set_value(1)
        elif digit == 3:
            self.digit_lines[3].set_value(0)
            self.digit_lines[2].set_value(1)
            self.digit_lines[1].set_value(1)
            self.digit_lines[0].set_value(1)
        
        number = str(number)
        segments = self.number_mapping[number]
        for i, segment_line in enumerate(self.segment_lines):
            segment_line.set_value(segments[i])
            
        if activate_dot:
            self.dot_line.set_value(1)

    def write_voltage(self, voltage):
        """
        Write the voltage to the 4-digit 7-segment display using gpiod.

        Args:
            voltage (float): The voltage to be displayed.
        """
        voltage_str = str(voltage)
        voltage_str = voltage_str[:4]
        
        for i, digit in enumerate(voltage_str):
            if digit == '.':
                continue  # Skip dot since it's handled in write_digit
            elif i > 0 and voltage_str[i-1] == '.':
                self.write_digit(i-1, int(digit), activate_dot=True)
            else:
                self.write_digit(i, int(digit))
                
            time.sleep(0.001)
                
    def clear(self):
        """
        Clear the 4-digit 7-segment display.
        """
        for line in self.digit_lines + self.segment_lines + [self.dot_line]:
            line.set_value(0)
            
    def cleanup(self):
        """
        Close the 4-digit 7-segment display.
        """
        for line in self.digit_lines + self.segment_lines + [self.dot_line]:
            line.release()
        self.chip.close()

if __name__ == "__main__":
    display = Seven_Segment([4, 17, 27, 22], [23, 24, 25, 5, 6, 13, 16], 26)
    
    try:
        while True:
            display.write_voltage(12.10)

        
    finally:
        display.cleanup()
    