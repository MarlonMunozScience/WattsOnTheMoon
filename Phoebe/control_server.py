import socket
from BK_Precision_8616_ctrl import load
from SPD3303 import SPD
from BK_Precision_MR50040_ctrl import power
import traceback
import time
import logging
from datetime import datetime

# Code to grab current time
current_datetime = datetime.now()
current_datetime_str = current_datetime.strftime("%m-%d %H-%M-%S")



logging.basicConfig(filename=r'C:\Users\Phoebe\Desktop\WattsontheMoon-v2\control_phoebe\logs\log.log', filemode='w', level=logging.DEBUG)

logging.debug("\n")
logging.debug("\n")
logging.debug("\n")
logging.debug("\n")
logging.debug("\n")
logging.debug(f"{current_datetime_str}")
logging.debug('Script has started')

host = ""
port = 9000

instr_load = load()
instr_load.setup()
instr_power = power("COM3")
instr_power.turn_off()
instr_load.turn_off()

logging.debug('Load and Power Supply turned off')

SPD = SPD()
SPD.setup()
ch1 = SPD.Channel(1, SPD.spd) # Change later to be included in commands
ch1.set_output(False)

# Set up ch2 for light
ch2 = SPD.Channel(2, SPD.spd) # Change later to be included in commands
ch2.set_output(False)

# This will always have the same voltage and current
ch2.set_voltage(24)
ch2.set_current(1)

logging.debug("Setup Complete")


