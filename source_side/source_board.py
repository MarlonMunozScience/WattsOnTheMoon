import socket
from ctrl_source import source_gpio
from source_adc import adc as source_adc
import traceback
import time
from victron import victron
host = ""
port = 9002
print("Finished imports")

vict = victron("/dev/ttyUSB0") # May need to change
print("step1")
gpio = source_gpio()
print("step2")
adc = source_adc()

print("step3")
#bcm = BCM()
print("Turning everything off")
gpio.ssr_120("off")
time.sleep(1)
gpio.bcm_lv_feed("off")
time.sleep(1)
gpio.ssr_400("off")
print("We made it") 

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

                            
                            if command == "ssr_120":
                                state = data_in[1]
                                # Returns ssr_120 on or ssr_120 off if successful
                                conn.sendall(f"{gpio.ssr_120(state)}".encode())

                            if command == "bcm_lv_feed":
                                state = data_in[1]
                                # Returns bcm_lv_feed on or bcm_lv_feed off if successful
                                conn.sendall(f"{gpio.bcm_lv_feed(state)}".encode())

                            if command == "ssr_400":
                                state = data_in[1]
                                # Returns ssr_400 on or ssr_400 off if successful
                                conn.sendall(f"{gpio.ssr_400(state)}".encode())

                            if command == "read_adcs":
                                # Returns a list of  ADC values
                                try:
                                    response = adc.read_all()   
                                    conn.sendall(f"{response}".encode())
                                except Exception:
                                    conn.sendall(f"{[0,0,0,0,0,0,0,0]}".encode())
                                    print("ADC read failed")
                                    continue  
                                
                            # Inactive commands
                            if command == "bcm_status":
                                conn.sendall(f"{bcm.query_bcm_status()}".encode())

                            if command == "victron_confirm":
                                conn.sendall(f"{vict.confirm()}".encode())
                                

                            if command == "read_victrons":
                                # Sends a list of ["Batt Voltage", "Batt Current", in_voltage, "in_current"]
                                try:
                                    conn.sendall(f"{vict.read_parse()}".encode())
                                except:
                                    conn.sendall(f"{'bat_current': 10000.0, 'bat_voltage': 48900.0, 'in_voltage': 119960.0, 'in_power': 500.0}".encode())
                                    continue

                            if command == 'CTRLC':
                                print("CTRLC")
                                raise Exception
                            
                            if command == 'Monitor':
                                print("Begin Monitoring")
                                conn.sendall(b"Monitoring")
                                conn.settimeout(0.1)
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
                            response = adc.read_all()
                            adc.check_all(response)
                            #print(response)

                        except:
                            print("Error in command")
                            print(traceback.print_exc())
                            #conn.sendall(b"error")
                            raise Exception

    except Exception:
        traceback.print_exc()
        gpio.ssr_120("off")
        time.sleep(1)
        gpio.bcm_lv_feed("off")
        time.sleep(1)
        gpio.ssr_400("off")
        print("exited safely")
        
