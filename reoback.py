import ftplib
import getopt
import json
import logging
import os
import socket
import subprocess
import sys
import time

VERBOSE = False
CONFIG_FILE = "./config.json"
LOG_DIR_DEFAULT = "."
HOSTNAME = socket.gethostname()
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


def remove_slash(directory):
    if directory.endswith("/"):
        size = len(directory)
        dir_return = directory[:size - 1]
        print(dir_return)
        return dir_return
    else:
        return directory


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


def tar_command(arch_dir: str, excludes: list, out_file: str) -> list:
    tar_arr = ["/usr/bin/tar", "-cf", out_file, "-I", "pigz"]
    if len(excludes) > 0:
        for item_exclude in excludes:
            tar_arr.extend([f"--exclude={remove_slash(item_exclude)}"])

    tar_arr.append(arch_dir)

    return tar_arr


def create_dir(directory: str) -> bool:
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except OSError as e:
        print_log(VERBOSE, f"ERROR {e}")
        return False


def create_ftp_dir(directory: str, session) -> bool:
    try:
        session.mkd(directory)
        print_log(VERBOSE, f"INFO directory created {directory}")
        return True
    except ftplib.error_perm as perm:
        print_log(VERBOSE, f"INFO directory exists {directory}")
        return True
    except ftplib.Error as e:
        print_log(VERBOSE, f"ERROR {e}")
        return False


def ftp_session(ftp_host: str, ftp_user: str, ftp_pass: str):
    try:
        session = ftplib.FTP(ftp_host, ftp_user, ftp_pass, timeout=3)
        print(session)
        return session
    except ftplib.Error as e:
        print(f"ERROR {ftp_host} {e}")
        return False
    except socket.timeout as t:
        print(f"ERROR {ftp_host} {t}")
        return False


def ftp_upload(file: str, hostname: str, backup_stamp: int, session) -> bool:
    f_name = os.path.basename(file)
    dir_stamp = f"{hostname}/{backup_stamp}"

    if not create_ftp_dir(hostname, session):
        sys.exit(1)

    if not create_ftp_dir(dir_stamp, session):
        sys.exit(1)

    file_fh = open(file, "rb")
    try:
        session.storbinary(f"STOR {dir_stamp}/{f_name}", file_fh)
        return True
    except ftplib.Error as e:
        print_log(VERBOSE, f"ERROR {e}")
        return False
    finally:
        file_fh.close()
        session.close()


def ftp_dir_remove(session, path: str) -> bool:
    for (name, facts) in session.mlsd(path=path):
        if name in ['.', '..']:
            continue
        elif facts['type'] == 'file':
            session.delete(f"{path}/{name}")
        elif facts['type'] == 'dir':
            ftp_dir_remove(session, f"{path}/{name}")

    try:
        session.rmd(path)
        return True
    except ftplib.Error as e:
        print_log(VERBOSE, f"ERROR remove {path}")
        return False


def ftp_backup_rotate(session, hostname: str, days_rotate: int, backup_stamp: int):
    print(session)
    print(hostname)
    seconds_minus = days_rotate * 86400
    print(seconds_minus)

    dirs_arr = []
    for (name, facts) in session.mlsd(path=hostname)
        if name in ['.', '..']:
            continue
        elif facts['type'] == 'dir':
            dirs_arr.append(name)

    print(dirs_arr)

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

BACKUP_STAMP = int(time.time())
BACKUP_DIR = f"{add_slash(CONFIG_DATA['tmp_dir'])}{str(BACKUP_STAMP)}/"

for item_arch in CONFIG_DATA['backup']:
    OUT_FILE = f"{BACKUP_DIR}{item_arch['name']}.tar.gz"
    if not create_dir(BACKUP_DIR):
        sys.exit(1)
    tar_cmd = tar_command(item_arch['path'], item_arch['excludes'], OUT_FILE)
    run_tar = subprocess.run(tar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if run_tar.returncode != 0:
        print_log(VERBOSE, f"ERROR in {item_arch['path']}")
        print_log(VERBOSE, f"ERROR {run_tar.stderr}")
        sys.exit(1)
    else:
        print_log(VERBOSE, f"INFO archive successful {OUT_FILE}")
        ftp_upload(OUT_FILE,
                   HOSTNAME,
                   BACKUP_STAMP,
                   ftp_session(CONFIG_DATA['ftp_login']['ftp_host'],
                               CONFIG_DATA['ftp_login']['ftp_user'],
                               CONFIG_DATA['ftp_login']['ftp_pass']))

ftp_backup_rotate(ftp_session(CONFIG_DATA['ftp_login']['ftp_host'],
                              CONFIG_DATA['ftp_login']['ftp_user'],
                              CONFIG_DATA['ftp_login']['ftp_pass']),
                  HOSTNAME,
                  CONFIG_DATA['backup_rotate'])

if process_nagios_file(NAGIOS_FILE):
    os.remove(PID_FILE)
else:
    print_log(VERBOSE, f"ERROR could not write to {NAGIOS_FILE}")
