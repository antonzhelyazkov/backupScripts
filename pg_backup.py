import datetime
import getopt
import json
import logging
import os
import socket
import sys
import time

ARGV = sys.argv[1:]
VERBOSE = False
CONFIG_FILE = "./pg_backup.json"
LOG_DIR_DEFAULT = "."
HOSTNAME = socket.gethostname().split(".")[0]

try:
    opts, argv = getopt.getopt(ARGV, "c:v", ["config=", "verbose"])
except getopt.GetoptError as err:
    print(err)
    opts = []

for opt, arg in opts:
    if opt in ['-c', '--config']:
        CONFIG_FILE = arg
    if opt in ['-v', '--verbose']:
        VERBOSE = True


################################################################

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


def add_slash(directory: str) -> str:
    if directory.endswith("/"):
        return directory
    else:
        return directory + "/"


def process_pid_file(pid_f: str) -> bool:
    if os.path.isfile(pid_f):
        print_log(VERBOSE, "ERROR pid file exists %s" % pid_f)
        return False
    else:
        try:
            f = open(pid_f, "w")
            f.write(str(os.getpid()))
            f.close()
            return True
        except IOError as e:
            print_log(VERBOSE, 'ERROR %s' % e)
            return False


def process_nagios_file(nagios_f: str) -> bool:
    time_now = int(time.time())

    try:
        f = open(nagios_f, "w")
        f.write(str(time_now))
        f.close()
        return True
    except IOError as e:
        print_log(VERBOSE, 'ERROR %s' % e)
        return False


def mkdir(directory: str) -> dict:
    try:
        os.makedirs(directory, exist_ok=True)
        out_dict = {'status': True,
                    'msg': "INFO Directory %s created" % directory}
    except OSError as e:
        out_dict = {'status': False,
                    'msg': 'ERROR %s' % e}

    return out_dict


######################################################

config_open = open(CONFIG_FILE, encoding='utf-8')
CONFIG_DATA = json.load(config_open)
SCRIPT_NAME = os.path.basename(sys.argv[0]).split(".")
PID_FILE = add_slash(CONFIG_DATA['pid_file_path']) + SCRIPT_NAME[0] + ".pid"
NAGIOS_FILE = add_slash(CONFIG_DATA['pid_file_path']) + SCRIPT_NAME[0] + ".nagios"
if not process_pid_file(PID_FILE):
    sys.exit(1)

if HOSTNAME is None or HOSTNAME == '':
    print_log(VERBOSE, "ERROR in hostname %s" % HOSTNAME)
    sys.exit(1)

backup_dir = mkdir(CONFIG_DATA['backup_dir'])
if not backup_dir['status']:
    print_log(VERBOSE, backup_dir['msg'])
    sys.exit(1)

current_date = datetime.datetime.now()
print(current_date)
current_date_string = current_date.strftime("%Y%m")
print(current_date_string)

if process_nagios_file(NAGIOS_FILE):
    os.remove(PID_FILE)
else:
    print_log(VERBOSE, "ERROR could not write to %s" % NAGIOS_FILE)
