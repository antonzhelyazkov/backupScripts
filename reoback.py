import argparse
import ftplib
import json
import logging
import os
import re
import socket
import subprocess
import sys
import time


HOSTNAME = socket.gethostname().split(".")[0]


class PidFileExists(Exception):
    pass


class DirectoryMissing(Exception):
    pass


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
        return dir_return
    else:
        return directory


def process_pid_file(pid_f: str) -> bool:
    if os.path.isfile(pid_f):
        raise PidFileExists
    else:
        try:
            f = open(pid_f, "w")
            f.write(str(os.getpid()))
            f.close()
            return True
        except IOError as e:
            raise IOError(e)


def check_dirs_exist(dirs: list):
    err_dirs = []
    for item in dirs:
        if not os.path.isdir(item):
            err_dirs.append(item)

    if len(err_dirs) > 0:
        raise DirectoryMissing(err_dirs)


def tar_command(arch_dir: str, excludes: list, out_file: str) -> list:
    tar_arr = ["/usr/bin/tar", "-cf", out_file, "-I", "pigz"]
    if len(excludes) > 0:
        for item_exclude in excludes:
            tar_arr.extend([f"--exclude={remove_slash(item_exclude)}"])

    tar_arr.append(arch_dir)

    return tar_arr


def ftp_session(ftp_host: str, ftp_user: str, ftp_pass: str):
    try:
        session = ftplib.FTP(ftp_host, ftp_user, ftp_pass, timeout=3)
        return session
    except ftplib.Error as e:
        raise ftplib.Error(e)
    except socket.timeout as to:
        print(f"############ {to}")
        raise socket.timeout()


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
        return False


def ftp_backup_rotate(session, remote_dir: str, days_rotate: int, backup_stamp: int) -> bool:
    seconds_minus = days_rotate * 86400
    stamp_before = backup_stamp - seconds_minus

    dirs_arr = []
    for (name, facts) in session.mlsd(path=remote_dir):
        if name in ['.', '..']:
            continue
        elif facts['type'] == 'dir' and re.match("^\d{10}$", name):
            dirs_arr.append(name)

    for item in dirs_arr:
        if int(item) < stamp_before:
            dir_to_remove = f"{remote_dir}/{item}"
            if not ftp_dir_remove(session, dir_to_remove):
                return False

    return True


def ftp_upload(file: str, remote_dir: str, backup_stamp: int, session) -> bool:
    f_name = os.path.basename(file)
    dir_stamp = f"{remote_dir}/{backup_stamp}"

    for directory in (remote_dir, dir_stamp):
        try:
            session.mkd(directory)
        except ftplib.error_perm as perm:
            pass
        except ftplib.Error as e:
            raise ftplib.Error(e)

    file_fh = open(file, "rb")
    try:
        session.storbinary(f"STOR {dir_stamp}/{f_name}", file_fh, blocksize=10000000)
        return True
    except ftplib.Error as e:
        return False
    finally:
        file_fh.close()
        session.close()


def remove_local_dir(directory: str) -> bool:
    files_arr = os.listdir(directory)
    for item in files_arr:
        file_to_remove = f"{directory}/{item}"
        try:
            os.remove(file_to_remove)
        except OSError as e:
            return False

    try:
        os.rmdir(directory)
        return True
    except OSError as e:
        return False


def remove_local_backups(days_rotate: int, backup_dir: str, backup_stamp: int) -> bool:
    seconds_minus = days_rotate * 86400
    stamp_before = backup_stamp - seconds_minus

    dirs_arr = os.listdir(backup_dir)
    dirs_to_process = []
    for item in dirs_arr:
        if re.match("^\d{10}$", item):
            dirs_to_process.append(item)

    for item in dirs_to_process:
        if int(item) < stamp_before:
            dir_to_remove = f"{backup_dir}{item}"
            if not remove_local_dir(dir_to_remove):
                return False

    return True


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', type=str, required=True, help="Path to config file", dest='config')

    args_cmd = parser.parse_args()
    config_file = args_cmd.config

    config_open = open(config_file, encoding='utf-8')
    config_data = json.load(config_open)
    script_name = os.path.basename(sys.argv[0]).split(".")
    log_file = f"{add_slash(config_data['log_dir'])}{script_name[0]}.log"

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    pid_file = f"{add_slash(config_data['pid_file_path'])}{script_name[0]}.pid"
    nagios_file = f"{add_slash(config_data['pid_file_path'])}{script_name[0]}.nagios"
    try:
        process_pid_file(pid_file)
    except PidFileExists:
        logger.info(f"INFO pid file {pid_file} exists")
        sys.exit(1)
    except OSError as e:
        logger.exception(f"#### {e}")

    dirs_exists = [config_data['tmp_dir'], config_data['log_dir'], config_data['pid_file_path']]
    dirs_to_archive = []
    for item_dir in config_data['backup']:
        dirs_exists.append(item_dir['path'])
        dirs_to_archive.append(item_dir['path'])
    try:
        check_dirs_exist(dirs_exists)
    except DirectoryMissing as e:
        logger.exception(f"#### {e}")

    if HOSTNAME is None or HOSTNAME == '':
        logger.info(f"ERROR in hostname {HOSTNAME}")
        sys.exit(1)

    backup_stamp = int(time.time())
    backup_dir = f"{add_slash(config_data['tmp_dir'])}{str(backup_stamp)}/"
    backup_ftp_dir = f"{HOSTNAME}-reoback"

    for item_arch in config_data['backup']:
        out_file = f"{backup_dir}{item_arch['name']}.tar.gz"
        try:
            os.makedirs(backup_dir, exist_ok=True)
        except OSError as e:
            logger.exception(f"#### {e}")
            sys.exit(1)
        tar_cmd = tar_command(item_arch['path'], item_arch['excludes'], out_file)
        run_tar = subprocess.run(tar_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if run_tar.returncode != 0:
            logger.info(f"ERROR in {item_arch['path']}")
            logger.info(f"ERROR in {run_tar.stderr}")
            sys.exit(1)
        else:
            logger.info(f"INFO archive successful {out_file}")
            ftp_upload(out_file,
                       backup_ftp_dir,
                       backup_stamp,
                       ftp_session(config_data['ftp_login']['ftp_host'],
                                   config_data['ftp_login']['ftp_user'],
                                   config_data['ftp_login']['ftp_pass']))

    if ftp_backup_rotate(ftp_session(config_data['ftp_login']['ftp_host'],
                                     config_data['ftp_login']['ftp_user'],
                                     config_data['ftp_login']['ftp_pass']),
                         backup_ftp_dir,
                         config_data['ftp_backup_rotate'],
                         backup_stamp):
        logger.info(f"INFO all backups older than {config_data['ftp_backup_rotate']} are removed")
    else:
        logger.info(f"ERROR in remove FTP older backups")
        sys.exit(1)

    if not remove_local_backups(config_data['local_backup_rotate'],
                                add_slash(config_data['tmp_dir']),
                                backup_stamp):
        sys.exit(1)

    try:
        f = open(nagios_file, "w")
        f.write(str(int(time.time())))
        f.close()
        os.remove(pid_file)
    except IOError as e:
        logger.exception(f"##### {e}")


if __name__ == "__main__":
    main()
