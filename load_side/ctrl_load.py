import numpy as np
import RPi.GPIO as GPIO 
from smbus import SMBus 

class load_gpio():
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        self.hv_line_pin = 5 # pin 29
        self.bcm_lv_ssr_pin =  0 # pin 27
        self.load_ssr_pin = 11 # pin 23
        self.hv_present_led_pin = 9 # Pin 21

        GPIO.setup(self.hv_line_pin, GPIO.OUT)
        GPIO.setup(self.bcm_lv_ssr_pin, GPIO.OUT)
        GPIO.setup(self.load_ssr_pin, GPIO.OUT)
        GPIO.setup(self.hv_present_led_pin, GPIO.OUT)


    def hv_line(self, state):
        if state == "on":
            GPIO.output(self.hv_line_pin, GPIO.HIGH)
            return "hv_line on"
        elif state == "off":
            GPIO.output(self.hv_line_pin, GPIO.LOW)
            return "hv_line off"
        
    def bcm_lv_ssr(self, state):
        if state == "on":
            GPIO.output(self.bcm_lv_ssr_pin, GPIO.HIGH)
            GPIO.output(self.hv_present_led_pin, GPIO.HIGH)
            return "bcm_lv_ssr on"
        elif state == "off":
            GPIO.output(self.hv_present_led_pin, GPIO.LOW)
            GPIO.output(self.bcm_lv_ssr_pin, GPIO.LOW)
            return "bcm_lv_ssr off"
        
    def load_ssr(self, state):
        if state == "on":
            GPIO.output(self.load_ssr_pin, GPIO.HIGH)
            return "load_ssr on"
        elif state == "off":
            GPIO.output(self.load_ssr_pin, GPIO.LOW)
            return "load_ssr off"

class BCM:
    def __init__(self):
        self.i2c = SMBus(1) 
        self.i2caddress = 0x50
        
        self.READ_VIN = 0x88
        self.READ_IIN = 0x89
        self.READ_VOUT = 0x8B
        self.READ_IOUT = 0x8C



    # Activates BCM by setting page command from 00 to 01 (In order to read voltage)
    def activate(self):
        self.i2c.write_i2c_block_data(self.i2caddress, 0x00, [0x01])
        

    # Takes in an input of a list of two integers
    # Returns one integer
    def bcm_to_int(self, data_bcm):
        # First switch order of input
        
        data_bcm.reverse()
        # Convert to binary
        binary = ""
        for i in data_bcm:
            binary += format(i, '08b')

        # Convert to integer
        integer = int(binary, 2)
        return integer
    
    # Converts raw data into real world values
    # Data is a integer (converted by bcm_to_int)
    def calc_bcm(self, data_int, cmd):
        
        switch = {
            "READ_VIN": [1, 1, 0],
            "READ_IIN": [1, 3, 0],
            "READ_VOUT": [1, 1, 0],
            "READ_IOUT": [1, 2, 0],

        }
        array = switch.get(cmd, "Invalid command")
        m = array[0]
        r = array[1]
        b = array[2]
        #print(data_int)
        #print(type(data_int))
        value = (data_int * 10**(-r) - b) / m
        return value   

    # Reads all data from BCM
    # Outputs a list of two integers
    def read_bcm(self, i2c, i2c_cmd):
        bcm_data = i2c.read_i2c_block_data(self.i2caddress, i2c_cmd)
        bcm_data = bcm_data[0:2] # Grabs first two elements
        return bcm_data

    # Reads all data from BCM
    def bcm_read_all(self):
        # Voltage in 
        bcm_list = []
        vin = self.bcm_to_int(self.read_bcm(self.i2c, self.READ_VIN))
        vin = self.calc_bcm(vin, "READ_VIN")
        bcm_list.append(vin)

        # Voltaself.ge out
        vout = self.bcm_to_int(self.read_bcm(self.i2c, self.READ_VOUT))
        vout = self.calc_bcm(vout, "READ_VOUT")
        bcm_list.append(vout)

        # Current in
        iin = self.bcm_to_int(self.read_bcm(self.i2c, self.READ_IIN))
        iin = self.calc_bcm(iin, "READ_IIN")
        bcm_list.append(iin)

        # Current out
        iout = self.bcm_to_int(self.read_bcm(self.i2c, self.READ_IOUT))
        iout = self.calc_bcm(iout, "READ_IOUT")
        bcm_list.append(iout)

        return bcm_list 
    