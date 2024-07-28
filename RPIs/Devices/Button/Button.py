import gpiod # type: ignore

class Button:
    def __init__(self, pin):
        self.state = False
        self.pin = pin
        
        self.chip = gpiod.Chip('gpiochip4')
        
        self.line = self.chip.get_line(pin)
        self.line.request(consumer='Button', type=gpiod.LINE_REQ_EV_BOTH_EDGES)
        
    def wait_for_press(self):
        try:
            while True:
                event = self.line.event_wait(sec=float("inf"))
                print("Waiting for button press...")
                if event:
                    event_data = self.line.event_read()
                    if event_data.event_type == gpiod.LineEvent.RISING_EDGE:
                        print("Button pressed")
                    elif event_data.event_type == gpiod.LineEvent.FALLING_EDGE:
                        print("Button released")
                    
        except KeyboardInterrupt:
            pass
        
        finally:
            self.line.release()
            self.chip.close()

# Example usage
button = Button(pin=4)
button.wait_for_press()