"""
Python script to create a ssh connection to the load and run the load_board.py script

TODO: Add server uptime on error (server should just restart on ctrl c rather than having to manually restart it)

TODO: Rename file on load to load_server.py without breaking anything else 


"""

import paramiko
import signal
import sys
import threading
import time
import select


# Connection details 
remote_host = '192.168.1.66'
remote_user = 'periscope'
remote_password = 'spaceball-periscope'
remote_python_script = r'/home/periscope/Code/BCM/control_V2/main/load_board.py'
python_exe_path = r'/bin/python'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(remote_host, username=remote_user, password=remote_password)

channel = ssh.get_transport().open_session()
channel.get_pty()

channel.exec_command(f"{python_exe_path} -u {remote_python_script}")


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