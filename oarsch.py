import time
import queue

class Counter:
    def __init__(self, counter_queue):
        self.queue = counter_queue
            
    def count_up(self):
        counter = 0
        while True:
            counter += 1
            self.queue.put(counter)
            time.sleep(1)  # Sleep for 1 second to slow down the counting for demonstration purposes
