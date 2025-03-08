import gpiod
import time
from datetime import timedelta
from gpiod.line import Bias, Edge

class Button:
    def __init__(self, pin):
        self.pin = pin
        # Use LineSettings to configure the pin as an input with edge detection
        settings = gpiod.LineSettings(edge_detection=Edge.BOTH, bias=Bias.PULL_UP, debounce_period=timedelta(milliseconds=10))
        self.config = {pin: settings}
        
    
    def wait_for_press(self):
        with gpiod.request_lines(
            "/dev/gpiochip0",
            consumer="Button",
            config=self.config
        ) as request:
            while True:
                for event in request.read_edge_events():
                    print(event)
                    if event:
                        if event.event_type == event.Type.RISING_EDGE:
                            print("Button released")
                            return

                        elif event.event_type == event.Type.FALLING_EDGE:
                            print("Button pressed")
                            return


# Example usage:
if __name__ == "__main__":
    button = Button(pin=4)
    button.wait_for_press()