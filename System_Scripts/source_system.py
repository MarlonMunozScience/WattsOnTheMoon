import socket
import time
import sys
import json
import numpy as np
class source_pi:
    def __init__(self, host_ip):
        self.host_ip = host_ip
        self.host_port = 9002
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
            print("Both Raspberry Pi and Pyboard are connected")
    
    def ssr_120_on(self):
        self.sock.sendall(b'ssr_120,on')
        data = self.sock.recv(1024)
        return data.decode()
    
    def ssr_120_off(self):
        self.sock.sendall(b'ssr_120,off')
        data = self.sock.recv(1024)
        return data.decode()
    
    def bcm_lv_feed_on(self):
        self.sock.sendall(b'bcm_lv_feed,on')
        data = self.sock.recv(1024)
        return data.decode()
    
    def bcm_lv_feed_off(self):
        self.sock.sendall(b'bcm_lv_feed,off')
        data = self.sock.recv(1024)
        return data.decode()
    
    def ssr_400_on(self):
        self.sock.sendall(b'ssr_400,on')
        data = self.sock.recv(1024)
        return data.decode()

    def ssr_400_off(self):
        self.sock.sendall(b'ssr_400,off')
        data = self.sock.recv(1024)
        return data.decode()
    
    def check_switch_high(self, cmd):
        function_dict = {
            'ssr_120': self.ssr_120_on,
            'bcm_lv_feed': self.bcm_lv_feed_on,
            'ssr_400': self.ssr_400_on}
        response = function_dict[cmd]()
        print(response)
        if response != cmd + ' on':
            print("Error: " + cmd + " not on")
            raise Exception("Error: " + cmd + " not on")
        else:
            print(cmd + " on")

    
    def read_adcs(self):
        self.sock.sendall(b'read_adcs')
        # Receives [Source In Current, Source In Voltage, TE bcm_lv_in voltage, TE bcm_lv_in current, TE Battery Voltage, TE Battery Current, 400 Line Voltage, 400 Line Current]
        data = self.sock.recv(1024)
        #print(data.decode())
        return data # No need to decode data here, main code will do it
    
    def decipher_adcs(self, data):
        try:
            data = data.decode().split(',')
            data[-1] = data[-1].rstrip('\r\n')
            data[0]  = data[0].strip('[')
            data[-1] = data[-1].strip(']')
            # Convert to floats
            data = [float(i) for i in data]

            #data[3] = data[3] * -1
            #data[7] = data[7] * -1
            # Round each value to 2 decimal places
            data = [round(i, 2) for i in data]
            return data
        except ValueError:
            raise Exception("Error in decipher_adcs")
    
    def try_read(self):
        data = self.sock.recv(1024)
        return data.decode()
    
    def bcm_status(self):
        self.sock.sendall(b'bcm_status')
        
        data = self.sock.recv(1024)
        print(data)
        data = data.decode().split(',')
        data[-1] = data[-1].rstrip('\r\n')
        return data
    
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
        function_dict = {"Source In Voltage": [self.read_adcs, self.decipher_adcs, 1, 118, 122], 
                         "Source In Current": [self.read_adcs, self.decipher_adcs, 0, -1, 1],
                         "Source Victron Voltage": [self.read_victrons, None, 0, 41, 53.5],
                         "400 Line Voltage": [self.read_adcs, self.decipher_adcs, 6, 320, 430],
        }
        response = function_dict[cmd][0]()
        if function_dict[cmd][1] != None:
            response = function_dict[cmd][1](response)

        response = response[function_dict[cmd][2]]
        
        if response < function_dict[cmd][3] or response > function_dict[cmd][4]:
            print(response)
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
    # Check that transmit Raspberry Pi is connected
    print("Checking that transmit Raspberry Pi is connected")
    pi_source =  source_pi("192.168.1.47")
    pi_source.connect()
    pi_source.check_connection()

    