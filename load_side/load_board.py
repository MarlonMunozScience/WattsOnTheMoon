import socket
from ctrl_load import load_gpio, BCM
from load_adc import adc
import traceback
import time

from victron import victron
host = ""
port = 9001

vict = victron("/dev/ttyUSB0")

gpio = load_gpio()
bcm = BCM()
load_adc = adc()

# Setting Switches to zero at beginning
gpio.hv_line("off")
time.sleep(1)
gpio.bcm_lv_ssr("off")
time.sleep(1)
gpio.load_ssr("off")


while True:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            print("listening")
            while True:
                s.listen(1)
                conn, addr = s.accept()
                with conn:
                    print(f"Connected by {addr}")
                    while True:
                        try:
                            data_in = conn.recv(1024)
                            if not data_in:
                                break
                            data_in = data_in.decode("ascii")
                            data_in = data_in.split(',')
                            print(data_in)
                            command = data_in[0]

                            if command == 'hello':
                                conn.sendall(b'Hello!!!!')

                            if command == "hv_line":
                                state = data_in[1]
                                # Sends "hv_line on" or "hv_line off" if successful
                                conn.sendall(f"{gpio.hv_line(state)}".encode())
                            
                            if command == "bcm_lv_ssr":
                                state = data_in[1]
                                # Sends "load_ssr on" or "load_ssr off" if successful
                                conn.sendall(f"{gpio.bcm_lv_ssr(state)}".encode())
                            
                            if command == "load_ssr":
                                state = data_in[1]
                                # Sends "load_ssr on" or "load_ssr off" if successful
                                conn.sendall(f"{gpio.load_ssr(state)}".encode())
                            
                            if command == "read_adcs":
                                try:
                                    conn.sendall(f"{load_adc.read_all()}".encode())
                                except:
                                    conn.sendall(f"{[0, 0, 0, 0]}".encode())

                            if command == "bcm_read":
                                try:
                                    conn.sendall(f"{bcm.bcm_read_all()}".encode())
                                except:
                                    conn.sendall(f"{[0, 0, 0, 0]}".encode())
                                    print("error reading bcm")
                                    continue
                            
                            if command == "bcm_activate":
                                bcm.activate()
                                conn.sendall(b"bcm_activate")

                            if command == "victron_confirm":
                                conn.sendall(f"{vict.confirm()}".encode())

                            if command == "read_victrons":
                                # Sends a list of ["Batt Voltage", "Batt Current", in_voltage, "in_current"]
                                try:
                                    conn.sendall(f"{vict.read_parse()}".encode())

                                except:
                                    conn.sendall(f"{'bat_current': 0.0, 'bat_voltage': 0.0, 'in_voltage': 0.0, 'in_power': 0.0}".encode())
                                    print("error reading victron")
                                    continue

                            if command == "CTRLC":
                                print("CTRLC")
                                raise Exception
                            
                            if command == 'Monitor':
                                print("Begin Monitoring")
                                conn.sendall(b"Monitoring")
                                conn.settimeout(0.2)
                                conn.setblocking(False)

                            if command == 'Stop_Monitor':
                                print("Stop Monitoring")
                                conn.setblocking(True)
                                conn.settimeout(None)
                                conn.sendall(b"Monitoring")

                        except socket.timeout:
                            # No data available, read ADCs
                            response = adc.read_all()
                            adc.check_all(response)
                            #print(response)

                        except BlockingIOError:
                            # No data available, read ADCs
                            response = load_adc.read_all()
                            load_adc.check_all(response)
                            #print(response)


                        except IOError:
                            conn.sendall(f"{[0, 0, 0, 0]}".encode())
                            print("IOError")
                            continue

                        except:
                            print("Error trying to understand command")
                            print(traceback.print_exc())
                            raise Exception
    except Exception:
        
        traceback.print_exc()

        
        gpio.hv_line("off")
        time.sleep(1)
        gpio.bcm_lv_ssr("off")
        time.sleep(1)
        gpio.load_ssr("off")
        print("Exiting Complete")
        time.sleep(1)
        exit()