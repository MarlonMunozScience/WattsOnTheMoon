import serial
import time
class power:
    def __init__(self, port):
        self.port = port
        self.ser = serial.Serial(port)
        self.time_sleep = 0.5

    # Confirms there's a connection by querying about machine ID
    def confirm(self):
        self.ser.write('*IDN?\n'.encode())
        time.sleep(self.time_sleep)
        return self.ser.readline()

    # Sets output state to on
    def turn_on(self):
        self.ser.write('outp 1\n'.encode())
        time.sleep(self.time_sleep)

    # Sets output state to off
    def turn_off(self):
        self.ser.write('outp off\n'.encode())
        time.sleep(self.time_sleep)

    # Checks the current state of the power supply
    def check_state(self):
        self.ser.write('outp:state?\n'.encode())
        time.sleep(self.time_sleep)
        return self.ser.readline() # 0 if off, 1 if on
    
    # Sets voltage then reads it
    def set_voltage(self, voltage):
        
        self.ser.write(f'volt {voltage}\n'.encode())

        time.sleep(self.time_sleep)

    # Returns voltage
    def read_voltage(self): 
        self.ser.write('volt?\n'.encode())
        time.sleep(self.time_sleep)
        return self.ser.readline()

    # Measures voltage
    def meas_voltage(self):
        self.ser.write('meas:volt?\n'.encode())
        time.sleep(self.time_sleep)
        return self.ser.readline()

    # Sets current and then reads it
    def set_current(self, current):
        self.ser.write(f'curr {current}\n'.encode())

        time.sleep(self.time_sleep)

    # Returns current
    def read_current(self):
        self.ser.write('curr?\n'.encode())
        time.sleep(self.time_sleep)
        return self.ser.readline()

    def meas_current(self):
        self.ser.write('meas:curr?\n'.encode())
        time.sleep(self.time_sleep)
        return self.ser.readline()

    def meas_power(self):
        self.ser.write('meas:pow?\n'.encode())
        time.sleep(self.time_sleep)
        return self.ser.readline()

    def read_power(self):
        self.ser.write('pow?\n'.encode())
        time.sleep(self.time_sleep)
        return self.ser.readline()

if __name__ == '__main__':
    # Tests to make sure Power Supply is working as expected
    port = "COM3"

    #Create object of power class
    instr = power(port)

    print(f"State returned: {instr.check_state()}")

    # Confirming that power supply is connected by returning ID of instrument
    print(f'Connected at ID: {instr.confirm()}')


    # Turn on the power supply
    instr.turn_on()

    # Check that state is on
    print(f"State returned: {instr.check_state()}")

    # Setting Voltage and current to high
    instr.set_voltage(1)
    instr.set_current(1)
    
    # Measuring
    print(f'Voltage measured at {instr.meas_voltage()} Volts')
    print(f'Current measured at {instr.meas_current()} Amps')   
    print(f'Power measured at {instr.meas_power()} Watts')

    # Setting voltage and current  to low
    instr.set_voltage(0)
    instr.set_current(0)

    # Measuring
    print(f'Voltage measured at {instr.meas_voltage()} Volts')
    print(f'Current measured at {instr.meas_current()} Amps')
    print(f'Power measured at {instr.meas_power()} Watts')

    # Turn on the power supply
    instr.turn_off()

    # Check that state is off
    print(f"State returned: {instr.check_state()}")



