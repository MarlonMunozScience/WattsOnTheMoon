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

# Custom imports
from System_Scripts.source_system import source_pi
from System_Scripts.load_system import load_pi
from System_Scripts.control_systems import Phoebe
from System_Scripts.plotsnprints import printinator
from System_Scripts.Threads import WatchDoginator

printer = printinator()
########################################################################
################# Check that all systems are connected #################
########################################################################

# Check that load Raspberry Pi is connected
print("Checking that load Raspberry Pi is connected")
pi_load =  load_pi("192.168.1.66")
pi_load.connect()
pi_load.check_connection()

# Check that transmit Raspberry Pi is connected
print("Checking that transmit Raspberry Pi is connected")
pi_source =  source_pi("192.168.1.56")
pi_source.connect()
pi_source.check_connection()

# Checking that Phoebe is connected
print("Checking that Phoebe is connected")
ctrl = Phoebe("192.168.1.71")
ctrl.connect()
ctrl.check_connection()

print("Phoebe connected properly")
print("All systems connected properly")

#########################################################
################# Instrumentation Setup #################
#########################################################

################### Initial Parameters ##################
charge_mode = False 
num_data_per_period = 1
time_sleep_period = 0.1

if charge_mode == True:
    source_cap = 4.08
else:
    source_cap = 4.1
################### Load System Setup ###################

# Set load parameters (load setup is done in Phoebe)
ctrl.set_mode("CW")
ctrl.set_power(100)
print("Load setup complete")


################### Source System Setup ##################

# Check that power supply is properly connected
ctrl.PS_confirm()

# Set power supply parameters
ctrl.PS_set_voltage(120)
ctrl.PS_set_current(20)
print("Power supply setup complete")


####################### SPD Setup ########################

# Checking SPD is connected
ctrl.SPD_confirm()

# Set SPD parameters for channel 1 (for reverse start)
ctrl.CH1_set_voltage(30)
ctrl.CH1_set_current(3)
print("SPD setup complete")


####################### Victron Setup ######################

# Check that Victron is connected
#pi_source.victron_confirm()
#pi_load.victron_confirm()
print("Victrons are connected")

#########################################################
#################### Data Setup #########################
#########################################################

# Reading Excel file and grabbing columns we are interested in
load_data = pd.read_excel('Load_Profile_Data_Figure1_WOTM-with energy-storage-b.xlsx', sheet_name='With energy storage')

# Load (Watts)
NASA_load_bank = load_data['NASA Load Bank (W) = Power Out of Battery 2 + Power into Battery 2 (=power transmitted that gets to battery 2 = A9*A11)'].to_numpy()

# If power supply is on or off
NASA_power_state = load_data['NASA Power Supply (state) 1=ON, 0=OFF'].to_numpy()

# Power_supply (Watts)
NASA_power_supply = load_data['NASA Supply Available (watts)'].to_numpy()



# Get test name from user
data_name = input("Enter title for test: ")

# Set up data folder
now = datetime.now()
dt_string = now.strftime('-%m-%dT%H%M')
# Create folder under data folder
folder = 'data/' + data_name + dt_string
parent_dir = r"C:\Users\Lubin\Desktop\code\wattsonthemoon"
folder = os.path.join(parent_dir, folder)
os.mkdir(folder)

