import threading
import time

class WatchDoginator(threading.Thread):
    def __init__(self, threshold_upper, threshold_lower, sleep, value_adjust,  name=None):
        super().__init__()
        self.name = name
        self.threshold_upper = threshold_upper
        self.threshold_lower = threshold_lower
        self.sleep = sleep
        self.value_adjust = value_adjust
        self.current_value = None
        self.previous_value = None
        self.shutdown_requested = False

    def update_value(self, value):
        self.previous_value = self.current_value
        self.current_value = value

    def check_value(self, value):
        value = value / self.value_adjust
        if value < self.threshold_lower or value > self.threshold_upper:
            print("Threshold exceeded")
            print(f"{self.name} Battery voltage Checked ERROR: {value} \n")
            return False
        else:
            print(f"{self.name} Battery voltage Checked:  {value} \n")
            return True

    def run(self):
        while not self.shutdown_requested:
            print(f"Checking value: {self.current_value}")
            if self.current_value is not None:
                if not self.check_value(self.current_value) and not self.check_value(self.previous_value):
                    print("#############################################\n")
                    print(f"Threshold exceeded at {self.current_value / self.value_adjust}  for {self.name}")
                    print("#############################################\n")
                    self.shutdown_requested = True
                    raise Exception("Threshold exceeded")
            time.sleep(self.sleep)
