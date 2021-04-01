import getopt
import json
import logging
import os
import socket
import sys
import time

VERBOSE = False
CONFIG_FILE = "./config.json"
LOG_DIR_DEFAULT = "."
HOSTNAME = socket.gethostname().split(".")[0]
argv = sys.argv[1:]

try:
    opts, argv = getopt.getopt(argv, "c:v", ["config=", "verbose"])
except getopt.GetoptError as err:
    print(err)
    opts = []

for opt, arg in opts:
    if opt in ['-c', '--config']:
        config_file = arg
    if opt in ['-v', '--verbose']:
        VERBOSE = True


def print_log(debug, message):
    file_name = os.path.basename(sys.argv[0]).split(".")
    current_log_dir = add_slash(CONFIG_DATA['log_dir'])

    if os.path.isdir(current_log_dir):
        script_log = current_log_dir + "/" + file_name[0] + ".log"
    else:
        script_log = LOG_DIR_DEFAULT + "/" + file_name[0] + ".log"

    logging.basicConfig(filename=script_log, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    logging.info(message)

    if debug is True:
        print(message)


def add_slash(directory):
    if not directory.endswith("/"):
        dir_return = directory + "/"
    else:
        dir_return = directory
    return dir_return


def process_nagios_file(nagios_f: str) -> bool:
    time_now = int(time.time())

    try:
        f = open(nagios_f, "w")
        f.write(str(time_now))
        f.close()
        return True
    except IOError as e:
        print_log(VERBOSE, f"ERROR {e}")
        return False


def process_pid_file(pid_f: str) -> bool:
    if os.path.isfile(pid_f):
        print_log(VERBOSE, f"ERROR pid file exists {pid_f}")
        return False
    else:
        try:
            f = open(pid_f, "w")
            f.write(str(os.getpid()))
            f.close()
            return True
        except IOError as e:
            print_log(VERBOSE, f"ERROR {e}")
            return False


def check_dirs_exist(dirs: list) -> dict:
    out_data = {}
    for item in dirs:
        print(item)

    return out_data


########################################

config_open = open(CONFIG_FILE, encoding='utf-8')
CONFIG_DATA = json.load(config_open)

SCRIPT_NAME = os.path.basename(sys.argv[0]).split(".")
PID_FILE = add_slash(CONFIG_DATA['pid_file_path']) + SCRIPT_NAME[0] + ".pid"
NAGIOS_FILE = add_slash(CONFIG_DATA['pid_file_path']) + SCRIPT_NAME[0] + ".nagios"
if not process_pid_file(PID_FILE):
    sys.exit(1)

DIRS_EXISTS = [CONFIG_DATA['tmp_dir'], CONFIG_DATA['log_dir'], CONFIG_DATA['pid_file_path']]
for item_dir in CONFIG_DATA['backup']:
    DIRS_EXISTS.append(item_dir['path'])
    DIRS_EXISTS.extend(item_dir['excludes'])
check_dirs_exist(DIRS_EXISTS)


if HOSTNAME is None or HOSTNAME == '':
    print_log(VERBOSE, f"ERROR in hostname {HOSTNAME}")
    sys.exit(1)


if process_nagios_file(NAGIOS_FILE):
    os.remove(PID_FILE)
else:
    print_log(VERBOSE, f"ERROR could not write to {NAGIOS_FILE}")
