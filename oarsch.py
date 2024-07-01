import time
import queue

def count_up(counter_queue):
    counter = 0
    while True:
        counter += 1
        counter_queue.put(counter)
        time.sleep(1)  # Sleep for 1 second to slow down the counting for demonstration purposes
