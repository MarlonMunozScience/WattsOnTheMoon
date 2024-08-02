# This Python file uses the following encoding: utf-8
"""
This file contains the main window class for the GUI. It also contains the main function for running the GUI. Run this to run the GUI.
"""
# THIS CODE WILL STOP IT FROM STEALING FOCUS FROM THE MAIN WINDOW
# NEEDS TO BE TESTED: https://stackoverflow.com/questions/61397176/how-to-keep-matplotlib-from-stealing-focus
# matplotlib.use("Qt5agg")
# PLACE IN plotsnprints.py

import logging
import sys
import json
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTableWidgetItem, QTableWidget 
from PyQt6.QtCore import QObject, QThread, pyqtSignal, QTimer, Qt
from PyQt6 import uic
import threading
import traceback
import matplotlib.pyplot as plt
import pandas as pd
import time
from PyQt6 import QtTest

from System_Scripts.ssh_scripts.ssh_connection import ssh_connect, SSHManager
from System_Scripts.plotsnprints import printinator
from wotm import wotm_controller

from ui_form import Ui_MainWindow

# Class used for rerouting Standard Output of the console to the GUI
class Stream(QtCore.QObject):
    newText = QtCore.pyqtSignal(str)

    def write(self, text):
        self.newText.emit(str(text))
        #print(traceback.format_exc())

class CustomDialog(QtWidgets.QDialog):
    """
    A custom dialog box for confirming a test start. This runs when the user clicks the "Start Test" button.

    """

    def __init__(self, fulltime, flags):
        """
        Initializes the CustomDialog object.

        Args:
            fulltime (float): The estimated time in minutes for the test to complete.
            flags (Flags): A Flags object containing various flags for the test.

        Returns:
            None.
        """

        super().__init__()

        # Code for the dialog box goes here
        # Setting the window title
        self.setWindowTitle("HOLY SHIT!")

        # Creating a button box with OK and Cancel buttons
        QBtn = QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel
        print(type(QBtn))  # Print the type of the button box (for debugging purposes)
        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)  # Create the button box
        self.buttonBox.accepted.connect(self.accept)  # Connect the OK button to the accept() method
        self.buttonBox.rejected.connect(self.reject)  # Connect the Cancel button to the reject() method

        # Creating a vertical layout for the dialog box
        self.layout = QtWidgets.QVBoxLayout()
        message = QtWidgets.QLabel("Are you sure you want to start the test?")  # Create a label for the message
        message2 = QtWidgets.QLabel(f"Test will take {fulltime} minutes to complete")  # Create a label for the estimated time
        self.layout.addWidget(message)  # Add the message label to the layout
        self.layout.addWidget(message2)  # Add the estimated time label to the layout

        # Checking if the test title has been changed in the main GUI
        if flags.changed_title == False:
            message3 = QtWidgets.QLabel("CAUTION: Remember to rename the test")  # Create a label for the caution message
            self.layout.addWidget(message3)  # Add the caution message label to the layout

        self.layout.addWidget(self.buttonBox)  # Add the button box to the layout
        self.setLayout(self.layout)  # Set the layout for the dialog box

