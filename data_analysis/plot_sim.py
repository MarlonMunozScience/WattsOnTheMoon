import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import datetime
from tabulate import tabulate
from itertools import zip_longest
from matplotlib.ticker import LogLocator, LogFormatter

print("We made it")
def calc_strings(df, full_time):
        lenn = len(df["Time"]) - 1
        power_in = round(df['Source in Voltage (V)'][lenn] * df['Source in Current (A)'][lenn], 2)
        power_out = round( df['BK Load Power (W)'][lenn], 2)
        time_elapsed = round(df['Time'][lenn], 1)

        power_400 = round(df['400 Line Voltage (V)'][lenn] * df['400 Line Current (A)'][lenn], 2)
        source_batt = round(df['Transmit Battery Voltage (V)'][lenn], 2)
        load_batt = round(df['BK Load Voltage (V)'][lenn], 2)
        load_batt_per_cell = round(load_batt/7, 2)
        source_batt_per_cell = round(source_batt/13, 2)

        string1 = f'Watts on on the Moon {full_time} min test Full Profile Data - Initial SOC = 75%\n'
        string2 = f'Power in: {power_in} W | Power out: {power_out} | 400 Line Power: {power_400} W | Time Elapsed: {time_elapsed} mins \n'
        string3 = f'Source Battery: {source_batt} V | Load Battery: {load_batt} V | Load Battery per cell: {load_batt_per_cell} V | Source Battery per cell: {source_batt_per_cell} V'
        return string1, string2, string3



file_path = 'C:/Users/Lubin/Desktop/code/wattsonthemoon/data/three_hour_test_1-04-21T1402/three_hour_test_1.xlsx'
df = pd.read_excel(file_path, sheet_name='Sheet1')
plt.ion()  # Turn on interactive mode
# Set style as five-thirty-eight
plt.style.use('fivethirtyeight')
fig, ax = plt.subplots(2, 3)  # Create a new figure and axis
fig.set_size_inches(24, 12)

full_time = 180
"""
lenn = len(df['Time']) - 1
power_in = round(df['Source in Voltage (V)'][lenn] * df['Source in Current (A)'][lenn], 2)
power_out = round( df['BK Load Power (W)'][lenn], 2)
time_elapsed = round(df['Time'][lenn], 1)

power_400 = round(df['400 Line Voltage (V)'][lenn] * df['400 Line Current (A)'][lenn], 2)
source_batt = round(df['Transmit Battery Voltage (V)'][lenn], 2)
load_batt = round(df['BK Load Voltage (V)'][lenn], 2)
load_batt_per_cell = round(load_batt/7, 2)
source_batt_per_cell = round(source_batt/13, 2)

string1 = f'Watts on on the Moon {full_time} min test Full Profile Data \n'
string2 = f'Power in: {power_in} W | Power out: {power_out} | 400 Line Power: {power_400} W | Time Elapsed: {time_elapsed} mins \n'
string3 = f'Source Battery: {source_batt} V | Load Battery: {load_batt} V | Load Battery per cell: {load_batt_per_cell} V | Source Battery per cell: {source_batt_per_cell} V'
fig.suptitle(string1 + string2 + string3, fontsize=16)"""

# Remove zeros from the data
bcm_power_out = np.multiply(df['BCM Voltage Out (V)'], df['BCM Current Out (A)'])
bcm_power_out.replace(0, np.nan, inplace=True)
bcm_power_out.interpolate(inplace=True)
bcm_power_out = bcm_power_out.to_numpy()
# reformat from shape (2222, ) to (2222, 1)
bcm_power_out = np.reshape(bcm_power_out, (bcm_power_out.shape[0], 1))


str1, str2, str3 = calc_strings(df, full_time)
fig.suptitle(str1, fontsize=32)
ax[0, 0].clear()
# Calculating energies
def calc_energy( voltage, current, time, list):
    # Create a dictionary to access each dictionary 
    dict = {
        "energy in": energy_in,
        "energy out": energy_out
    }
    list = dict[list]
    if len(list) == 0:
        list.append(0)
    else:
        current_index = len(list)
        previous_value = list[current_index - 1]
        h = (time[current_index] - time[current_index - 1])/60
        if current_index % 2 == 0:
            val = (h/3) * 4 * (voltage[current_index] * current[current_index])
            val = val + previous_value
            list.append(val)
        else:
            val = (h/3) * 2 * (voltage[current_index] * current[current_index])
            val = val + previous_value
            list.append(val)


def psuedo_calc(voltage, current, time):
    list = []
    dummy_val  = 0
    for i in range(len(voltage)):
        if i == 0:
            list.append(0)
        else:
            h = (time[i] - time[i-1]) /(60) # Gets the time difference in hours
            if i % 2 == 0:
                val = (h/3) *4 * voltage[i] * current[i] 
                val = val + dummy_val # append it
                dummy_val = val # Stores the previous value
                list.append(val)
            else:
                val = (h/3) *2 * voltage[i] * current[i] 
                val = val + dummy_val
                dummy_val = val
                list.append(val)
    #print(list)
    return list

