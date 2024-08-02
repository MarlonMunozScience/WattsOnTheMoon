from tabulate import tabulate
from itertools import zip_longest
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import LogLocator, LogFormatter


# THIS CODE WILL STOP IT FROM STEALING FOCUS FROM THE MAIN WINDOW
# NEEDS TO BE TESTED: https://stackoverflow.com/questions/61397176/how-to-keep-matplotlib-from-stealing-focus
# matplotlib.use("Qt5agg")

# This class handles all of the plotting and printing of the data
# This is mainly for plots, the printing has been outsourced to the gpu
class printinator:
    def __init__(self):
        # Energy calculations need for power over time calculations
        self.energy_in = []
        self.energy_out = []

    # Prints the data in a table format, divided by transmit, load, and bk/equipment
    def print_tables(self, adc_data_source, adc_data_load, bcm_data_load, victron_source, victron_load, phoebe_data):
        data_TE = [
        ("Source in Voltage (V)", adc_data_source[1]),
        ("Source in Current (A)", adc_data_source[0]),
        ("TE Battery Voltage (V)", adc_data_source[4]),
        ("TE Volts per Cell (V)", adc_data_source[4]/13),
        ("TE Battery Current (A)", adc_data_source[5]),
        ("400 Line Voltage (V)", adc_data_source[6]),
        ("400 Line Current (A)", adc_data_source[7]),
        ("TE BCM LV IN Voltage (V)", adc_data_source[2]),
        ("TE BCM LV IN Current (A)", adc_data_source[3]),
        ("TE Victron Voltage (V)", victron_source[0]),
        ("TE Victron Current (A)", victron_source[1]),
        ("TE Victron VPV (V)", victron_source[2]),
        ("TE Victron WPV (W)", victron_source[3]),
    ]

        data_LE = [
        ("LE Load Voltage (V)", adc_data_load[1]),
        ("LE Load Current (A)", adc_data_load[0]),
        ("LE Battery Voltage (V)", adc_data_load[3]),
        ("LE Volts per Cell (V)", adc_data_load[3]/7), 
        ("LE Battery Current (A)", adc_data_load[2]),
        ("LE BCM Voltage In (V)", bcm_data_load[0]),
        ("LE BCM Current In (A)", bcm_data_load[2]),
        ("LE BCM Voltage Out (V)", bcm_data_load[1]),
        ("LE BCM Current Out (A)", bcm_data_load[3]),
        ("LE Victron Voltage (V)", victron_load[0]),
        ("LE Victron Current (A)", victron_load[1]),
        ("LE Victron VPV (V)", victron_load[2]),
        ("LE Victron WPV (W)", victron_load[3]),
    ]

        data_bk = [
        ("BK Load Voltage (V)", phoebe_data[0]),
        ("BK Load Current (A)", phoebe_data[1]),
        ("BK Load Power (W)", phoebe_data[2]),
        ("PS Voltage (V)", phoebe_data[3]),
        ("PS Current (A)", phoebe_data[4]),
        ("PS Power (W)", phoebe_data[5]),
    ]
        # Create plain text tables
        table_TE = tabulate(data_TE, headers =["Transmit Side", "Value"], tablefmt="plain", floatfmt=".2f")
        table_LE = tabulate(data_LE, headers=["Load Side", "Value"], tablefmt="plain", floatfmt=".2f")
        table_bk = tabulate(data_bk, headers=["BK Instrument", "Value"], tablefmt="plain", floatfmt=".2f")

        # Split tables into lines
        table_TE_lines = table_TE.split("\n")
        table_LE_lines = table_LE.split("\n")
        table_bk_lines = table_bk.split("\n")

        # Calculate maximum line lengths for each table
        max_len_TE = max(len(line) for line in table_TE_lines)
        max_len_LE = max(len(line) for line in table_LE_lines)
        max_len_bk = max(len(line) for line in table_bk_lines)

        # Print tables side by side with spaces in between
        for line_TE, line_LE, line_bk in zip_longest(table_TE_lines, table_LE_lines, table_bk_lines):
            print(f"{line_TE:<{max_len_TE + 4}}{line_LE:<{max_len_LE + 4}}{line_bk}")

    # This calculates the power over time for the energy in and the energy out so that it could be plotted
    def calc_energy(self, voltage, current, time, list, final):
        # Create a dictionary to access each dictionary 
        dict = {
            "energy in": self.energy_in,
            "energy out": self.energy_out
        }
        list = dict[list]
        if len(list) == 0:
            list.append(0)
        else:
            if final == True:
                current_index = len(list) - 1
                previous_value = list[current_index - 1]
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

    # This calculates the strings that is printed at the top of the plot (updated in real time)
    def calc_strings(self, df, full_time):
        lenn = len(df["Time"]) - 1
        power_in = round(df['Source in Voltage (V)'][lenn] * df['Source in Current (A)'][lenn], 2)
        power_out = round( df['BK Load Power (W)'][lenn], 2)
        time_elapsed = round(df['Time'][lenn], 1)

        power_400 = round(-1* df['400 Line Voltage (V)'][lenn] * df['400 Line Current (A)'][lenn], 2)
        bcm_power_in = round(df["BCM Voltage In (V)"][lenn] * df["BCM Current In (A)"][lenn], 2)
        source_batt = round(df['Transmit Battery Voltage (V)'][lenn], 2)
        load_batt = round(df['Load Battery Voltage (V)'][lenn], 2)
        load_batt_per_cell = round(load_batt/7, 2)
        source_batt_per_cell = round(source_batt/13, 2)

        string1 = f'Watts on on the Moon {full_time} min test Full Profile Data \n'
        string2 = f'Power in: {power_in} W | Power out: {power_out} W | 400 Line Power: {power_400} W | Line Loss: {round(power_400 - bcm_power_in, 2)} W | Time Elapsed: {time_elapsed} mins \n'
        string3 = f'Source Battery: {source_batt} V | Load Battery: {load_batt} V | Load Battery per cell: {load_batt_per_cell} V | Source Battery per cell: {source_batt_per_cell} V'
        return string1 + string2 + string3

    # This calculates the initial energy of the battery based on the voltage and the battery type
    def add_initial_energy(self, voltage, batt):
        dict = {"Source": [1440, 13], "Load": [720, 7]}
        capacity = dict[batt][0]
        num_cells = dict[batt][1]
        starting_v_per_cell = voltage[0] / num_cells
        starting_capacity = capacity * (starting_v_per_cell -3.2) / 0.9
        #print(starting_capacity)
        return starting_capacity

    # This calculates the battery capacity over time based on the voltage and current
    def psuedo_calc_batt(self, voltage, current, time, inital_energy, batt):
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

    #$ This plots the data in real time
    # Essentially, it clears the plot, then plots the data, then redraws the plot
    def print_graphs(self, df, ax, fig, full_time, final=False):
        

        # Plot 1: Full Profile
        if final == True:
            fig.suptitle(f'Watts on on the Moon {full_time} min test Full Profile Data \n', fontsize=16)
        else:
            fig.suptitle(self.calc_strings(df, full_time), fontsize=16)

        
        fig.subplots_adjust(left=0.08, right=.97, bottom=0.05, top=0.9, wspace=0.25, hspace=0.25)

        # Calculating energies
        ax[0, 0].clear()


        ax[0, 0].plot(df["Time"], np.multiply(df["Transmit Battery Voltage (V)"], df["Transmit Battery Current (A)"]), label="Source Bat Power Input (w)", color="blue", )  # Plot the updated data
        ax[0, 0].plot(df["Time"], np.multiply(df['Load Battery Voltage (V)'], df["Load Battery Current (A)"]), label="Load Bat Power Input (w)", color="red")  # Plot the updated data
        # Convert this: .plot(bk_load_power_1, label="Load Power Output (w)", color="cyan")
        ax[0, 0].plot(df["Time"], df['BK Load Power (W)'], label="BK Load Power Output (w)", color="cyan")  # Plot the updated data
        ax[0, 0].plot(df["Time"], df['PS Power (W)'], label="BK Power Supply Output (w)", color="purple")  # Plot the updated data
        ax[0, 0].set_xlabel('Time (Min)')  # Set the x-axis label
        ax[0, 0].set_ylabel('Power (W)')  # Set the y-axis label
        ax[0, 0].set_title('Power Profile')  # Set the title
        ax[0, 0].grid(True, color='gray', linestyle='--', linewidth=0.5)

        ax[0, 0].legend() # Add a legend

        # Plot 2: Battery voltages
        ax[0, 1].clear()
        ax[0, 1].plot(df["Time"], df["Transmit Battery Voltage (V)"], label="Source Battery Voltage (V)", color="blue")  # Plot the updated data
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
        ax[1, 1].plot(df["Time"], np.multiply(df['BCM Voltage Out (V)'], df['BCM Current Out (A)']), label="BCM Power Out", color="green")  # Plot the updated data
        ax[1, 1].set_xlabel('Time (Min)')  # Set the x-axis label
        ax[1, 1].set_ylabel('Power (W)')  # Set the y-axis label
        ax[1, 1].set_title('Power Out Load Side')  # Set the title
        ax[1, 1].legend()  # Add a legend
        ax[1, 1].grid(True, color='gray', linestyle='--', linewidth=0.5)

        # Plot 5: Energy in and out
        ax[1, 2].clear()

        # Run calculations for energy in and out
        if final == False:
            self.calc_energy(df["Source in Voltage (V)"], df["Source in Current (A)"], df["Time"], "energy in", final)
            self.calc_energy(df['BK Load Voltage (V)'], df['Load Side Current (A)'], df["Time"], "energy out", final)
        ax[1, 2].plot(df["Time"], self.energy_in, label="Energy In", color="blue", linestyle="dashed")  # Plot the updated data
        ax[1, 2].plot(df["Time"], self.energy_out, label="Energy Out", color="red")  # Plot the updated data
        ax[1, 2].set_xlabel('Time (Min)')  # Set the x-axis label
        ax[1, 2].set_ylabel('Energy (W-Hr)')  # Set the y-axis label
        ax[1, 2].set_title('Energy In and Out')  # Set the title
        ax[1, 2].legend()  # Add a legend
        ax[1, 2].grid(True, color='gray', linestyle='--', linewidth=0.5)

        # Plot 6: Voltage per cell
        ax[0, 2].clear()
        ax[0, 2].plot(df["Time"], df["Transmit Battery Voltage (V)"]/13, label="Source Battery Voltage (V)", color="blue")  # TE has 13 cells
        ax[0, 2].plot(df["Time"], df['Load Battery Voltage (V)']/7, label="Load Battery Voltage (V)", color="red")  # LE has 7 cells
        ax[0, 2].set_xlabel('Time (Min)')  # Set the x-axis label
        ax[0, 2].set_ylabel('Voltage (V) per cell')  # Set the y-axis label
        ax[0, 2].set_title('Voltage per Cell')  # Set the title
        ax[0, 2].legend()  # Add a legend
        ax[0, 2].grid(True, color='gray', linestyle='--', linewidth=0.5)


        plt.draw()  # Redraw the plot

        fig.canvas.draw()
        fig.canvas.flush_events()
        

        plt.pause(0.01)  # Pause for a short period to allow the plot to update
