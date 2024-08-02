try:
    import pyvisa
except ImportError:
    from pip._internal import main as pipmain
    pipmain(['install', 'pyvisa'])
import time

class SPD():
    def __init__(self):
        self.spd = None
    def setup(self):
        """
        Setup the SPD 3303 power supply using pyvisa
        """
        rm = pyvisa.ResourceManager()
        resourceList = rm.list_resources("?*SPD?*")
        self.spd = rm.open_resource(resourceList[0])
        print("Successfully Connected to SPD")
    def confirm(self):
        return self.spd.query("*IDN?")
    
    class Channel():
        def __init__(self, chan_no: int, dev):
            self._name = f"CH{chan_no}"
            self._dev = dev
        def set_output(self, status: bool):
            self._dev.write(f"OUTP {self._name},{'ON' if status else 'OFF'}")
    
        def set_voltage(self, voltage: float):
            self._dev.write(f"{self._name}:VOLT {voltage:.3f}")

        def set_current(self, current: float):
            self._dev.write(f"{self._name}:CURR {current:.3f}")

        def get_voltage(self):
            return self._dev.query(f"{self._name}:VOLT?")

        def get_current(self):
            return self._dev.query(f"{self._name}:CURR?")

        def measure_voltage(self):
            return self._dev.query(f"MEAS:VOLT? {self._name}")

        def measure_current(self):
            return self._dev.query(f"MEAS:CURR? {self._name}")

        def measure_power(self):
            return self._dev.query(f"MEAS:POWE? {self._name}")
