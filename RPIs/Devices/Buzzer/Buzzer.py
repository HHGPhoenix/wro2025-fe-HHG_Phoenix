import threading
import time
from rpi_hardware_pwm import HardwarePWM # type: ignore

class Buzzer:
    def __init__(self, channel=2) -> None:
        self.pwm = HardwarePWM(pwm_channel=channel, hz=1, chip=2)
        # self.pwm.start(0)  # 7.5% duty cycle corresponds to 1.5ms pulse width (90 degrees)
        self.buzz_thread = None
    
    def buzz(self, duration, frequency) -> None:
        self.buzz_thread = threading.Thread(target=self._buzz_thread, args=(duration, frequency)).start()
    
    def _buzz_thread(self, duration, frequency):
        print("Buzzing at frequency: " + str(frequency) + " for duration: " + str(duration))
        self.pwm.change_frequency(frequency)
        self.pwm.start(50)
        print("Buzzing...")
        time.sleep(duration)
        self.pwm.stop()
        
    ##################################################
    
    def buzz_success(self) -> None:
        threading.Thread(target=self._buzz_success_thread).start()
        
    def _buzz_success_thread(self):
        self._buzz_thread(0.15, 1600)
        time.sleep(0.05)
        # time.sleep(1)
        self._buzz_thread(0.15, 1600)
        
    def buzz_failure(self) -> None:
        threading.Thread(target=self._buzz_failure_thread).start()
        
    def _buzz_failure_thread(self):
        self._buzz_thread(1.01, 800)
        
    def buzz_battery_low(self) -> None:
        threading.Thread(target=self._buzz_battery_low_thread).start()
        
    def _buzz_battery_low_thread(self):
        self._buzz_thread(0.6, 450)
        time.sleep(0.15)
        self._buzz_thread(0.6, 450)
        
    def stop(self):
        self.pwm.stop()