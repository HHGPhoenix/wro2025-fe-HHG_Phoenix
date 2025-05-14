import gpiod
import time
from datetime import timedelta
from gpiod.line import Bias, Edge
import threading

class Button:
    def __init__(self, pin, datamanager):
        self.pin = pin
        # Use LineSettings to configure the pin as an input with edge detection
        settings = gpiod.LineSettings(edge_detection=Edge.BOTH, bias=Bias.PULL_UP, debounce_period=timedelta(milliseconds=10))
        self.config = {pin: settings}
        self.datamanager = datamanager
        
    
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
                        if event.event_type in (event.Type.RISING_EDGE, event.Type.FALLING_EDGE):
                            print("Button pressed")
                            return
                        
    def start_stop_thread(self):
        # Start a thread to monitor the button state
        if not self.datamanager.running:
            ValueError("DataManager is not running")
            return
        
        threading.Thread(target=self._stop_thread, daemon=True).start()

    def _stop_thread(self):
        # Monitor button using edge events and set datamanager.running to False when pressed
        with gpiod.request_lines(
            "/dev/gpiochip0",
            consumer="Button",
            config=self.config
        ) as request:
            while self.datamanager.running:
                for event in request.read_edge_events():
                    if event:
                        if event.event_type in (event.Type.RISING_EDGE, event.Type.FALLING_EDGE):
                            self.datamanager.running = False
                            print("Button pressed, stopping thread")
                            return


# Example usage:
if __name__ == "__main__":
    button = Button(pin=4)
    button.wait_for_press()