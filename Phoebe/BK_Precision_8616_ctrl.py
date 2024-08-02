import serial
import usbtmc
import time

class load:
    def  __init__(self):
        self.ser = None

    # Sets up USBTMC Connection
    def setup(self):
        id_string = usbtmc.list_devices()
        print(id_string)
        


        # This code grabs the address from the id_string and puts in hex
        id_split = str(id_string).split()
        address = id_split[2].split(":")
        for i in range(len(address)):
            address[i] = "0x" + address[i]
        print(f"Found address: {int(address[0], 0)}, {int(address[1], 0)}")

        # Now we can plug the address into usbtmc package
        self.ser =  usbtmc.Instrument(int(address[0], 0) , int(address[1], 0)  )

        print("Successfully Connected")
        


    # Confirms there's a connection by querying about machine ID
    def confirm(self):
        #print(self.ser.ask('*IDN?'))

        return self.ser.ask('*IDN?')
    
    def turn_on(self):
        self.ser.write('INP 1')
        time.sleep(0.5)
        return self.ser.ask("INP?")

    def turn_off(self):
        self.ser.write('INP 0')
        time.sleep(0.5)
        return self.ser.ask("INP?")   

    def set_res(self, resistance):
        
        self.ser.write(f'RES {resistance}\n'.encode())

        self.ser.write('RES?\n'.encode())
        print(self.ser.readline())

    def read_res(self):
        self.ser.write('RES?\n'.encode())
        print(self.ser.readline())  

    # Sets the voltage (volts)
    def set_voltage(self, voltage):
        self.ser.write(f'VOLT {voltage}')

        return self.ser.ask('VOLT?')
    
    # Returns the current voltage
    def read_voltage(self):
        self.ser.write('VOLT?'.encode())
        return self.ser.ask('MEAS:VOLT?')

    # Measures the current voltage
    def measure_voltage(self):
        #print(self.ser.ask('MEAS:VOLT?'))
        return self.ser.ask('MEAS:VOLT?')

    # Sets the current (Amps)
    def set_current(self, current):
        self.ser.write(f'CURR {current}')

        return self.ser.ask('CURR?')

    def read_current(self):

        self.ser.write('CURR?\n'.encode())
        return self.ser.readline()
    
    # Measures the current current
    def measure_current(self):
        #print(self.ser.ask('MEAS:CURR?'))
        return self.ser.ask('MEAS:CURR?')
        
    
    # Sets the input regulation mode of the load to constant power mode
    def const_power_mode(self):
        self.ser.write('FUNC POW')
        
        print(self.ser.ask('FUNC?'))
        return (self.ser.ask('FUNC?')) 

    # Sets the input regulation mode of the load to constant power mode
    def const_current_mode(self):
        self.ser.write('FUNC CURR')
        
        print(self.ser.ask('FUNC?'))
        return (self.ser.ask('FUNC?')) 


    # Sets the input regulation mode of the load to constant voltage mode 
    def const_voltage_mode(self):
        self.ser.write('FUNC VOLT')

        print(self.ser.ask('FUNC?'))
        return (self.ser.ask('FUNC?'))


    # Sets power (Watts)
    def set_power(self, power):
        self.ser.write(f'POW {power}')

        return self.ser.ask('POW?')

    def read_power(self):
        
        return self.ser.ask('POW?')

    def read_errors(self):
        return self.ser.ask('SYST:ERR?')
    
    


if __name__ == '__main__':
    instr = load()
    print("Starting Setup")
    instr.setup()

    print("Confirming Set up")

    print(f'ID: {instr.confirm()}')

    print(f"Turning on input {instr.turn_on()}")

    time.sleep(1)
    print("Starting up constant power mode")
    print(f"Mode: {instr.const_power_mode()}")

    #time.sleep(1)
    print("Turning on Power for 5 seconds ")

    print(f"Power set to {instr.set_power(1)} Watt(s)")

    #time.sleep(1)
    
    for i in range(5):
        print(f" Current Voltage: {instr.measure_voltage()} Volt(s)")
        print(f" Current Current: {instr.measure_current()} Amp(s)")
        
        time.sleep(1)

    print("Turning off power")
    print(f"Power set to {instr.set_power(0)} Watt(s)")
    print("Done with tests")

    print(f"Turning off: {instr.turn_off()}")

    for i in range(10):
        print(instr.read_errors())