# Updates table in the main GUI as the test is running
class TableUpdateWidget(QTableWidget ):
    def __init__(self, ui, df):
        super().__init__()
        self.ui = ui
        self.df = df
        self.data_list = [[
            ("Source in Voltage (V)", 0),
            ("Source in Current (A)", 0),
            ("TE Battery Voltage (V)", 0),
            ("TE Volts per Cell (V)", 0),
            ("TE Battery Current (A)", 0),
            ("400 Line Voltage (V)", 0),
            ("400 Line Current (A)", 0),
            ("TE BCM LV IN Voltage (V)", 0),
            ("TE BCM LV IN Current (A)", 0),
            ("TE Victron Voltage (V)", 0),
            ("TE Victron Current (A)", 0),
            ("TE Victron VPV (V)", 0),
            ("TE Victron WPV (W)", 0)],[
            ("LE Load Voltage (V)", 0),
            ("LE Load Current (A)", 0),
            ("LE Battery Voltage (V)", 0),
            ("LE Volts per Cell (V)", 0),
            ("LE Battery Current (A)", 0),
            ("LE BCM Voltage In (V)", 0),
            ("LE BCM Current In (A)", 0),
            ("LE BCM Voltage Out (V)", 0),
            ("LE BCM Current Out (A)", 0),
            ("LE Victron Voltage (V)", 0),
            ("LE Victron Current (A)", 0),
            ("LE Victron VPV (V)", 0),
            ("LE Victron WPV (W)", 0)], [
            ("BK Load Voltage (V)", 0),
            ("BK Load Current (A)", 0),
            ("BK Load Power (W)", 0),
            ("PS Voltage (V)", 0),
            ("PS Current (A)", 0),
            ("PS Power (W)", 0)
            ]]

        # Timer to update table
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_table)
        self.data_table = self.ui.data_table
        self.setup()
        self.timer.start(2000)  # Update every 2 seconds

        # Set table to stretch
        self.data_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.data_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.data_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.data_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

        self.data_table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.data_table.verticalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)

    # Ran on startup
    def setup(self):
        self.data_table.setRowCount(len(self.data_list[0]))
        self.data_table.setColumnCount(6)

        for i, (label, value) in enumerate(self.data_list[0]):
            item1 = QTableWidgetItem()
            item2 = QTableWidgetItem()
            item1.setData(0, label)
            item2.setData(0, str(value))
            self.data_table.setItem(i, 0, item1)
            self.data_table.setItem(i, 1, item2)
        
        for i, (label, value) in enumerate(self.data_list[1]):
            self.data_table.setItem(i, 2, QTableWidgetItem(label))
            self.data_table.setItem(i, 3, QTableWidgetItem(str(value)))  

        for i, (label, value) in enumerate(self.data_list[2]):
            self.data_table.setItem(i, 4, QTableWidgetItem(label))
            self.data_table.setItem(i, 5, QTableWidgetItem(str(value)))


    def update_table(self, init = False):
        #print("##### Updating table ####")
        
        #self.ui.data_table.setRowCount(len(self.data_list[0]))
        #self.ui.data_table.setColumnCount(6)
        #self.ui.data_table.setHorizontalHeaderLabels(self.df.columns)

        self.data_table.setRowCount(len(self.data_list[0]))
        self.data_table.setColumnCount(6)

        for i, (label, value) in enumerate(self.data_list[0]):
            item1 = QTableWidgetItem()
            item2 = QTableWidgetItem()
            item1.setData(0, label)
            item2.setData(0, str(value))
            self.data_table.setItem(i, 0, item1)
            self.data_table.setItem(i, 1, item2)
        
        for i, (label, value) in enumerate(self.data_list[1]):
            self.data_table.setItem(i, 2, QTableWidgetItem(label))
            self.data_table.setItem(i, 3, QTableWidgetItem(str(value)))  

        for i, (label, value) in enumerate(self.data_list[2]):
            self.data_table.setItem(i, 4, QTableWidgetItem(label))
            self.data_table.setItem(i, 5, QTableWidgetItem(str(value)))

