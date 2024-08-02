"""
Python Code responsible for creating a remote ssh connection into Phoebe and running the server.py script

Creates ssh connections with active computers that run a listening script on startup. Allows the user to manage ssh connections on other computers
without using desktop sharing. Additionally, sends the local output of the ssh computer to the main computer and displays it in our pyQT WOTM GUI.

"""


import paramiko
import signal
import sys
import threading
import time
import select
import json
from PyQt6 import QtGui
from PyQt6.QtGui import QColor

"""
Class where init function creates ssh connection and runs the server.py script

Data is grabbed from the config.json file.

Connection made with the paramiko library.
"""

class ssh_connect:
    def __init__(self, json_config):
        # Parameters grabbed from config.json
        self.host = json_config['host']
        self.user = json_config['user']
        self.password = json_config['password']
        self.python_script_path = json_config['python_script_path']
        self.python_exe_path = json_config['python_exe_path']

        # Creating the SSH Connection
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.host, username=self.user, password=self.password, timeout=5) 

        self.channel = self.ssh.get_transport().open_session()
        self.channel.get_pty()

        # Executing the server.py script by calling python path and python script path
        self.channel.exec_command(f"{self.python_exe_path} -u {self.python_script_path}")


# Class that holds all of ssh objects, created from the class above
class SSHManager:
    def __init__(self):
        self.connections = []
        self.thread_running = True
        self.exit_flag = False

    # Creates the connection for respective computer, using the json file
    def add_connection(self, json_config):
        try:
            print("Adding Connection")
            connection = ssh_connect(json_config)
            self.connections.append(connection)
            print(f"Connection Established with {json_config['host']}")
            return True
        except:
            print(f"ERROR: Unable to connect to {json_config['host']}")
            return False

    # Reads the output of all of the connections.
    # This is multithreaded in the mainwindow.py file
    def read_output(self, ssh_output):
        #print("Thread Started")
        while self.thread_running:
            
            # Checks each connection for output
            channels = [conn.channel for conn in self.connections]
            if channels:
                try:

                    # Checks if theres an exit flag, if so, sends ctrl c to all connections
                    # Exit flag is set in the GUI when the user presses the ctrl c button
                    if self.exit_flag:
                        for conn in self.connections:
                            conn.channel.send(u"\x03")
                        self.exit_flag = False # So it doesn't send ctrl c more than once
                    
                    # checks if theres output from the connection
                    readable, _, _ = select.select(channels, [], [], 0.0)
                    for channel in readable:
                        if channel.recv_ready():
                            output = channel.recv(1024).decode('utf-8')
                            if len(output) > 2:  # First two characters are junk
                                
                                # Changes the color of the output depending on which computer it came from
                                if channel.get_transport().getpeername()[0] == '192.168.1.71':
                                    ssh_output.setTextColor(QColor(0, 255, 0))
                                elif channel.get_transport().getpeername()[0] == '192.168.1.56':
                                    ssh_output.setTextColor(QColor(255, 0, 0))
                                else:
                                    ssh_output.setTextColor(QColor(0, 0, 255))

                                # Outputs and housekeeping for the cursor
                                ssh_output.append(f"Output from {channel.get_transport().getpeername()}: {output}")
                                cursor = ssh_output.textCursor()
                                cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
                                ssh_output.setTextCursor(cursor)
                                
                        if channel.exit_status_ready():
                            channels.remove(channel)
                except:
                    print("Error")
                    for conn in self.connections:
                        conn.channel.send(u"\x03")
                    pass
                    

## Inline testing for running individual script

# Connection tst
def test_add_connection(manager, config):
    try:
        result = manager.add_connection(config)

        if result:
            print(f"Connection to {config['host']} computer established successfully.")
        else:
            print(f"Failed to establish connection to {config['host']} computer.")
        return result
    
    except Exception as e:
        print(f"Exception occurred while trying to connect to {config['host']} computer: {e}")
        return False

def test_read_output(manager):
    try:
        print("Starting to read output from connections.")
        manager.read_output()
        print("Output reading completed.")
        return True
    
    except Exception as e:
        print(f"Exception occurred while reading output: {e}")
        return False

if __name__ == "__main__":
    # Open json
    try:
        config_path = r"C:\Users\Lubin\Desktop\code\WOTM_GUI\config.json"
        with open(config_path, 'r') as config_file:
            config = json.load(config_file)
    except Exception as e:
        print(f"Failed to load json file: {e}")
        sys.exit(1)

    manager = SSHManager()

    # Connection Test
    connection_success = test_add_connection(manager, config['phoebe'])

    # Output Test
    if connection_success:
        # Test reading output if connection was successful
        output_success = test_read_output(manager)
    else:
        print("Skipping output reading due to connection failure.")