while True:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            print("listening")
            logging.debug("listening")
            s.settimeout(1)
            while True:
                try:
                    s.listen(1)
                    conn, addr = s.accept()
                    # Handle the connection here
                    with conn:
                        print(f"Connected by {addr}")
                        logging.debug(f"Connected by {addr}")
                        while True:
                            data_in = conn.recv(1024)
                            if not data_in:
                                break
                            data_in = data_in.decode("ascii")
                            data_in = data_in.split(',')
                            print(data_in)
                            logging.debug(data_in)
                            command = data_in[0]

                            if command == 'hello':
                                conn.sendall(b'Hello!!!!')

                            if command == 'setup':
                                print("Starting setup")
                                instr_load.setup()
                                print("confirming Setup")

                                conn.sendall(f'ID: {instr_load.confirm()}'.encode())

                            if command == "on":
                                instr_load.turn_on()
                                conn.sendall("Electronic Load on".encode())
                            
                            if command == "off":
                                instr_load.turn_off()
                                conn.sendall("Electronic Load off".encode())

                            if command == 'mode':
                                if data_in[1] == "CW":
                                    conn.sendall(f"Mode: {instr_load.const_power_mode()}".encode())
                                elif data_in[1] == 'CC':
                                    conn.sendall(f"Mode: {instr_load.const_current_mode()}".encode())
                                else:
                                    conn.sendall("Error ".encode())
                            
                            if command == "power":
                                instr_load.set_power(float(data_in[1]))
                                conn.sendall(f"Power set to {data_in[1]} W".encode())
                            
                            #Still needs to be tested 
                            if command == "current":
                                instr_load.set_current(float(data_in[1]))
                                conn.sendall(f"Current set to {float(data_in[1])} A".encode())

                            if command == "meas_voltage":
                                conn.sendall(f"{instr_load.measure_voltage()}".encode())

                            if command == "meas_current":
                                conn.sendall(f"{instr_load.measure_current()}".encode())



                            # Power supply commands
                            if command == "PS_confirm":
                                conn.sendall(f"{instr_power.confirm}".encode())
                            
                            if command == "PS_turn_on":
                                instr_power.turn_on()
                                conn.sendall("Power supply turned on".encode())

                            if command == "PS_turn_off":
                                instr_power.turn_off()
                                conn.sendall("Power supply turned off".encode())

                            if command == "PS_set_voltage":
                                instr_power.set_voltage(int(data_in[1]))
                                conn.sendall(f"{instr_power.meas_voltage()}".encode())

                            if command == "PS_set_current":
                                instr_power.set_current(int(data_in[1]))
                                conn.sendall(f"{instr_power.meas_current()}".encode())

                            if command == "PS_meas_voltage":
                                conn.sendall(f"{instr_power.meas_voltage()}".encode())

                            if command == "PS_meas_current":
                                conn.sendall(f"{instr_power.meas_current()}".encode())
                            
                            if command == "PS_meas_power":
                                conn.sendall(f"{instr_power.meas_power()}".encode()) 

                            # Take measurements on both power supply and load
                            # Returns a list of the measurements
                            if command == "measure_all":
                                measurements = []
                                load_voltage = instr_load.measure_voltage() # String
                                load_current = instr_load.measure_current() # String

                                measurements.extend([load_voltage, load_current])
                                measurements.extend([float(load_voltage) * float(load_current)]) # Power supply power
                                measurements.extend([instr_power.meas_voltage()])
                                measurements.extend([instr_power.meas_current()])
                                measurements.extend([instr_power.meas_power()])

                                conn.sendall(f"{measurements}".encode())


                            # SPD Commands
                            if command == "SPD_setup":
                                SPD.setup()
                                conn.sendall("Setup Confirmed".encode())

                            if command == "SPD_confirm":
                                conn.sendall(f"SPD Connected at ID: {SPD.confirm()}".encode())

                            if command == "CH1_set_voltage":
                                ch1.set_voltage(int(data_in[1]))
                                conn.sendall(f"Ch1 voltage set to {int(data_in[1])}".encode())
                            
                            if command == "CH1_set_current":
                                ch1.set_current(float(data_in[1]))
                                conn.sendall(f"Ch1 current set to {float(data_in[1])}".encode())
                            
                            if command == "CH1_set_output":
                                if data_in[1] == "on":
                                    ch1.set_output(True)
                                    conn.sendall("ON".encode())
                                elif data_in[1] == "off":
                                    ch1.set_output(False)
                                    conn.sendall("OFF".encode())
                                else: 
                                    conn.sendall("Error".encode())

                            if command == "CH2_set_output":
                                if data_in[1] == 'on':
                                    ch2.set_output(True)
                                    conn.sendall("ON".encode())
                                elif data_in[1] == "off":
                                    ch2.set_output(False)
                                    conn.sendall("OFF".encode())
                                else: 
                                    conn.sendall("Error".encode())
                            
                            if command == "CTRLC":
                                raise Exception
                        
                except socket.timeout:
                    logging.debug("Socket Timeout")
                    # The socket timed out, continue listening
                    pass 
                except socket.error:
                    logging.debug("Socket error")

                except:
                    logging.debug("Ctrl C sent")
                    print("Ctrl C sent")
                    print(traceback.print_exc())
                    logging.debug(traceback.print_exc())
                    try:
                        instr_load.set_power(0)
                        instr_load.turn_off()
                    except:
                        print("Unable to turn load off on error")
                        pass
                    try: 
                        instr_power.set_voltage(0)
                        instr_power.turn_off()

                    except:
                        print("unable to turn off power supply")
                    try:
                        ch1.set_output(False)
                    except:
                        print("Unable to turn off SPD")
                    logging.debug("Shutdown Complete")
                    print('Shutdown Complete')
                    time.sleep(1)
                    print("Shutdown 1")
                    time.sleep(1)
                    print("Shutdown 2")

                




    except BaseException:
        logging.debug("Exiting on Error")
        logging.debug(traceback.print_exc())
        print("Exiting on Error")
        print(traceback.print_exc())
        try:
            instr_load.set_power(0)
            instr_load.turn_off()
        except:
            print("Unable to turn load off on error")
            pass
        try: 
            instr_power.set_voltage(0)
            instr_power.turn_off()

        except:
            print("unable to turn off power supply")
        try:
            ch1.set_output(False)
        except:
            print("Unable to turn off SPD")
        logging.debug("Exit complete")
        print('Exit Complete')
        time.sleep(3)
        exit()