class flag_manager:
    """
    Class to manage the flags for the program. This is used to determine when all the shh and sockets connections are successful. 
    Flags are set to true when the user presses the appropriate button and the connection is successful.
    All flags are check to be true when the user presses the "start" button. If not, the user is alerted and the program does not start.
    """
    def __init__(self):
        self.changed_title = False
        self.phoebe_ssh = False
        self.phoebe_socket = False
        self.source_ssh = False
        self.source_socket = False
        self.load_ssh = False
        self.load_socket = False

    def check_all(self):
        return self.phoebe_ssh and self.phoebe_socket and self.source_ssh and self.source_socket and self.load_ssh and self.load_socket


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        # Initial parameters
        self.meas = 1
        self.sleep = .1
        self.title = "test"

        # Create the flag manager for ssh and socket connections
        self.flags = flag_manager()

        self.df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})

        super().__init__(*args, **kwargs)
        self.ui = uic.loadUi("mainwindow.ui", self)
        self.queue = []
        self.controller = wotm_controller()
        # Load the UI Page

        # Import the json file containing the configuration (Used for IP addresses and ports)
        self.config = json.load(open("config.json"))

        # Create the SSH Manager (/System_Scripts/ssh_scripts)
        self.ssh_manager = SSHManager()

        ##### Phoebe #####
        # Phoebe SSH Connection Button
        self.phoebe_connect = self.ui.phoebe_connect
        self.phoebe_connect.clicked.connect(self.phoebe_add_connection)

        # Phoebe Socket Connection Button
        self.phoebe_hello = self.ui.phoebe_hello
        self.phoebe_hello.clicked.connect(self.phoebe_socket_connection)
        self.phoebe_hello.setEnabled(False)

        # Phoebe Send ctrl c Button
        self.phoebe_ctrlc = self.ui.phoebe_ctrlc
        self.phoebe_ctrlc.clicked.connect(self.phoebe_send_ctrlc)


        ##### Load #####
        # Load SSH Connection Button
        self.load_connect = self.ui.load_connect
        self.load_connect.clicked.connect(self.load_add_connection)

        # Load Socket Connection Button
        self.load_hello = self.ui.load_hello
        self.load_hello.clicked.connect(self.load_socket_connection)
        self.load_hello.setEnabled(False)

        # Load Send ctrl c Button
        self.load_ctrlc = self.ui.load_ctrlc
        self.load_ctrlc.clicked.connect(self.load_send_ctrlc)

        ##### Source #####

        # Source SSH Connection Button
        self.source_connect = self.ui.source_connect
        self.source_connect.clicked.connect(self.source_add_connection)

        # Source Socket Connection Button
        self.source_hello = self.ui.source_hello
        self.source_hello.clicked.connect(self.source_socket_connection)
        self.source_hello.setEnabled(False)

        # Source Send ctrl c Button
        self.source_ctrlc = self.ui.source_ctrlc
        self.source_ctrlc.clicked.connect(self.source_send_ctrlc)

        # Start Test Button
        self.start_test = self.ui.start_test
        self.start_test.clicked.connect(self.create_popup)
        self.start_test.setStyleSheet('QPushButton {background-color: green; color: white;}')

        # Stop Test Button
        self.stop_test = self.ui.stop_test
        self.stop_test.clicked.connect(self.interrupt_test)
        self.stop_test.setStyleSheet('QPushButton {background-color: red; color: white;}')

        # Charge Mode Checkbox
        self.charge_mode = self.ui.charge_mode
        self.charge_mode.setChecked(False)

        # Measurement per Step QLineedit
        self.measurement_input = self.ui.measurement_input
        self.measurement_input.setText("1")
        self.measurement_input.textChanged.connect(self.measurement_input_changed)

        # Title Input QLineedit
        self.title_input = self.ui.title_input
        self.title_input.setText("title :3")
        self.title_input.textChanged.connect(self.title_input_changed)

        # Terminal output text box
        self.terminal = self.ui.terminal
        sys.stdout = Stream(newText=self.append_to_terminal)

        # SSH Terminal Output text box
        self.ssh_output = self.ui.ssh_output

        # Create a new thread to always read the ssh output
        self.thread_ssh = threading.Thread(target=self.ssh_manager.read_output, args=(self.ssh_output,))
        self.thread_ssh.start()
        
        # Initializing print class
        self.printer = printinator()

        # Data table
        # This code resizes the table to fit any aspect ratio we decide to use  
        self.data_table = TableUpdateWidget(self.ui, self.df) 
        time.sleep(1)

        # Prints the welcome message
        self.welcome()

        # Logging
        f = open("gui-log" + "/log.txt", "w")
        f.write("Log file for WOTM experiment\n")
        f.close()
        
        logging.basicConfig(filename=("gui-log/log.txt"), encoding='utf-8', level=logging.DEBUG)
        print("Data folder created")
        logging.debug("Data folder created")


    def welcome(self):
        print("Welcome to the WOTM GUI \n")
        print("Please connect to the SSH servers first\n")
        print("Then connect to the sockets\n")
        print("Then you can run the test using the start button\n")
        print("If you want to stop the test, press the stop button\n")
        print("If you want to change the number of measurements per step, change the number in the box\n")
        print("Remember to change the title of the test in the box\n")
        print("If there are any errors with the SSH connection, make sure the computer/pi are turned on\n")
        print("If there are any errors with the socket connection, make sure the WOTM devices are turned on\n")



    # Code used for formatting console output to the GUI
    def append_to_terminal(self, text):
        cursor = self.terminal.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.terminal.setTextCursor(cursor)


    # Code used for creating the popup window. User must accept to start the test
    def create_popup(self, s):
        logging.debug("Create popup called")

        # Checking all flags are true from flag manager
        if self.flags.check_all() != True:
            logging.debug("Not all flags are true")
            print("ERROR: Make sure all connections are established")
            return
        
        # Runs the setup function in the WOTM algorithm
        self.run_setup()
        print("click", s)
        print("Measurement Input changed to", self.meas)

        # Calculates the time the test will take
        self.fulltime =  round((101 * int(self.meas)* 6.1)/60, 2)

        # Creates the popup window
        dlg = CustomDialog(self.fulltime, self.flags)

        # if the user accepts, the test will start
        if dlg.exec():
            print("Running Test!")
            self.run_main()
        else:
            print("Cancel!")

    # prints to console everytime the measurement input is changed
    # Also changes the variable everytime the input is changed
    def measurement_input_changed(self, s):
        if s != "":
            print(f"Test will take {round((101 * int(s)* 6.1)/60, 2)} minutes")
        self.meas = s

    # Changes the variable everytime the input is changed
    def title_input_changed(self, s):
        #print(f"Title Input changed to {s}")
        self.title = s
        self.flags.changed_title = True
    
    ###### Phoebe Functions ######
    def phoebe_add_connection(self):
        print("Creating Phoebe Connection")
        value = self.ssh_manager.add_connection(self.config["phoebe"])
        if value != False:
            self.flags.phoebe_ssh = True
            self.phoebe_connect.setEnabled(False)
            self.phoebe_hello.setEnabled(True)


    def phoebe_socket_connection(self):
        print("Creating Phoebe Socket Connection")
        value = self.controller.phoebe_connect()
        if value != False:
            self.flags.phoebe_socket = True
            self.phoebe_hello.setEnabled(False)

    def phoebe_send_ctrlc(self):
        self.controller.phoebe_ctrlc()
        #self.ssh_manager.exit_flag = True


    ###### Load Functions ######
    def load_add_connection(self):
        print("Creating Load Connection")
        value = self.ssh_manager.add_connection(self.config["load"])
        if value != False:
            self.flags.load_ssh = True
            self.load_connect.setEnabled(False)
            self.load_hello.setEnabled(True)

    def load_socket_connection(self):
        print("Creating Load Socket Connection")
        value = self.controller.load_connect()
        if value != False:
            self.flags.load_socket = True
            self.load_hello.setEnabled(False)

    def load_send_ctrlc(self):
        self.controller.load_ctrlc()


    ###### Source Functions ######
    def source_add_connection(self):
        print("Creating Source Connection")
        value = self.ssh_manager.add_connection(self.config["source"])
        if value != False:
            self.flags.source_ssh = True
            self.source_connect.setEnabled(False)
            self.source_hello.setEnabled(True)

    def source_socket_connection(self):
        print("Creating Source Socket Connection")
        value = self.controller.source_connect()
        if value != False:
            self.flags.source_socket = True
            self.source_hello.setEnabled(False)


    def source_send_ctrlc(self):
        self.controller.source_ctrlc()

    ###### General GUI Functions ########

    # Connects the stop button to the interrupt function
    # Also disables the stop button
    # Also requests an interrupt from the thread, which will stop the test in the wotm algorithm
    def interrupt_test(self):
        self.stop_test.setEnabled(False)
        self.thread.requestInterruption()

    
    # Code that handles when you press the X button on the window
    # Useful for ensuring that all processes are closed when the window is closed
    def closeEvent(self, event):
        self.ssh_manager.thread_running = False
        self.thread_ssh.join()
        event.accept()


    # House keeping to set variables and run the wotm "setup" function
    def run_setup(self):
        print("Starting Test")

        # Setting Initial Variables     
        if self.charge_mode.isChecked():
            self.controller.charge_mode == True
        self.controller.num_data_per_period = int(self.meas)
        self.controller.data_name = str(self.title)
        try:
            self.controller.setup()
        except: 
            print("Error in setup")
            print("Make sure you have connected to the SSH servers and sockets")

    # Rearranges the data from the wotm algorithm into a table for the GUI
    # Very messy because of the way the data is stored in the wotm algorithm and I messed up :c
    def rearrange_data(self,n):
        #print(self.data_table.data_list)\

        # Source Data
        self.data_table.data_list[0][0] = ('Source in Voltage (V)', n.iloc[-1][2])
        self.data_table.data_list[0][1] = ('Source in Current (A)', n.iloc[-1][1])
        self.data_table.data_list[0][2] = ("TE Battery Voltage (V)", n.iloc[-1][5])
        self.data_table.data_list[0][3] = ("TE Volts per Cell (V)", round(n.iloc[-1][5]/13, 2) )
        self.data_table.data_list[0][4] = ("TE Battery Current (A)", n.iloc[-1][6])
        self.data_table.data_list[0][5] = ("400 Line Voltage (V)", n.iloc[-1][7])
        self.data_table.data_list[0][6] = ("400 Line Current (A)", n.iloc[-1][8])
        self.data_table.data_list[0][7] = ("TE BCM LV IN Voltage (V)", n.iloc[-1][3])
        self.data_table.data_list[0][8] = ("TE BCM LV IN Current (A)", n.iloc[-1][4])
        self.data_table.data_list[0][9] = ("TE Victron Voltage (V)", n.iloc[-1][17])
        self.data_table.data_list[0][10] = ("TE Victron Current (A)", n.iloc[-1][18])
        self.data_table.data_list[0][11] = ("TE Victron VPV (V)", n.iloc[-1][19])
        self.data_table.data_list[0][12] = ("TE Victron WPV (W)", n.iloc[-1][20])

        # Load Data
        self.data_table.data_list[1][0] = ("LE Load Voltage (V)", n.iloc[-1][9])
        self.data_table.data_list[1][1] = ("LE Load Current (A)", n.iloc[-1][10])
        self.data_table.data_list[1][2] = ("LE Battery Voltage (V)", n.iloc[-1][11])
        self.data_table.data_list[1][3] = ("LE Volts per Cell (V)", round(n.iloc[-1][11]/7, 2))
        self.data_table.data_list[1][4] = ("LE Battery Current (A)", n.iloc[-1][12])
        self.data_table.data_list[1][5] = ("LE BCM Voltage In (V)", n.iloc[-1][13])
        self.data_table.data_list[1][6] = ("LE BCM Current In (A)", n.iloc[-1][15])
        self.data_table.data_list[1][7] = ("LE BCM Voltage Out (V)", n.iloc[-1][14])
        self.data_table.data_list[1][8] = ("LE BCM Current Out (A)", n.iloc[-1][16])
        self.data_table.data_list[1][9] = ("LE Victron Voltage (V)", n.iloc[-1][21])
        self.data_table.data_list[1][10] = ("LE Victron Current (A)", n.iloc[-1][22])
        self.data_table.data_list[1][11] = ("LE Victron VPV (V)", n.iloc[-1][23])
        self.data_table.data_list[1][12] = ("LE Victron WPV (W)", n.iloc[-1][24])

        # Power Supply Data
        self.data_table.data_list[2][0] = ("BK Load Voltage (V)", round(n.iloc[-1][25], 2))
        self.data_table.data_list[2][1] = ("BK Load Current (A)", round(n.iloc[-1][26], 2))
        self.data_table.data_list[2][2] = ("BK Load Power (W)", round(n.iloc[-1][27], 2))
        self.data_table.data_list[2][3] = ("PS Voltage (V)", round(n.iloc[-1][28], 2))
        self.data_table.data_list[2][4] = ("PS Current (A)", round(n.iloc[-1][29], 2))
        self.data_table.data_list[2][5] = ("PS Power (W)", round(n.iloc[-1][30], 2))

        # This function handles taking the data and creating a graph in a seperate window
        self.printer.print_graphs(n, self.ax, self.fig, self.fulltime, final=False)

        self.data_table.update_table()

    # Code responsible for running all of the setup
    # CURRENTLY DOES NOT WORK, NOT UTILIZED IN CODE
    def run_all(self):
        # Running all of ssh connections
        if self.flags.phoebe_ssh == False:
            logging.debug("Phoebe ssh Connection")
            self.phoebe_socket_connection()
            QtTest.QTest.qWait(2000)
        if self.flags.source_ssh == False:
            logging.debug("Source ssh Connection")
            self.source_socket_connection()
            QtTest.QTest.qWait(2000)
        if self.flags.load_ssh == False:
            logging.debug("Load ssh Connection")
            self.load_socket_connection()
            QtTest.QTest.qWait(2000)

        # Running all of the socket connections
        if self.flags.phoebe_socket == False and self.flags.phoebe_ssh == True:
            logging.debug("Phoebe Socket Connection")
            self.phoebe_socket_connection()
            QtTest.QTest.qWait(2000)
        if self.flags.source_socket == False and self.flags.source_ssh == True:
            logging.debug("Source Socket Connection")
            self.source_socket_connection()
            QtTest.QTest.qWait(2000)
        if self.flags.load_socket == False and self.flags.load_ssh == True:
            logging.debug("Load Socket Connection")
            self.load_socket_connection()
            QtTest.QTest.qWait(2000)
        logging.debug("All Connections Established")

    # Performs housekeeping in order to run the wotm algorithm main code
    def run_main(self):
        print("Starting Test")
        #self.controller.run_main()

        # Set up the plots
        plt.ion()  # Turn on interactive mode
        # Set style as five-thirty-eight
        plt.style.use('fivethirtyeight')
        self.fig, self.ax = plt.subplots(2, 3)  # Create a new figure and axis
        self.fig.set_size_inches(20, 10)

        # Disable start test button (prevents duplicates)
        self.start_test.setEnabled(False)

        # Here we create a separate thread in order to run the wotm algorithm
        # This thread communicates with the main thread through signals and slots

        # Step 2: Create a QThread object
        self.thread = QThread() # type: ignore
        # Step 3: Create a worker object
        # Worker object is created earlier as "controller"
        print("Starting Test")
        # Step 4: Move worker to the thread
        self.controller.moveToThread(self.thread)

        # Step 5: Connect signals and slots
        self.thread.started.connect(self.controller.run_main)
        self.controller.finished.connect(self.thread.quit)
        self.controller.finished.connect(self.controller.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.controller.dfsignal.connect(self.rearrange_data)

        #self.data_table.timer.start(2000)  # Update every 2 seconds

        print("Step1")
        self.thread.start()
        print("step2")
    



# Main code that launches the GUI      
if __name__ == "__main__":

    app = QApplication(sys.argv)


    widget = MainWindow()

    widget.show()

    sys.exit(app.exec())

