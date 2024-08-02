import time
import board
import busio
import adafruit_ads1x15.ads1015 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import json
import logging
from datetime import datetime

class adc():
    def __init__(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self.gain = 1
        self.mode = 0
        self.data_rate = 128
        

        self.ads1 = ADS.ADS1015(i2c, gain=self.gain, data_rate=self.data_rate, mode=self.mode, address=0x48) 
        self.ads2 = ADS.ADS1015(i2c, gain=self.gain, data_rate=self.data_rate, mode=self.mode, address=0x49)

        self.source_in_current = AnalogIn(self.ads1, ADS.P0)
        self.source_in_voltage = AnalogIn(self.ads1, ADS.P1)
        self.bcm_lv_in_voltage = AnalogIn(self.ads1, ADS.P2)
        self.bcm_lv_in_current = AnalogIn(self.ads1, ADS.P3)

        self.line_voltage_400 = AnalogIn(self.ads2, ADS.P0)
        self.line_current_400 = AnalogIn(self.ads2, ADS.P1)
        self.batt_voltage = AnalogIn(self.ads2, ADS.P2)
        self.batt_current = AnalogIn(self.ads2, ADS.P3)

        self.adc_vals = json.load(open("/home/pi/code/control_source/source_adc_check.json"))
        # Code to log values
        # Code to grab current time
        current_datetime = datetime.now()
        current_datetime_str = current_datetime.strftime("%m-%d--%H-%M-%S")

        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        logging.basicConfig(filename=fr'/home/pi/code/control_source/{current_datetime_str}.log', filemode='w', level=logging.DEBUG)

        logging.debug("\n")
        logging.debug("\n")
        logging.debug("\n")
        logging.debug("\n")
        logging.debug("\n")
        logging.debug(f"{current_datetime_str}")
        logging.debug('Script has started')

    def read_source_in_current(self):
        value = self.source_in_current.voltage
        #print(f"DEBUG: Raw Source In current is {value}")
        logging.debug(f"Raw Source In current is {(value - 3.3/10)/ 0.1}")
        return (value - 3.3/10)/ 0.1
    
    def read_source_in_voltage(self):
        value = self.source_in_voltage.voltage
        return value * (150/2)
    
    def read_bcm_lv_in_voltage(self):
        value = self.bcm_lv_in_voltage.voltage
        return value * (55/2)
    
    def read_bcm_lv_in_current(self):
        value = self.bcm_lv_in_current.voltage
        #print(f"DEBUG: Raw BCM LV current is {value}")
        logging.debug(f"Raw BCM LV current is {-1 * (value - 3.3/2)/ 0.05}")
        return -1 * (value - 3.3/2)/ 0.05
    
    def read_line_voltage_400(self):
        value = self.line_voltage_400.voltage
        return value * (450/2)
    
    def read_line_current_400(self):
        value = self.line_current_400.voltage
        logging.debug(f"Raw Line current is {-1 *(value - 3.3/2)/ 0.2}")
        return -1 * (value - 3.3/2)/ 0.2 # BI-Directional Current Sensor, needs to multiply by -1 to get correct value
    
    def read_batt_voltage(self):
        value = self.batt_voltage.voltage
        #print(f"DEBUG: Bat Volt is {value * (55/2)}")
        return value * (55/2)
    
    def read_batt_current(self):
        value = self.batt_current.voltage
        #print(f"DEBUG: Raw Bat current is {value}")
        logging.debug(f"Raw Bat current is {(value - 3.3/2)/ 0.05}")
        return (value - 3.3/2)/ 0.05
    
    def read_all(self):
        list = []
        list.append(self.read_source_in_current())
        list.append(self.read_source_in_voltage())
        list.append(self.read_bcm_lv_in_voltage())
        list.append(self.read_bcm_lv_in_current())
        list.append(self.read_batt_voltage())
        list.append(self.read_batt_current())
        list.append(self.read_line_voltage_400())
        list.append(self.read_line_current_400() )
        return list
    
    def check_all(self, adc_list):
        for i, r in enumerate(self.adc_vals):
            if adc_list[i] < r["low"] or adc_list[i] > r["high"]:
                print(f"{adc_list[i]} is not between {r['low']} and {r['high']}")
                print(f"ADC {r['ADC']} is out of range")
                logging.debug(f"ADC {r['ADC']} is out of range")
                logging.debug(f"{adc_list[i]} is not between {r['low']} and {r['high']}")
                raise Exception(f"ADC {r['ADC']} is out of range")
        print("All ADCs are within range")


