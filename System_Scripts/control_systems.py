"""
Code that controls the power supply and electronic load. This code is run on the control computer. It is responsible for converting functions into 
commands and sends/recieves commands and data from the power supply and electronic load.
"""

import socket
import time
import sys
#import numpy as np

# Control Systems for power supply and electronic load
class Phoebe: 
    def __init__(self, host_ip):
        self.host_ip = host_ip
        self.host_port = 9000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Creates the socket connection 
    def connect(self):
        print("Connecting to Phoebe at " + self.host_ip + ":" + str(self.host_port) + "...")
        self.sock.connect((self.host_ip, self.host_port))
        print("Connected!")
    
    # Handshake
    def hello(self):
        self.sock.sendall(b'hello')
        data = self.sock.recv(1024)
        return data
    

    def check_connection(self):
        phoebe_expected = b'Hello!!!!'
        
        phoebe_response = self.hello()

        if phoebe_response != phoebe_expected:
            print("Phoebe is not connected")
            sys.exit()
        else:
            print("Phoebe is connected")
        
    
    def send_ctrlc(self):
        self.sock.sendall(b'CTRLC')
        data = self.sock.recv(1024)
        return data.decode() # Returns nothing if successful


    ######## Electronic Load ########
    # Sets up the load
    def setup(self):
        self.sock.sendall(b'setup')
        data = self.sock.recv(1024)
        return data.decode() # Returns Load ID Number if successful
    
    # Turns on the load 
    def turn_on(self):
        self.sock.sendall(b'on')
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode() # Returns "Electronic Load is on" if successful
    
    # Turns off the load
    def turn_off(self):
        self.sock.sendall(b'off')
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode() # Returns "Electronic Load is off" if successful

    # Sets the mode of the load
    def set_mode(self, mode):
        # CC = Constant Current
        if mode == "CC":
            self.sock.sendall(b'mode,CC')
            data = self.sock.recv(1024)
            print(data.decode())
            return data.decode() # Returns "Mode: CC" if successful
        
        # CW = Constant Power
        elif mode == "CW":
            self.sock.sendall(b'mode,CW')
            data = self.sock.recv(1024)
            print(data.decode())
            return data.decode()

    # Sets the power of the load
    def set_power(self, power):
        self.sock.sendall(b'power,' + str(power).encode())
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode() # Returns "Power set to: " + power if successful
    
    # Sets the current of the load
    def set_current(self, current):
        self.sock.sendall(b'current,' + str(current).encode())
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode() # Returns "Current set to: " + current if successful
    
    # Measures voltage of the load
    def measure_voltage(self):
        self.sock.sendall(b'meas_voltage')
        data = self.sock.recv(1024)
        return data # Returns voltage in V (as string)
    
    # Measures current of the load
    def measure_current(self):
        self.sock.sendall(b'meas_current')
        data = self.sock.recv(1024)
        return data # Returns current in A (as string)
    
    ######## Power Supply ########

    # Asks Power Supply if it is connected
    def PS_confirm(self):
        self.sock.sendall(b'PS_confirm')
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode() # Returns IDN of Power Supply if successful
    
    # Turns on the power supply
    def PS_turn_on(self):
        self.sock.sendall(b'PS_turn_on')
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode() # Returns "Power Supply is on" if successful
    
    # Turns off the power supply
    def PS_turn_off(self):
        self.sock.sendall(b'PS_turn_off')
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode() # Returns "Power Supply is off" if successful
    
    # Sets the voltage of the power supply
    def PS_set_voltage(self, voltage):
        self.sock.sendall(b'PS_set_voltage,' + str(voltage).encode())
        data = self.sock.recv(1024)
        print(data.decode()) 
        return data.decode() # Returns Measure Voltage (as string)
    
    # Sets the current of the power supply
    def PS_set_current(self, current):
        self.sock.sendall(b'PS_set_current,' + str(current).encode())
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode() # Returns Measure Current (as string)
    
    # Measures voltage of the power supply
    def PS_meas_voltage(self):
        self.sock.sendall(b'PS_meas_voltage')
        data = self.sock.recv(1024)
        return data.decode() # Returns voltage in V (as string)
    
    # Measures current of the power supply
    def PS_meas_current(self):
        self.sock.sendall(b'PS_meas_current')
        data = self.sock.recv(1024) 
        return data.decode() # Returns current in A (as string)
    
    # Measures power of the power supply
    def PS_meas_power(self):
        self.sock.sendall(b'PS_meas_power')
        data = self.sock.recv(1024)
        return data.decode()   # Returns power in W (as string)
    
    # Calls the measure all command on the control computer. This returns an array 
    #   of strings which are the values of the measurements. Code also deciphers this.
    def measure_all(self):
        self.sock.sendall(b'measure_all')
        data = self.sock.recv(1024)

        # returns [BK Load Voltage (V), BK Load Current (A), BK Load Power (W), PS Voltage (V), PS Current (A), PS Power (W)]
        # Decoding the data inside of the function
        data = data.decode()
        data = data.split(',')
        data[0] = data[0].strip('[')
        data[-1] = data[-1].strip(']')
        data = [i.strip("'") for i in data]
        data = [i.strip(" '") for i in data]
        data = [i.strip("b") for i in data]
        data = [i.strip("\\n") for i in data]
        data = [i.strip("b'") for i in data]
        data = [float(i) for i in data]
        return data
    

    ######## SPD Power Supply ########
    def SPD_setup(self):
        self.sock.sendall(b'SPD_setup')
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode()
    
    def SPD_confirm(self):
        self.sock.sendall(b'SPD_confirm')
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode()
    
    def CH1_set_voltage(self, voltage):
        self.sock.sendall(b'CH1_set_voltage,' + str(voltage).encode())
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode()
    
    def CH1_set_current(self, current):
        self.sock.sendall(b'CH1_set_current,' + str(current).encode())
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode()
    
    def CH1_turn_on(self):
        self.sock.sendall(b'CH1_set_output,on')
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode()

    def CH1_turn_off(self):
        self.sock.sendall(b'CH1_set_output,off')
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode()
    
    # This Code makes sure that the CH1 is in the correct state for the reverse start.
    def CH1_check(self, cmd):
        function_dict = {
            "turn on": self.CH1_turn_on,
            "turn off": self.CH1_turn_off,
        }
        response = function_dict[cmd]()
        if cmd =="turn on":
            if response != "ON":
                self.CH1_turn_off()
                print("Unable to turn on CH1")
                raise Exception("Unable to turn on CH1")
        elif cmd == "turn off":
            if response != "OFF":
                self.CH1_turn_off()
                print("Unable to turn off CH1")
                raise Exception("Unable to turn off CH1")

    def CH2_turn_on(self):
        self.sock.sendall(b'CH2_set_output,on')
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode()

    def CH2_turn_off(self):
        self.sock.sendall(b'CH2_set_output,off')
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode()  
 



