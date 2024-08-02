"""
Python Code responsible for creating a remote ssh connection into Phoebe and running the server.py script

TODO: Add server uptime on error (server should just restart on ctrl c rather than having to manually restart it)


"""


import paramiko
import signal
import sys
import threading
import time
import select

"""
def ssh_handler(signum, frame):
    ssh_stdin.write('\x03')  # Send Ctrl+C character to the remote script
    ssh_stdin.flush()
"""

def read_output():
    while True:
        val = ssh_stdout.readline().strip()
        if val:
            print(val)
            time.sleep(0.1)
        else:
            time.sleep(0.1)
            break


remote_host = '192.168.1.71'
remote_user = 'phoebe'
remote_password = 'spaceball-phoebe'
remote_python_script = r'C:\Users\Phoebe\Desktop\WattsontheMoon-v2\control_phoebe\server.py'
python_exe_path = r'C:/Users/Phoebe/AppData/Local/Programs/Python/Python39/python.exe'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(remote_host, username=remote_user, password=remote_password)

#channel = ssh.invoke_shell()

channel = ssh.get_transport().open_session()
channel.get_pty()

channel.exec_command(f"{python_exe_path} -u {remote_python_script}")

#signal.signal(signal.SIGINT, ssh_handler)  # Set up signal handler for keyboard interrupts
count = 0

while True:
    try:
        if channel.exit_status_ready():
            break
        #print(count)
            
        rl, wl, xl = select.select([channel], [], [], 0.0)
        if len(rl) > 0:
            print(channel.recv(1024).decode())
    except:
        print("Error")
        channel.send(u"\x03")
        pass
