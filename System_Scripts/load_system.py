"""
Code that controls the load side raspberry pi. This code is run on the raspberry pi computer on the load side.
It is responsible for converting functions into commands and sends/recieves commands and data from the load board.
"""

import socket
import time
import sys
import json
import numpy as np

class load_pi:
    def __init__(self, host_ip):
        self.host_ip = host_ip
        self.host_port = 9001
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        print("Connecting to Load Side Pi at " + self.host_ip + ":" + str(self.host_port) + "...")
        self.sock.connect((self.host_ip, self.host_port))
        print("Connected!")
    
    def hello(self):
        self.sock.sendall(b'hello')
        data = self.sock.recv(1024)
        return data
    
    def send_ctrlc(self):
        self.sock.sendall(b'CTRLC')
        data = self.sock.recv(1024)
        return data.decode()
    
    def check_connection(self):
        rpi_expected = b'Hello!!!!'
        
        rpi_response = self.hello()
        
        if rpi_response != rpi_expected:
            print("Raspberry Pi is not connected")
            sys.exit()
        
        else:
            print("Raspberry Pi is connected")

    def hv_line_on(self):
        self.sock.sendall(b'hv_line,on')
        # Receives "hv_line on" from the load side pi
        data = self.sock.recv(1024)
        return data.decode()
    
    def hv_line_off(self):
        self.sock.sendall(b'hv_line,off')
        # Receives "hv_line off" from the load side pi
        data = self.sock.recv(1024)
        return data.decode()
    
    def bcm_lv_ssr_on(self):
        self.sock.sendall(b'bcm_lv_ssr,on')
        # Receives "bcm_lv_ssr on" from the load side pi
        data = self.sock.recv(1024)
        return data.decode()
    
    def bcm_lv_ssr_off(self):
        self.sock.sendall(b'bcm_lv_ssr,off')
        # Receives "bcm_lv_ssr off" from the load side pi
        data = self.sock.recv(1024)
        return data.decode()
    
    def load_ssr_on(self):
        self.sock.sendall(b'load_ssr,on')
        # Receives "load_ssr on" from the load side pi
        data = self.sock.recv(1024)
        return data.decode()
    
    def load_ssr_off(self):
        self.sock.sendall(b'load_ssr,off')
        # Receives "load_ssr off" from the load side pi
        data = self.sock.recv(1024)
        return data.decode()
    
    # Checks if the switch is on, if not raises an exception
    def check_switch_high(self, cmd):
        function_dict = {
            "hv_line": self.hv_line_on,
            "bcm_lv_ssr": self.bcm_lv_ssr_on,
            "load_ssr": self.load_ssr_on
        }
        response = function_dict[cmd]()

        if response != cmd + " on":
            print(response)
            print(cmd + " not turned on")
            raise Exception(cmd + " not turned on")
        else:
            print(cmd + " turned on")
            return True
        
    
    def read_adcs(self):
        self.sock.sendall(b'read_adcs')
        # Receives [LE Load Current, LE Load Voltage, LE Battery Current, LE Battery Voltage]
        data = self.sock.recv(1024)
        return data # No need to decode, done in function  below
    
    def decipher_adcs(self, data):
        try:
            data = data.decode().split(',')
            data[-1] = data[-1].rstrip('\r\n')
            data[0]  = data[0].strip('[')
            data[-1] = data[-1].strip(']')
            # Convert to floats
            data = [float(i) for i in data]

            # Round each value to 2 decimal places
            data = [round(i, 2) for i in data]

            data[0] = abs(data[0]) # Load current is always positive
            data[2] = -1 * data[2] # Negative means out of the battery, Positve means into the battery

            return data
        except ValueError:
            raise Exception("Error in decipher_adcs")

    def bcm_read(self):
        self.sock.sendall(b'bcm_read')
        # Receives [VIN, VOUT, IIN, IOUT]
        data = self.sock.recv(1024)
        return data.decode()
    
    def decipher_bcm(self, data):
        data = data.split(',')
        data[-1] = data[-1].rstrip('\r\n')
        data[0]  = data[0].strip('[')
        data[-1] = data[-1].strip(']')
        # Convert to floats
        data = [float(i) for i in data]

        # Round each value to 2 decimal places
        data = [round(i, 2) for i in data]

        # If any value is higher than normal set it to 0
        for i in range(0,2):
            if data[i] > 1000:
                data[i] = 0
        
        for i in range(2,4):
            if data[i] > 10:
                data[i] = 0

        return data
    
    def bcm_activate(self):
        self.sock.sendall(b'bcm_activate')
        # Receives "bcm_activate" from the load side pi
        data = self.sock.recv(1024)
        return data.decode()
    
    def victron_confirm(self):
        self.sock.sendall(b'victron_confirm')
        # Receives product ID from the load side pi
        data = self.sock.recv(1024)
        print(data.decode())
        return data.decode()
    
    def read_victrons(self):
        self.sock.sendall(b'read_victrons')
        # Receives # a list of ["Batt Voltage", "Batt Current", in_voltage, "in_current"]
        data = self.sock.recv(1024)
        data = data.decode()
        data = data.replace("'", '"')
        data = json.loads(data)
        data = [data['bat_voltage'], data['bat_current'], data['in_voltage'], data['in_power']]
        data = [float(i) for i in data]

        data = [round(i, 2) for i in data]

        data = [i/1000 for i in data]
        
        return data
    
    # Reads in a value from a certain step, if the value is not the expected value, raises an exception
    def read_and_check_sensor(self, cmd):
        function_dict = {
            "Load Side Voltage": [self.read_adcs, self.decipher_adcs, 1, 22.2, 28.9],
            "Load Victron Voltage": [self.read_victrons, None, 0, 22.4, 28.9],
            "BCM Voltage In": [self.bcm_read, self.decipher_bcm, 0, 320, 500],
            "BCM Voltage Out": [self.bcm_read, self.decipher_bcm, 1, 40, 53],}

        response = function_dict[cmd][0]()
        if function_dict[cmd][1] != None:
            response = function_dict[cmd][1](response)
        
        response = response[function_dict[cmd][2]]

        if response < function_dict[cmd][3] or response > function_dict[cmd][4]:
            print(f"{cmd} is {response} and not in range of {function_dict[cmd][3]} to {function_dict[cmd][4]}")
            raise Exception(cmd + " not in range")
        else:
            print(f"DEBUG: {cmd} is {response} is in range of {function_dict[cmd][3]} to {function_dict[cmd][4]}")
            print(cmd + " in range")
            return True
        
    def begin_monitoring(self):
        self.sock.sendall(b'Monitor')
        data = self.sock.recv(1024)
        return data.decode()
    
    def stop_monitoring(self):
        self.sock.sendall(b'Stop_Monitor')
        data = self.sock.recv(1024)
        return data.decode()
    

if __name__ == "__main__":
    lp = load_pi("192.168.1.47")
    lp.connect()
    print(lp.hello())
    print(lp.hello_py())
    