# Code to test the class
if __name__ == "__main__":
    control_system = Phoebe("192.168.1.71")
    control_system.connect()
    print(control_system.hello())
    control_system.check_connection()
    print("Testing Load")
    print(control_system.setup())
    #print(control_system.turn_on())
    print(control_system.set_mode("CW"))
    input("Press Enter to continue...")
    control_system.turn_on()
    for i in range(1):
        print(control_system.set_power(i))
        print(control_system.measure_voltage())
        print(control_system.measure_current())
        time.sleep(1)
    print(control_system.set_power(0))
    #print(control_system.turn_off())

    print("Testing Power Supply")
    control_system.PS_confirm()
    control_system.PS_set_voltage(1)
    control_system.PS_set_current(1)
    control_system.PS_turn_on()

    for i in range(1):
        print(control_system.PS_meas_voltage())
        print(control_system.PS_meas_current())
        print(control_system.PS_meas_power())
        time.sleep(1)
    
    # Testing measurement all function
    print(control_system.measure_all())

    # Turning Everything off
    control_system.PS_turn_off()
    control_system.turn_off()

    # Testing SPD functions
    print("\n")
    print("Testing SPD")
    print("\n")

    control_system.SPD_confirm()
    control_system.CH1_set_voltage(1)
    control_system.CH1_set_current(0.25)

    control_system.CH1_check("turn on")
    control_system.CH1_check("turn off")


