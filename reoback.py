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
    out_data = {"status": True}
    err_dirs = []
    for item in dirs:
        if not os.path.isdir(item):
            out_data['status'] = False
            err_dirs.append(item)

    if len(err_dirs) > 0:
        out_data['err'] = err_dirs

    return out_data


def walk_files(directory: str) -> list:
    all_files = []
    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        if os.path.isdir(full_path):
            all_files.extend(walk_files(full_path))
        else:
            all_files.append(full_path)

    return all_files


def excl(file_to_check, excludes):
    if any(item_file in file_to_check.name for item_file in excludes):
        return None
    else:
        return file_to_check


########################################

config_open = open(CONFIG_FILE, encoding='utf-8')
CONFIG_DATA = json.load(config_open)

SCRIPT_NAME = os.path.basename(sys.argv[0]).split(".")
PID_FILE = add_slash(CONFIG_DATA['pid_file_path']) + SCRIPT_NAME[0] + ".pid"
NAGIOS_FILE = add_slash(CONFIG_DATA['pid_file_path']) + SCRIPT_NAME[0] + ".nagios"
if not process_pid_file(PID_FILE):
    sys.exit(1)

DIRS_EXISTS = [CONFIG_DATA['tmp_dir'], CONFIG_DATA['log_dir'], CONFIG_DATA['pid_file_path']]
DIRS_TO_ARCHIVE = []
for item_dir in CONFIG_DATA['backup']:
    DIRS_EXISTS.append(item_dir['path'])
    DIRS_TO_ARCHIVE.append(item_dir['path'])

if not check_dirs_exist(DIRS_EXISTS)['status']:
    print_log(VERBOSE, f"ERROR dirs not found {check_dirs_exist(DIRS_EXISTS)['err']}")
    sys.exit(1)

if HOSTNAME is None or HOSTNAME == '':
    print_log(VERBOSE, f"ERROR in hostname {HOSTNAME}")
    sys.exit(1)

for item_arch in CONFIG_DATA['backup']:
    files_arr = walk_files(item_arch['path'])
    print(files_arr)

if process_nagios_file(NAGIOS_FILE):
    os.remove(PID_FILE)
else:
    print_log(VERBOSE, f"ERROR could not write to {NAGIOS_FILE}")
