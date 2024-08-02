import time
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import json
from datetime import datetime
import logging



class adc():
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.gain = 1
        self.mode = 0
        self.data_rate = 128
        self.address = 0x48

        self.ads = ADS.ADS1015(i2c, gain=self.gain, data_rate=self.data_rate, mode=self.mode, address=self.address)

        self.load_current = AnalogIn(self.ads, ADS.P0)
        self.load_voltage = AnalogIn(self.ads, ADS.P1)
        self.batt_current = AnalogIn(self.ads, ADS.P2)
        self.batt_voltage = AnalogIn(self.ads, ADS.P3)

        self.adc_vals = json.load(open("/home/periscope/Code/BCM/control_V2/main/load_adc_check.json"))

        # Code to log values
        # Code to grab current time
        current_datetime = datetime.now()
        current_datetime_str = current_datetime.strftime("%m-%d--%H-%M-%S")

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(filename=fr'/home/periscope/Code/BCM/control_V2/main/{current_datetime_str}.log', filemode='w', level=logging.DEBUG)

        logging.debug("\n")
        logging.debug("\n")
        logging.debug("\n")
        logging.debug("\n")
        logging.debug("\n")
        logging.debug(f"{current_datetime_str}")
        logging.debug('Script has started') 



    def read_load_current(self):
        value = self.load_current.voltage
        #print(f"DEBUG: Raw load current value {(value - 3.3/2)/ 0.05}")
        logging.debug(f"Raw load current value {(value - 3.3/2)/ 0.05}")
        return -1 * (value - 3.3/2)/ 0.05 # BI-directional so we need to multiply by negative 1
    
    def read_batt_current(self):
        value = self.batt_current.voltage
        logging.debug(f"Raw batt current value {(value - 3.3/2)/ 0.05}")
        return (value - 3.3/2)/ 0.05
    
    def read_load_voltage(self):
        value = self.load_voltage.voltage
        #print(f"DEBUG: Raw load voltage value {value}")
        value = value * 9.2305
        
        return value
    
    def read_batt_voltage(self):
        value = self.batt_voltage.voltage
        value = value * 9.1996
        
        return value
    
    def read_all(self):
        list = []
        list.append(self.read_load_current())
        list.append(self.read_load_voltage())
        list.append(self.read_batt_current())
        list.append(self.read_batt_voltage())
        return list
    
    def check_all(self, adc_list):
        for i, r in enumerate(self.adc_vals):
            if adc_list[i] < r["low"] or adc_list[i] > r["high"]:
                print(f"{adc_list[i]} is not between {r['low']} and {r['high']}")
                print(f"ADC {r['ADC']} is out of range")
                logging.debug(f"{adc_list[i]} is not between {r['low']} and {r['high']}")
                raise Exception(f"ADC {r['ADC']} is out of range")
        #print("All ADCs are within range")



