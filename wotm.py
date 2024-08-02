"""
This is the main algorithm for Watts on the Moon. It is wrapped in a class so that it can be called by the GUI.

The code consists of 2 parts: The setup that sets up the system and the main loop that runs the algorithm.

The main algorithm is respoinsible for the start up sequence as well as the data collection and control of the system.


"""



# Standard imports
import os 
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning) # Need with pandas
import pandas as pd
from datetime import datetime
import time
import xlsxwriter
import traceback
import numpy as np
import sys
import matplotlib.pyplot as plt
import logging
logging.getLogger('matplotlib').setLevel(logging.WARNING)
from PyQt6.QtCore import QObject, QThread, pyqtSignal

# Custom imports
from System_Scripts.source_system import source_pi
from System_Scripts.load_system import load_pi
from System_Scripts.control_systems import Phoebe
from System_Scripts.Threads import WatchDoginator

# Main WOTM Algorithm. This is the main class that will be called by the GUI
class wotm_controller(QObject):
    #Multithreading stuff
    finished = pyqtSignal()
    dfsignal = pyqtSignal(pd.DataFrame)

    def __init__(self):
        super().__init__()

        # Parameters
        self.charge_mode = False
        self.num_data_per_period = 1
        self.sleep_period = 0.1
        self.data_name = "test"

        ## System Objects
        # Reading Excel file and grabbing columns we are interested in
        load_data = pd.read_excel('Load_Profile_Data_Figure1_WOTM-with energy-storage-b.xlsx', sheet_name='With energy storage')

        # Load (Watts)
        self.NASA_load_bank = load_data['NASA Load Bank (W) = Power Out of Battery 2 + Power into Battery 2 (=power transmitted that gets to battery 2 = A9*A11)'].to_numpy()

        # If power supply is on or off
        self.NASA_power_state = load_data['NASA Power Supply (state) 1=ON, 0=OFF'].to_numpy()

        # Power_supply (Watts)
        self.NASA_power_supply = load_data['NASA Supply Available (watts)'].to_numpy()

        
        # Creating Dataframe to store data (32 things to record)
        self.df = pd.DataFrame(columns=['Time', 'Source in Current (A)', 'Source in Voltage (V)',        # transmit side
                                'BCM LV IN Voltage (V)', 'BCM LV IN Current (A)',                # transmit side
                                'Transmit Battery Voltage (V)', 'Transmit Battery Current (A)',  # transmit side
                                '400 Line Voltage (V)', '400 Line Current (A)',                  # transmit side
                                'Load Side Voltage (V)', 'Load Side Current (A)',                # load side
                                'Load Battery Voltage (V)', 'Load Battery Current (A)',          # load side
                                'BCM Voltage In (V)', 'BCM Voltage Out (V)',                     # load side   
                                'BCM Current In (A)', 'BCM Current Out (A)',                     # load side
                                'Source Victron Voltage (V)', 'Source Victron Current (A)',      # transmit side
                                'Source Victron VPV (V)', 'Source Victron WPV (W)',              # transmit side
                                'Load Victron Voltage (V)', 'Load Victron Current (A)',          # load side
                                'Load Victron VPV (V)', 'Load Victron WPV (W)',                  # load side
                                'BK Load Voltage (V)', 'BK Load Current (A)','BK Load Power (W)',# Phoebe
                                'PS Voltage (V)', 'PS Current (A)', 'PS Power (W)',              # Phoebe
                                    ])
        #logging.debug("Initialization created")


    ##### Phoebe Functions #####
    # Connect to Phoebe
    def phoebe_connect(self):
        print("connecting to phoebe")
        try:
            self.ctrl = Phoebe("192.168.1.71")
            self.ctrl.connect()
            self.ctrl.check_connection()
            return True
        except:
            print("Phoebe connection failed")
            return False

    # Sends ctrl-c to Phoebe
    def phoebe_ctrlc(self):
        self.ctrl.send_ctrlc()

    # Checks if Phoebe is connected
    def phoebe_hello(self):
        self.ctrl.check_connection()

    # Sets up the electronic load to the correct settings
    def phoebe_load_setup(self):
        self.ctrl.set_mode("CW")
        self.ctrl.set_power(100)
        print("Load setup complete")

    # Sets up the power supply to the correct settings
    def phoebe_source_setup(self):
        # Check that power supply is properly connected
        self.ctrl.PS_confirm()

        # Set power supply parameters
        self.ctrl.PS_set_voltage(120)
        self.ctrl.PS_set_current(20)
        print("Power supply setup complete")

    ##### Load Functions #####
    # Connects to load board socket
    def load_connect(self):
        print("connecting to load")
        try:
            self.load = load_pi("192.168.1.66")
            self.load.connect()
            self.load.check_connection()
            return True
        except:
            print("Load connection failed")
            return False

    # Sends ctrl-c to load board
    def load_ctrlc(self):
        self.load.send_ctrlc()

    # Checks if load board is connected (not used rn)
    def load_hello(self):
        pass

    ##### Source Functions #####
    def source_connect(self):
        print("connecting to source")
        try:
            self.source = source_pi("192.168.1.56")
            self.source.connect()
            self.source.check_connection()
            return True
        except:
            print("Source connection failed")
            return False

    # Sends ctrl-c to source
    def source_ctrlc(self):
        self.source.send_ctrlc()

    # Checks if source is connected (not used rn)
    def source_hello(self):
        pass

    ################### General Function ###################
    # Creates a folder to store data in /data
    def data_folder(self):
        now = datetime.now()
        dt_string = now.strftime('-%m-%dT%H%M')
        # Create folder under data folder
        self.folder = 'data/' + self.data_name + dt_string
        parent_dir = r"C:\Users\Lubin\Desktop\code\WOTM_GUI"
        self.folder = os.path.join(parent_dir, self.folder)
        os.mkdir(self.folder)

        # Logging
        f = open(self.folder + "/log.txt", "w")
        f.write("Log file for WOTM experiment\n")
        f.close()

        logging.basicConfig(filename=(self.folder + "/log.txt"), encoding='utf-8', level=logging.DEBUG)
        print("Data folder created")
        logging.debug("Data folder created")



    ################### Main Function ###################

    # Sets up the system
    # This function is ran when the start button is pressed in the gui (before the pop up window)
    def setup(self):
        if self.charge_mode:
            self.source_cap = 4.08
        else:
            self.source_cap = 4.1

        ################### Load System Setup ###################
        self.phoebe_load_setup()

        ################### Source System Setup ##################
        self.phoebe_source_setup()

        ################### House Keeping ###################

        # Setting up data folder
        self.data_folder()
        
        self.full_time = round((len(self.NASA_load_bank) * self.num_data_per_period * (6.1))/60, 2)
        print(f"This test will take {self.full_time} minutes to complete")
        logging.debug("Setup complete")

        # User input to start test (in gui)

    # Runs the main experiment after the pop up window
    def run_main(self):

        # Try statement for error control
        try:
            print("Starting experiment")
            logging.debug("Starting experiment")
            
            # Sending Hello to restart time out timer
            self.load.check_connection()
            self.source.check_connection()

            #################### Transmit System ####################
            print("Setting up transmit side")

            # Start main power supply
            self.ctrl.PS_turn_on()
            logging.debug("Power supply turned on")

            # Turn on the ssr connected to the 120 line 
            self.source.check_switch_high("ssr_120")

            time.sleep(0.5)

            # Check that SOURCE IN Voltage is around 120V and Source in current is around 0A
            self.source.read_and_check_sensor("Source In Voltage")
            time.sleep(0.5)
            self.source.read_and_check_sensor("Source In Current")

            logging.debug("Setting up transmit side, all switches/sensors checked")
            time.sleep(5)

            # Read transmit bat voltage
            self.source.read_and_check_sensor("Source Victron Voltage")

            time.sleep(0.5)

            # Turn on the bcm_lv_feed switch
            self.source.check_switch_high("bcm_lv_feed")

            logging.debug("BCM LV Feed turned on and checked")

            time.sleep(5)

            # Run the reverse start for the bcm
            self.ctrl.CH1_check("turn on")
            time.sleep(2)
            self.ctrl.CH1_check("turn off")

            logging.debug("Reverse start complete")

            time.sleep(5)

            # Turn on the ssr connected to the 400 line 
            self.source.check_switch_high("ssr_400")
            time.sleep(0.5)

            # Check if 400 Line voltage is above 330V
            self.source.read_and_check_sensor("400 Line Voltage")

            logging.debug("400 Line voltage set high and checked")

            time.sleep(5)

            logging.debug("Source System Setup Complete")


            #################### Load System ####################
            print("Setting up load side")
            logging.debug("Setting up load side")

            # Turning on the HV line
            self.load.check_switch_high("hv_line")

            
            time.sleep(5)

            # Activates BCM once there's high voltage (needed for i2c communication)
            self.load.bcm_activate()

            #bcm check input and output voltage
            self.load.read_and_check_sensor("BCM Voltage In")
            time.sleep(1)
            self.load.read_and_check_sensor("BCM Voltage Out")


            # Turning on the BCM_LV_FEED switch
            self.load.check_switch_high("bcm_lv_ssr")

            logging.debug("BCM turned on and checked")

            time.sleep(5)

            # Check that load victron works
            self.load.read_and_check_sensor("Load Victron Voltage")

            # Turn on the Load SSR
            self.load.check_switch_high("load_ssr")

            logging.debug("Load SSR turned on and checked")

            # Check load side voltage
            #pi_load.read_and_check_sensor("Load Side Voltage") # This is not working, commented out for now     

            logging.debug("Load System Setup Complete")
            #################### Data Collection ####################
            print("Setup Complete, all initial checks passed")
            print("Starting data collection")
            logging.debug("Starting data collection")
            

            # Turn on the load if not in charge mode (charge mode is for adding energy into the battery, so no load is needed)
            if self.charge_mode == False:
                self.ctrl.turn_on()

            #input__ = input("Press enter to start data collection")
            start_time = datetime.now()


            # Set up the watchdog threads
            # These check the battery voltages between the lower and upper thresolds every (sleep) seconds and throws an error if it is outside the range
            source_battery_watchdog = WatchDoginator(threshold_upper=self.source_cap, threshold_lower=3.2,sleep=15,value_adjust=13, name="Source Battery")
            load_battery_watchdog = WatchDoginator(threshold_upper=4.12, threshold_lower=3.2,sleep=15,value_adjust=7,  name="Load Battery")
            source_battery_watchdog.start()
            load_battery_watchdog.start()

            logging.debug("Data Collection Started")

            # Send signals to turn on adc monitoring on source and load board. (This is a watchdog process on the rpi in order to check all adc values are reasonable)
            self.source.begin_monitoring()
            self.load.begin_monitoring()

            # Begin data collection Loop\

            # Here we are looping through each step in the load profile
            for count in range(len(self.NASA_load_bank)):

                # Check if the watchdog threads have thrown an erro
                if self.thread().isInterruptionRequested():
                    print("exiting test")
                    logging.debug("exiting test on stop button")
                    raise Exception("exiting test")  
                
                # Housekeeping
                print("Step: " + str(count))
                logging.debug("Step: " + str(count))

                # Setting power to load
                self.ctrl.set_power(self.NASA_load_bank[count])

                # Setting Power Supply
                if self.NASA_power_state[count] == 1:
                    self.ctrl.PS_turn_on()
                    self.ctrl.PS_set_voltage(120)
                else: 
                    # If charge mode is true, then we don't want to turn off the power supply
                    if self.charge_mode == False:
                        self.ctrl.PS_turn_off()
                    #instr_power.set_voltage(28)

                # In each load profile step, we want to take a set amount of data points (num_data_per_period)
                for data_count in range(self.num_data_per_period):
                    logging.debug("Data point: " + str(data_count))


                    #### Watchdog check ####

                    # Check if the watchdog threads have thrown an error
                    if self.thread().isInterruptionRequested():
                        print("exiting test")
                        raise Exception("exiting test")  
                    time.sleep(self.sleep_period)
                    if source_battery_watchdog.shutdown_requested == True or load_battery_watchdog.shutdown_requested == True:
                        print("Shutdown requested, shutting down")
                        raise Exception("Shutdown requested")
                    

                    #### Data Collection ####

                    # Read ADCS on the source side
                    adc_data_source = self.source.decipher_adcs(self.source.read_adcs())
                    source_battery_watchdog.update_value(adc_data_source[4])

                    # Read ADCS on the load side
                    adc_data_load = self.load.decipher_adcs(self.load.read_adcs())
                    load_battery_watchdog.update_value(adc_data_load[3])

                    # Read BCM on the load side
                    try:
                        bcm_data_load = self.load.decipher_bcm(self.load.bcm_read())
                    except:
                        print("error reading bcm")
                        bcm_data_load = [0,0,0,0]
                        pass

                    # Read power supply and load from Phoebe
                    phoebe_data = self.ctrl.measure_all()

                    # Read victrons from the transmit side
                    try:
                        victron_source = self.source.read_victrons()
                    except:
                        print("error reading victron")
                        victron_source = [0,0,0,0]
                        pass

                    # Read victrons from the load side
                    try:
                        victron_load = self.load.read_victrons()
                    except:
                        print("error reading victron")
                        victron_load = [0,0,0,0]
                        pass
                    
                    # Get Time 
                    now = datetime.now()
                    # Convert time to hours
                    time_elapsed = (now - start_time).total_seconds()/3600


                    #### Data Storage ####

                    # Adding data to the dataframe
                    self.df = self.df.append({"Time": time_elapsed*60, "Source in Current (A)": adc_data_source[0], "Source in Voltage (V)": adc_data_source[1], 
                                    "BCM LV IN Voltage (V)": adc_data_source[2], "BCM LV IN Current (A)": adc_data_source[3], 
                                    "Transmit Battery Voltage (V)": adc_data_source[4], "Transmit Battery Current (A)": adc_data_source[5], 
                                    "400 Line Voltage (V)": adc_data_source[6], "400 Line Current (A)": adc_data_source[7],
                                    'Load Side Voltage (V)': adc_data_load[1], 'Load Side Current (A)': adc_data_load[0], 
                                    'Load Battery Voltage (V)': adc_data_load[3], 'Load Battery Current (A)': adc_data_load[2],
                                    'BCM Voltage In (V)': bcm_data_load[0], 'BCM Voltage Out (V)': bcm_data_load[1], 
                                    'BCM Current In (A)': bcm_data_load[2], 'BCM Current Out (A)': bcm_data_load[3],
                                    'Source Victron Voltage (V)': victron_source[0], 'Source Victron Current (A)': victron_source[1],
                                    'Source Victron VPV (V)': victron_source[2], 'Source Victron WPV (W)': victron_source[3],
                                    'Load Victron Voltage (V)': victron_load[0], 'Load Victron Current (A)': victron_load[1],
                                    'Load Victron VPV (V)': victron_load[2], 'Load Victron WPV (W)': victron_load[3],
                                    'BK Load Voltage (V)': phoebe_data[0], 'BK Load Current (A)': phoebe_data[1], 'BK Load Power (W)': phoebe_data[2],
                                    'PS Voltage (V)': phoebe_data[3], 'PS Current (A)': phoebe_data[4], 'PS Power (W)': phoebe_data[5]
                                    }

                                    , ignore_index=True)
                    print(now)
                    print(f"Time Elapsed: {time_elapsed*60} Minutes")
                    print(f"Read {data_count} of {self.num_data_per_period} data points on step {count} of {len(self.NASA_load_bank)}")
                    self.dfsignal.emit(self.df)
                    #self.printer.print_tables(adc_data_source, adc_data_load, bcm_data_load, victron_source, victron_load, phoebe_data)
                    print("\n")

                   

        except BaseException:
            logging.debug(traceback.format_exc())
            print(traceback.format_exc())
            

        #### Shutdown Sequence ####
        finally:
            logging.debug("Shutting down")
            print("Shutting down")

        # Turning off switches on source side
            try:
                self.source.ssr_120_off() 
                time.sleep(1)
                self.source.bcm_lv_feed_off()
                time.sleep(1)
                self.source.ssr_400_off()
                time.sleep(1)
                logging.debug("Source side switches turned off")
                self.source.stop_monitoring()
            except:
                print("Error turning off source side switches")
                pass
            print("Source side switches turned off")

            # Turning off switches on load side
            try:
                self.load.hv_line_off()
                time.sleep(1)
                self.load.bcm_lv_ssr_off()
                time.sleep(1)
                self.load.load_ssr_off()
                time.sleep(1)
                logging.debug("Load side switches turned off")
                self.load.stop_monitoring()
            except:
                print("Error turning off load side switches")
                pass
            print("Load side switches turned off")

            # Turning off power supply
            try:
                self.ctrl.PS_turn_off()
                logging.debug("Power supply turned off")
                print("Power supply turned off")
            except:
                print("Error turning off power supply")
                pass

            # Turning off load
            try:
                self.ctrl.turn_off()
                logging.debug("Load turned off")
            except:
                print("Error turning off load")
                pass

            # Turning off SPD
            try:
                self.ctrl.CH1_check("turn off")
                logging.debug("SPD turned off")
            except:
                print("Error turning off SPD")
                pass

            try:
                self.ctrl.CH2_turn_off()
            except:
                pass
            
            logging.debug("Saving Data")
            # Saving data
            # Saving data to excel sheet
            try:
                writer = pd.ExcelWriter(f"{self.folder}/{self.data_name}.xlsx", engine='xlsxwriter')
                self.df.to_excel(writer, sheet_name='Sheet1')   

                # Auto-adjust columns' width
                for column in self.df:
                    column_width = max(self.df[column].astype(str).map(len).max(), len(column))
                    col_idx = self.df.columns.get_loc(column)
                    writer.sheets['Sheet1'].set_column(col_idx, col_idx, column_width)
                writer.save()
                print("Data saved")
                logging.debug("Data saved")
            except:
                logging.debug("Error saving data to excel sheet")
                logging.debug(traceback.format_exc())
                print("Error saving data to excel sheet")

            #plt.savefig(f"{self.folder}/{self.data_name}_1.png")
            #self.printer.print_graphs(self.df, ax, fig, self.full_time, final=True)
            #plt.savefig(f"{self.folder}/{self.data_name}_2.png")
            
            # Turning off watchdogs (multi-threading)
            try:
                source_battery_watchdog.shutdown_requested = True
                source_battery_watchdog.join()
                load_battery_watchdog.shutdown_requested = True
                load_battery_watchdog.join()
            except:
                print("Error joining watchdog threads")
                pass

            # Emitting signal to main thread to update GUI
            self.finished.emit()
            print("Experiment Finished, Feel free to close the program")
            print("Make sure to thank Marlon for his hard work")
            