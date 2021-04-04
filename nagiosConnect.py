import sys
import time
import getopt
import os
from datetime import datetime
import psutil as psutil

verbose = False
argv = sys.argv[1:]
pid_file = None
time_delta = None
nagios_file = None
item_pid = None

time_now = int(time.time())

exit_ok = 0
exit_warning = 1
exit_critical = 2

try:
    opts, argv = getopt.getopt(argv, "n:p:t:v", ["pid=", "verbose", "time=", "nagios="])
except getopt.GetoptError as err:
    print(err)
    opts = []

for opt, arg in opts:
    if opt in ['-p', '--pid']:
        pid_file = arg
    if opt in ['-v', '--verbose']:
        verbose = True
    if opt in ['-t', '--time']:
        time_delta = arg
    if opt in ['-n', '--nagios']:
        nagios_file = arg

##########################

##########################

if pid_file is None:
    print(f"ERROR pid file needed -p <pid_file>")
    sys.exit(exit_critical)

if nagios_file is None:
    print(f"ERROR nagios file needed -n <pid_file>")
    sys.exit(exit_critical)

if time_delta is None:
    print(f"ERROR time delta needed -t <time seconds start interval>")
    sys.exit(exit_critical)

if os.path.isfile(pid_file):
    f = open(pid_file, "r")
    item_pid = f.read()

f = open(nagios_file, "r")
item_nagios = f.read()

time_critical = int(time_now) - int(time_delta)

script_name_base = os.path.basename(pid_file).replace('.pid', '')

if int(item_nagios) < time_critical:
    print(f"WARNING last backup had finished in far ancient times")
    sys.exit(1)

if item_pid is not None:
    try:
        process = psutil.Process(int(item_pid))
    except psutil.NoSuchProcess:
        print(f"ERROR process with id {item_pid} not found")
        sys.exit(exit_critical)
    else:
        if script_name_base in process.cmdline()[1]:
            print(f"OK script {process.cmdline()[1]} is running")
        sys.exit(exit_ok)
else:
    print(f"OK script {script_name_base} finished at {datetime.fromtimestamp(int(item_nagios))}")
    sys.exit(exit_ok)