def add_initial_energy(voltage, batt):
    dict = {"Source": [1440, 13], "Load": [720, 7]}
    capacity = dict[batt][0]
    num_cells = dict[batt][1]
    starting_v_per_cell = voltage[0] / num_cells
    starting_capacity = capacity * (starting_v_per_cell -3.2) / 0.9
    #print(starting_capacity)
    return starting_capacity

def psuedo_calc_batt(voltage, current, time, inital_energy, batt):
    dict = {"Source": [1440], "Load": [720]}
    capacity = dict[batt][0]
    list = []
    dummy_val  = 0
    for i in range(len(voltage)):
        if i == 0:
            list.append(inital_energy)
            dummy_val = inital_energy
        else:
            h = (time[i] - time[i-1]) /(60) # Gets the time difference in hours
            if i % 2 == 0:
                val = (h/3) *4 * voltage[i] * current[i] 
                # Convert from array to float
                
                val = val + dummy_val # append it
                val = val + 0
                if val > capacity:
                    val = capacity
                
                dummy_val = val # Stores the previous value
                list.append(val)
            else:
                val = (h/3) *2 * voltage[i] * current[i]
                val = val + dummy_val
                if val > capacity:
                    val = capacity
                dummy_val = val
                list.append(val)
    #print(list)
    return list

ax[0, 0].set_yscale('log')
fig.subplots_adjust(left=0.08, right=.97, bottom=0.05, top=0.9, wspace=0.25, hspace=0.25)


# Customize y-axis ticks using LogLocator and LogFormatter
log_locator = LogLocator(base=10, subs=[1, 2, 3, 4, 5, 6, 7, 8, 9])
log_formatter = LogFormatter(base=10)
ax[0, 0].yaxis.set_major_locator(log_locator)
ax[0, 0].yaxis.set_major_formatter(log_formatter)
ax[0, 0].set_yticks([600, 0.8*10**3, 1000, 1200, 1400, 1600])
ax[0, 0].set_yticklabels([600, 800, 1000, 1200, 1400, 1600])

list = psuedo_calc_batt(df['Transmit Battery Voltage (V)'], df["Transmit Battery Current (A)"], df["Time"], add_initial_energy(df['Transmit Battery Voltage (V)'], "Source"), "Source")
line1, = ax[0, 0].plot(df["Time"], list, label="Source Bat Energy (W-Hr)", color="blue"
)
list = psuedo_calc_batt(df["Load Battery Voltage (V)"], df["Load Battery Current (A)"], df["Time"], add_initial_energy(df["Load Battery Voltage (V)"], "Load"), "Load")

line2, = ax[0, 0].plot(df["Time"], list, label="Load Bat Energy (W-Hr)", color="red")
ax[0, 0].set_ylim([500, 1700])
ax[0, 0].set_ylabel("Energy (W-Hr)")
#ax[0, 0].grid(False)
"""
ax2 = ax[0, 0].twinx()
line3, = ax2.plot(df["Time"], np.multiply(df["Transmit Battery Voltage (V)"], df["Transmit Battery Current (A)"]), label="Source Bat Power Input (w)", color="blue", linestyle="dashed")  # Plot the updated data
line4, =ax2.plot(df["Time"], np.multiply(df['Load Battery Voltage (V)'], df["Load Battery Current (A)"]), label="Load Bat Power Input (w)", color="blue")  # Plot the updated data
# Convert this: .plot(bk_load_power_1, label="Load Power Output (w)", color="cyan")
line5, = ax2.plot(df["Time"], df['BK Load Power (W)'], label="BK Load Power Output (w)", color="cyan")  # Plot the updated data
line6, = ax2.plot(df["Time"], df['PS Power (W)'], label="BK Power Supply Output (w)", color="purple")  # Plot the updated data
ax2.set_xlabel('Time (Min)')  # Set the x-axis label
ax2.set_ylabel('Power (W)')  # Set the y-axis label
ax2.set_title('Power Profile')  # Set the title
ax2.grid(True, color='gray', linestyle='--', linewidth=0.5)
"""
lines = [ line1, line2]
labels = [l.get_label() for l in lines]
ax[0, 0].legend(lines, labels, loc="lower left", prop={'size': 8} )  # Add a legend

# To Delete Later
ax[0, 0].set_title('Energy Profile')  # Set the title
ax[0, 0].set_xlabel('Time (Min)')  # Set the x-axis label

#ax2.legend(lines, labels, loc="lower left", prop={'size': 8} )  # Add a legend

