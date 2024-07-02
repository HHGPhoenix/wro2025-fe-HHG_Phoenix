import threading
import time
import queue
from oarsch import Counter

class CounterThread:
    def __init__(self):
        self.queue = queue.Queue()
        self.counting_thread = None

        self.counter = Counter(self.queue)

        self.run()

    def run(self):
        self.counting_thread = threading.Thread(target=self.counter.count_up, daemon=True)
        self.counting_thread.start()
        
        self.run2()

    def run2(self):
        try:
            while True:
                if not self.queue.empty():
                    current_value = self.queue.get()
                    print(f"Current counter value: {current_value}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopped by user")

# Usage
counter_thread = CounterThread()