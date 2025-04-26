import os
import signal
import subprocess
import time

# The os.setsid() is passed in the argument preexec_fn so
# it's run after the fork() and before  exec() to run the shell.
API_KEY = os.getenv("API_KEY", "")
SECRET_KEY = os.getenv("SECRET_KEY", "")
STABLE_PAIR = os.getenv("STABLE_PAIR", "USDT")
MA_LENGTH = os.getenv("MA_LENGTH", str(24))
RANGE = os.getenv("RANGE", str(50000))
MIN_RATIO = os.getenv("MIN_RATIO", str(0.02))
MAX_RATIO = os.getenv("MAX_RATIO", str(0.98))
REBALANCE_AT = os.getenv("REBALANCE_AT", str(5.0))
TGBOT_TOKEN = os.getenv("TGBOT_TOKEN", "")
TGBOT_CHATID = os.getenv("TGBOT_CHATID", "")


pro = subprocess.Popen(['python', '/app/vh_float.py', API_KEY,
                        SECRET_KEY,
                        STABLE_PAIR,
                        MA_LENGTH,
                        RANGE,
                        MIN_RATIO,
                        MAX_RATIO,
                        REBALANCE_AT,
                        TGBOT_TOKEN,
                        TGBOT_CHATID],
                       preexec_fn=os.setsid) 

start_time = time.time()
work_time = 0.0
delay = float(60*60*10)

while work_time < delay:
    work_time = time.time() - start_time
    time.sleep(1.0)

os.killpg(os.getpgid(pro.pid), signal.SIGTERM)  