# Plot 2: Battery voltages
ax[0, 1].clear()
ax[0, 1].plot(df["Time"], df["Transmit Battery Voltage (V)"], label="Source Battery Voltage (V)", color="blue", linestyle="dashed")  # Plot the updated data
ax[0, 1].plot(df["Time"], df['Load Battery Voltage (V)'], label="Load Battery Voltage (V)", color="red")  # Plot the updated data
ax[0, 1].set_xlabel('Time (Min)')  # Set the x-axis label
ax[0, 1].set_ylabel('Voltage (V)')  # Set the y-axis label
ax[0, 1].set_title('Battery Voltages')  # Set the title
ax[0, 1].legend()  # Add a legend
ax[0, 1].grid(True, color='gray', linestyle='--', linewidth=0.5)


# Plot 3: Power in (source side)
ax[1, 0].clear()
ax[1, 0].plot(df["Time"], np.multiply(df["Source in Voltage (V)"], df["Source in Current (A)"]), label="Source Power Input (w)", color="blue", linestyle="dashed")  # Plot the updated data
ax[1, 0].plot(df["Time"], np.multiply(df["Transmit Battery Voltage (V)"], df["Transmit Battery Current (A)"]), label="Transmit battery power", color="red")  # Plot the updated data
ax[1, 0].plot(df["Time"], np.multiply(df["400 Line Voltage (V)"], -1 * df["400 Line Current (A)"]), label="400V Line Power", color="green")  # Plot the updated data
ax[1, 0].set_xlabel('Time (Min)')  # Set the x-axis label
ax[1, 0].set_ylabel('Power (W)')  # Set the y-axis label
ax[1, 0].set_title('Power In Source Side')  # Set the title
ax[1, 0].legend()  # Add a legend
ax[1, 0].grid(True, color='gray', linestyle='--', linewidth=0.5)

# Plot 4: Power out (load side)
ax[1, 1].clear() # TODO: Replace BK Load Voltage with Load Voltage when fixed
ax[1, 1].plot(df["Time"], np.multiply(df['BK Load Voltage (V)'], df['Load Side Current (A)']), label="Load Side Power Output (w)", color="blue", linestyle="dashed")  # Plot the updated data
ax[1, 1].plot(df["Time"], np.multiply(df['Load Battery Voltage (V)'], df["Load Battery Current (A)"]), label="Load battery power", color="red")  # Plot the updated data
ax[1, 1].plot(df["Time"], bcm_power_out, label="BCM Power Out", color="green")  # Plot the updated data
ax[1, 1].set_xlabel('Time (Min)')  # Set the x-axis label
ax[1, 1].set_ylabel('Power (W)')  # Set the y-axis label
ax[1, 1].set_title('Power Out Load Side')  # Set the title
ax[1, 1].legend()  # Add a legend
ax[1, 1].grid(True, color='gray', linestyle='--', linewidth=0.5)

# Plot 5: Energy in and out
ax[1, 2].clear()

# Run calculations for energy in and out
#calc_energy(df["Source in Voltage (V)"], df["Source in Current (A)"], df["Time"], "energy in")
#calc_energy(df['BK Load Voltage (V)'], df['Load Side Current (A)'], df["Time"], "energy out")
energy_in = psuedo_calc(df["Source in Voltage (V)"], df["Source in Current (A)"], df["Time"] )
energy_out = psuedo_calc(df['BK Load Voltage (V)'], df['Load Side Current (A)'], df["Time"])
ax[1, 2].plot(df["Time"], energy_in, label="Energy In", color="blue", linestyle="dashed")  # Plot the updated data
ax[1, 2].plot(df["Time"], energy_out, label="Energy Out", color="red")  # Plot the updated data
ax[1, 2].set_xlabel('Time (Min)')  # Set the x-axis label
ax[1, 2].set_ylabel('Energy (W-Hr)')  # Set the y-axis label
ax[1, 2].set_title('Energy In and Out')  # Set the title
ax[1, 2].legend()  # Add a legend
ax[1, 2].grid(True, color='gray', linestyle='--', linewidth=0.5)

# Plot 6: Voltage per cell
ax[0, 2].clear()
ax[0, 2].plot(df["Time"], df["Transmit Battery Voltage (V)"]/13, label="Source Battery Voltage (V)", color="blue", linestyle="dashed")  # TE has 13 cells
ax[0, 2].plot(df["Time"], df['Load Battery Voltage (V)']/7, label="Load Battery Voltage (V)", color="red")  # LE has 7 cells
ax[0, 2].set_xlabel('Time (Min)')  # Set the x-axis label
ax[0, 2].set_ylabel('Voltage (V) per cell')  # Set the y-axis label
ax[0, 2].set_title('Voltage per Cell')  # Set the title
ax[0, 2].legend()  # Add a legend
ax[0, 2].grid(True, color='gray', linestyle='--', linewidth=0.5)


plt.draw()  # Redraw the plot
plt.pause(0.01)  # Pause for a short period to allow the plot to update
input__ = input("Press enter to continue...")  # Wait for user input to continue