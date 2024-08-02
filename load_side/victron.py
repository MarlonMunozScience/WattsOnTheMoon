""" Class responsible for interacting and communicating with the Victron MPPT"""

import logging
import serial 
import time


logging.basicConfig(level=logging.DEBUG)
#logging.debug('This will not get logged to console')

class victron:

    def __init__(self, port):
        self.port = port
        self.ser = serial.Serial(port, 19200, timeout=2)
        self.time_sleep = 0.5
        self.ser.close()
        self.header1 = ord('\r')
        self.header2 = ord('\n')
        self.hexmarker = ord(':')
        self.delimiter = ord('\t')
        self.key = ''
        self.value = ''
        self.bytes_sum = 0;
        self.state = self.WAIT_HEADER
        self.dict = {}
        #print("TEST")

    (HEX, WAIT_HEADER, IN_KEY, IN_VALUE, IN_CHECKSUM) = range(5)

    def input(self, byte):
        if byte == self.hexmarker and self.state != self.IN_CHECKSUM:
            self.state = self.HEX
            
        
        if self.state == self.WAIT_HEADER:
            self.bytes_sum += byte
            if byte == self.header1:
                self.state = self.WAIT_HEADER
            elif byte == self.header2:
                self.state = self.IN_KEY

            return None
        elif self.state == self.IN_KEY:
            self.bytes_sum += byte
            if byte == self.delimiter:
                if (self.key == 'Checksum'):
                    self.state = self.IN_CHECKSUM
                else:
                    self.state = self.IN_VALUE
            else:
                self.key += chr(byte)
            return None
        elif self.state == self.IN_VALUE:
            self.bytes_sum += byte
            if byte == self.header1:
                self.state = self.WAIT_HEADER
                self.dict[self.key] = self.value;
                self.key = '';
                self.value = '';
            else:
                self.value += chr(byte)
            return None
        elif self.state == self.IN_CHECKSUM:
            self.bytes_sum += byte
            self.key = ''
            self.value = ''
            self.state = self.WAIT_HEADER
            if (self.bytes_sum % 256 == 0):
                self.bytes_sum = 0
                return self.dict
            else:
                self.bytes_sum = 0
        elif self.state == self.HEX:
            self.bytes_sum = 0
            if byte == self.header2:
                self.state = self.WAIT_HEADER
        else:
            raise AssertionError()

    def read_data_single(self):
        self.ser.open()
        while True:
            data = self.ser.read()
            #print(data)
            for single_byte in data:
                
                packet = self.input(single_byte)
                
                if (packet != None):
                    self.ser.close()
                    return packet

    # Confirms there's a connection by querying about machine ID
    def confirm(self):
        self.ser.open()
        self.ser.write ( str.encode ( ":451\n" ))        # get product ID
        read_val = self.ser.read ( size = 16 )
        #read_val = read_val.rsplit('n')[0]
        #logging.debug(read_val)
        decoded_val = bytes.decode ( read_val )

        
        decoded_val = decoded_val.rsplit('\n')[0]

        print ( "prod: " + decoded_val )
        self.ser.close()

    # Sends command to Victron
    def send_command(self, command):
        self.ser.open()
        self.ser.write ( str.encode ( command + '\n' ))
        time.sleep(self.time_sleep)
        read_val = self.ser.read ( size = 16 )
        decoded_val = bytes.decode ( read_val )
        decoded_val = decoded_val.rsplit('\n')[0]
        print ( "command: " + decoded_val )
        self.ser.close()

    # Converts input to little endian hex
    def convert_to_hex(self, input):
        # Change unites from 1 to 0.1
        input = input * 10
        hex_input = hex(input)
        
        # Remove 0x
        hex_input = hex_input[2:]

            # Add leading 0 if needed
        if len(hex_input) % 2 != 0:
            hex_input = '0' + hex_input
        if len(hex_input) <= 2:
            hex_input = '00' + hex_input
        #print(hex_input)

        # Convert to little endian
        hex_input = hex_input[2:] + hex_input[0:2]

        return hex_input.upper()

    def checksum(self, command):
        message = []
        checksum = 0x55
        value = command
        # Remove leading :
        value = value[1:]
       
        if len(value) % 2 != 0:
            value = '0' + value

       

        for i in range(0, len(value), 2):
            message.append(int(value[i:i+2], 16 ))
        

        for i in range(len(message)):
            checksum -= message[i]

        print(hex(checksum & 0xFF).upper()[2:])

        if len(hex(checksum & 0xFF)) == 3:
            return '0' + hex(checksum & 0xFF).upper()[2:]
        else:
            return  hex(checksum & 0xFF).upper()[2:]

    # Creates command for current limit (without checksum)
    def current_limit(self, current):
        print(current)
        # Convert to little endian hex
        hex_input = self.convert_to_hex(current)
        print(hex_input)
        # Create command
        command = ':8F0ED00' + hex_input
        print(command)
        # Calculate checksum
        check_cmd = self.checksum(command)
        print(command + check_cmd)
        # Send command
        self.send_command(':' + command + check_cmd)

    #Grabs useful data from packet
    def parse_data(self, packet):
        # sample data
        data = {}
        """
        {'PID': '0xA073', 'FW': '161', 'SER#': 'HQ2125UJDMX', 'V': '45070', 'I': '0', 'VPV': '20', 'PPV': '0', 'CS': '0', 'MPPT': '0', 'OR': '0x00000001', 'ERR': '0', 
'LOAD': 'ON', 'H19': '34', 'H20': '34', 'H21': '1082', 'H22': '0', 'H23': '1', 'HSDS': '2'}
        """
        # data = {}
        # print(packet)
        data['bat_current'] = float(packet['I']) # Current in mA
        data['bat_voltage'] = float(packet['V']) # Voltage in mV
        data['in_voltage'] = float(packet['VPV']) # PV voltage in mV
        data['in_power'] = float(packet['PPV']) # PV power in W
        # data['energy'] = float(packet['E'])
        # data['state'] = int(packet['CS'])
        # data['mode'] = int(packet['MPPT'])
        # data['error'] = int(packet['ERR'])
        # data['load'] = packet['LOAD']

        # data['error'] = int(packet['CE'])
        # data['fault'] = int(packet['CF'])
        # data['temp'] = float(packet['T'])
        # data['current_limit'] = float(packet['IL'])
        return data

    # Reads and parses data from victron
    # Returns dictionary of data
    def read_parse(self):
        data_single = self.read_data_single()
        data = self.parse_data(data_single)
        return data


        




if __name__ == "__main__":
    vc = victron('COM7')
    vc.confirm()
    #vc.current_limit(10)
    data = vc.read_parse()
    print(data)
    # print(data['voltage'])