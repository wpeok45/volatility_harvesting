import os
import signal
import subprocess
import time

# The os.setsid() is passed in the argument preexec_fn so
# it's run after the fork() and before  exec() to run the shell.

pro = subprocess.Popen(["python", "/app/vh_float.py"], preexec_fn=os.setsid)

start_time = time.time()
work_time = 0.0
delay = float(60 * 60 * 10)

# restart app for every 10h
while work_time < delay:
    work_time = time.time() - start_time
    time.sleep(1.0)


os.killpg(os.getpgid(pro.pid), signal.SIGTERM)
