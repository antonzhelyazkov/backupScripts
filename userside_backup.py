import argparse
import ftplib
import json
import logging
import os
import socket
import subprocess
import sys
import time

HOSTNAME = socket.gethostname().split(".")[0]


class PidFileExists(Exception):
    pass


class FtpConn:
    def __init__(self, ftp_host, ftp_user, ftp_pass):
        self.ftp_host = ftp_host
        self.ftp_user = ftp_user
        self.ftp_pass = ftp_pass

    def ftp_conn(self, local_logger):
        local_logger.info("ftp_conn")
        try:
            session = ftplib.FTP(self.ftp_host, self.ftp_user, self.ftp_pass, timeout=3)
            return session
        except ftplib.Error as e:
            raise ftplib.Error(e)
        except socket.timeout as to:
            raise socket.timeout()


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


def tar_command(arch_dir: str, excludes: list, out_file: str) -> list:
    tar_arr = ["/usr/bin/tar", "-cf", out_file, "-I", "pigz"]
    if len(excludes) > 0:
        for item_exclude in excludes:
            tar_arr.extend([f"--exclude={remove_slash(item_exclude)}"])

    tar_arr.append(arch_dir)

    return tar_arr


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', type=str, required=True, help="Path to config file", dest='config')
    parser.add_argument('-v', '--verbose', required=False, action='store_true', dest='verbose')

    args_cmd = parser.parse_args()
    config_file = args_cmd.config
    verbose = args_cmd.verbose

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

    if verbose:
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    else:
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

    backup_stamp = int(time.time())
    backup_dir = f"{add_slash(config_data['tmp_dir'])}{str(backup_stamp)}/"
    backup_ftp_dir = f"{HOSTNAME}-reoback"

    ftp_process = FtpConn(config_data['ftp_login']['ftp_host'],
                       config_data['ftp_login']['ftp_user'],
                       config_data['ftp_login']['ftp_pass'])

    for item_arch in config_data['backup']:
        out_file = f"{backup_dir}{item_arch['name']}.tar.gz"
        logger.info(f"out file {out_file}")
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
            ftp_process.ftp_conn(logger)

    try:
        f = open(nagios_file, "w")
        f.write(str(int(time.time())))
        f.close()
        os.remove(pid_file)
    except IOError as e:
        logger.exception(f"##### {e}")


if __name__ == "__main__":
    main()