# Creating Dataframe to store data (32 things to record)
df = pd.DataFrame(columns=['Time', 'Source in Current (A)', 'Source in Voltage (V)',        # transmit side
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
                             


#################### User Input #########################
print(len(NASA_load_bank))
print(num_data_per_period)
print(time_sleep_period)
full_time = round((len(NASA_load_bank) * num_data_per_period * (6  + time_sleep_period))/60, 2)
print(f"This test will take {full_time} minutes to complete")
# User Input to start test
if charge_mode == True:
    print("##### CHARGE MODE IS ENABLED #####")
while True:
    start = input("Would you like to begin the test (yes/no)? ").lower()
    if start.startswith('y'):
        print("Experiment started")
        break
    elif start.startswith('n'):
        print("Experiment cancelled")
        quit()
    else:
        print("Invalid input. Please enter 'yes' or 'no'.")


#########################################################
#################### Main Loop ##########################
#########################################################
try:
    print("Starting experiment")
    # Sending hello to restart time out timer
    pi_load.check_connection()
    pi_source.check_connection()


    #################### Transmit System ####################
    print("Setting up transmit side")

    ctrl.CH2_turn_on()
    time.sleep(1)

    # Start power supply
    ctrl.PS_turn_on()

    # Turn on the ssr connected to the 120 line 
    pi_source.check_switch_high("ssr_120")
    
    # Check that SOURCE IN Voltage is 120V and Source in current is 0A
    pi_source.read_and_check_sensor("Source In Voltage")
    pi_source.read_and_check_sensor("Source In Current")

    time.sleep(5)

    # Read transmit bat voltage
    pi_source.read_and_check_sensor("Source Victron Voltage")

    # Turn on the bcm_lv_feed switch
    pi_source.check_switch_high("bcm_lv_feed")

    time.sleep(5)

    # Run the reverse start
    ctrl.CH1_check("turn on")
    time.sleep(2)
    ctrl.CH1_check("turn off")

    time.sleep(5)


    # Turn on the ssr connected to the 400 line 
    pi_source.check_switch_high("ssr_400")

    # Check if 400 Line voltage is above 330V
    pi_source.read_and_check_sensor("400 Line Voltage")

    time.sleep(5)

    #################### Load System ####################
    print("Setting up load side")

    # Turning on the HV line
    pi_load.check_switch_high("hv_line")

    
    time.sleep(5)

    # Activates BCM once there's high voltage
    pi_load.bcm_activate()

    #bcm check input and output voltage
    pi_load.read_and_check_sensor("BCM Voltage In")
    pi_load.read_and_check_sensor("BCM Voltage Out")


    # Turning on the BCM_LV_FEED switch
    pi_load.check_switch_high("bcm_lv_ssr")

    time.sleep(5)

    # Check that load victron works
    pi_load.read_and_check_sensor("Load Victron Voltage")

    # Turn on the Load SSR
    pi_load.check_switch_high("load_ssr")

    # Check load side voltage
    #pi_load.read_and_check_sensor("Load Side Voltage") # This is not working, commented out for now     


    #################### Data Collection ####################
    print("Setup Complete, all initial checks passed")
    print("Starting data collection")
    
    if charge_mode == False:
        ctrl.turn_on()

    #input__ = input("Press enter to start data collection")
    start_time = datetime.now()

    # Set up the plots
    plt.ion()  # Turn on interactive mode
    # Set style as five-thirty-eight
    plt.style.use('fivethirtyeight')
    fig, ax = plt.subplots(2, 3)  # Create a new figure and axis
    fig.set_size_inches(20, 10)

    # Set up the watchdog threads
    source_battery_watchdog = WatchDoginator(threshold_upper=source_cap, threshold_lower=3.2,sleep=15,value_adjust=13, name="Source Battery")
    load_battery_watchdog = WatchDoginator(threshold_upper=4.12, threshold_lower=3.2,sleep=15,value_adjust=7,  name="Load Battery")
    source_battery_watchdog.start()
    load_battery_watchdog.start()

    for count in range(len(NASA_load_bank)):
        print("Step: " + str(count))

        # Setting power to load
        ctrl.set_power(NASA_load_bank[count])

        # Setting Power Supply
        if NASA_power_state[count] == 1:
            ctrl.PS_turn_on()
            ctrl.PS_set_voltage(120)
        else: 
            if charge_mode == False:
                ctrl.PS_turn_off()
            #instr_power.set_voltage(28)

        # How many data points are collected per step.
        for data_count in range(num_data_per_period):
            time.sleep(time_sleep_period)
            if source_battery_watchdog.shutdown_requested == True or load_battery_watchdog.shutdown_requested == True:
                print("Shutdown requested, shutting down")
                raise Exception("Shutdown requested")
            #now = datetime.now()

            # Read ADCS on the source side
            adc_data_source = pi_source.decipher_adcs(pi_source.read_adcs())
            source_battery_watchdog.update_value(adc_data_source[4])
            # Read ADCS on the load side
            adc_data_load = pi_load.decipher_adcs(pi_load.read_adcs())
            load_battery_watchdog.update_value(adc_data_load[3])
            # Read BCM on the load side
            try:
                bcm_data_load = pi_load.decipher_bcm(pi_load.bcm_read())
            except:
                print("error reading bcm")
                bcm_data_load = [0,0,0,0]
                pass

            # Read power supply and load from Phoebe
            phoebe_data = ctrl.measure_all()

            # Read victrons from the transmit side
            try:
                victron_source = pi_source.read_victrons()
            except:
                print("error reading victron")
                victron_source = [0,0,0,0]
                pass

            # Read victrons from the load side
            try:
                victron_load = pi_load.read_victrons()
            except:
                print("error reading victron")
                victron_load = [0,0,0,0]
                pass
            
            # Get Time 
            now = datetime.now()
            # Convert time to hours
            time_elapsed = (now - start_time).total_seconds()/3600

            # Adding data to the dataframe
            df = df.append({"Time": time_elapsed*60, "Source in Current (A)": adc_data_source[0], "Source in Voltage (V)": adc_data_source[1], 
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
            print(f"Read {data_count} of {num_data_per_period} data points on step {count} of {len(NASA_load_bank)}")
            printer.print_tables(adc_data_source, adc_data_load, bcm_data_load, victron_source, victron_load, phoebe_data)
            print("\n")

            printer.print_graphs(df, ax, fig, full_time)
            





except BaseException as e:
    try:
        print(e)
    except:
        pass
    print("Error in main loop")
    print(traceback.format_exc())
    print("Experiment cancelled")

finally:
    print("Experiment finished")

    # Turning off switches on source side
    try:
        pi_source.ssr_120_off() 
        time.sleep(1)
        pi_source.bcm_lv_feed_off()
        time.sleep(1)
        pi_source.ssr_400_off()
        time.sleep(1)
    except:
        print("Error turning off source side switches")
        pass

    # Turning off switches on load side
    try:
        pi_load.hv_line_off()
        time.sleep(1)
        pi_load.bcm_lv_ssr_off()
        time.sleep(1)
        pi_load.load_ssr_off()
        time.sleep(1)
    except:
        print("Error turning off load side switches")
        pass

    # Turning off power supply
    try:
        ctrl.PS_turn_off()
    except:
        print("Error turning off power supply")
        pass

    # Turning off load
    try:
        ctrl.turn_off()
    except:
        print("Error turning off load")
        pass

    # Turning off SPD
    try:
        ctrl.CH1_check("turn off")
    except:
        print("Error turning off SPD")
        pass

    try:
        ctrl.CH2_turn_off()
    except:
        pass
    

    # Saving data
    # Saving data to excel sheet
    writer = pd.ExcelWriter(f"{folder}/{data_name}.xlsx", engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')

    # Auto-adjust columns' width
    for column in df:
        column_width = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        writer.sheets['Sheet1'].set_column(col_idx, col_idx, column_width)
    writer.save()

    plt.savefig(f"{folder}/{data_name}_1.png")
    printer.print_graphs(df, ax, fig, full_time, final=True)
    plt.savefig(f"{folder}/{data_name}_2.png")
    print("Data saved")
    try:
        source_battery_watchdog.shutdown_requested = True
        source_battery_watchdog.join()
        load_battery_watchdog.shutdown_requested = True
        load_battery_watchdog.join()
    except:
        print("Error joining watchdog threads")
        pass
    _iinput = input("Press enter to exit")
      
