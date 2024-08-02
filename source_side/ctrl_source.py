import RPi.GPIO as GPIO

class source_gpio:
    def __init__(self):
        GPIO.setmode(GPIO.BCM) 
        GPIO.setwarnings(False)
        
        self.ssr_120_pin = 19 # Pin 35
        self.bcm_lv_feed_pin = 11 # Pin 23
        self.ssr_400_pin = 26 # pin 37
        self.hv_line_present_pin = 9 # Pin 21

        GPIO.setup(self.ssr_120_pin, GPIO.OUT)
        GPIO.setup(self.bcm_lv_feed_pin, GPIO.OUT)
        GPIO.setup(self.ssr_400_pin, GPIO.OUT)
        GPIO.setup(self.hv_line_present_pin, GPIO.OUT)


    def ssr_120(self, state):
        if state == "on":
            GPIO.output(self.ssr_120_pin, GPIO.HIGH)
            GPIO.output(self.hv_line_present_pin, GPIO.HIGH)
            return "ssr_120 on"
        elif state == "off":
            GPIO.output(self.ssr_120_pin, GPIO.LOW)
            GPIO.output(self.hv_line_present_pin, GPIO.LOW
                        )
            return "ssr_120 off"
        
        
    def bcm_lv_feed(self, state):
        if state == "on":
            GPIO.output(self.bcm_lv_feed_pin, GPIO.HIGH)
            return "bcm_lv_feed on"
        elif state == "off":
            GPIO.output(self.bcm_lv_feed_pin, GPIO.LOW)
            return "bcm_lv_feed off"
    
    def ssr_400(self, state):
        if state == "on":
            GPIO.output(self.ssr_400_pin, GPIO.HIGH)
            return "ssr_400 on"
        elif state == "off":
            GPIO.output(self.ssr_400_pin, GPIO.LOW)
            return "ssr_400 off"
    
    
""" # BCM Not in use for these tests
class BCM:
    def __init__(self):
        self.i2c = SMBus(1) 
        self.i2caddress = 0x50

        # Variables
        self.STATUS_WORD = 0x78
        self.STATUS_BYTE = 0x79
        self.STATUS_IOUT = 0x7B
        self.STATUS_INPUT = 0x7C
        self.STATUS_TEMPERATURE = 0x7D
        self.STATUS_MFR_SPECIFIC = 0x80



    # Reads all from BCM
    # Outputs a list of two integers
    def read_bcm(self, i2c, i2c_cmd):
        bcm_data = i2c.read_i2c_block_data(self.i2caddress, i2c_cmd)
        bcm_data = bcm_data[0:2] # Grabs first two elements
        return bcm_data
    
    # Queries the BCM for all status data
    # Outputs list of all status data
    def query_bcm_status(self):
        bcm_list = []

        bcm_list.extend(self.read_bcm(self.i2c, self.STATUS_WORD))
        bcm_list.extend(self.read_bcm(self.i2c, self.STATUS_BYTE))
        bcm_list.extend(self.read_bcm(self.i2c, self.STATUS_IOUT))
        bcm_list.extend(self.read_bcm(self.i2c, self.STATUS_INPUT))
        bcm_list.extend(self.read_bcm(self.i2c, self.STATUS_TEMPERATURE))
        bcm_list.extend(self.read_bcm(self.i2c, self.STATUS_MFR_SPECIFIC))

        return bcm_list

       """ 
