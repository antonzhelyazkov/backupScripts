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


class ErrFtpRotate(Exception):
    pass


class SocketTimeout(Exception):
    pass


class FtpConn:
    def __init__(self, ftp_host, ftp_user, ftp_pass):
        self.ftp_host = ftp_host
        self.ftp_user = ftp_user
        self.ftp_pass = ftp_pass

    def ftp_conn(self, local_logger):
        local_logger.info("try ftp_conn")
        try:
            session = ftplib.FTP(self.ftp_host, self.ftp_user, self.ftp_pass, timeout=3)
            local_logger.info("ftp conn OK")
            return session
        except ftplib.Error as e:
            local_logger.exception(e)
            raise ftplib.Error(e)
        except socket.timeout as to:
            local_logger.exception(to)
            raise socket.timeout()
        except OSError as oe:
            local_logger.exception(oe)
            raise OSError

    def ftp_upload(self, file: str, remote_dir: str, backup_stamp: int, session, local_logger) -> bool:
        f_name = os.path.basename(file)
        dir_stamp = f"{remote_dir}/{backup_stamp}"

        for directory in (remote_dir, dir_stamp):
            try:
                session.mkd(directory)
            except ftplib.error_perm as perm:
                pass
            except ftplib.Error as e:
                local_logger.exception(e)
                raise ftplib.Error(e)

        file_fh = open(file, "rb")
        try:
            session.storbinary(f"STOR {dir_stamp}/{f_name}", file_fh, blocksize=10000000)
            local_logger.info(f"file {dir_stamp}/{f_name} uploaded")
            return True
        except ftplib.Error as e:
            return False
        finally:
            file_fh.close()

    def ftp_backup_rotate(self, remote_dir: str, days_rotate: int, backup_stamp: int,
                          local_logger, session):
        local_logger.info(f"start rotate")
        seconds_minus = days_rotate * 0
        stamp_before = backup_stamp - seconds_minus

        try:
            local_logger.info(f"try mlsd")
            ftp_dirs = session.mlsd(path=remote_dir)
        except ftplib.Error as err_rotate:
            local_logger.info(f"ERROR mlsd")
            raise ErrFtpRotate(err_rotate)
        except socket.timeout as st:
            local_logger.info(f"socket {st}")
            raise SocketTimeout(st)

        local_logger.info(f"{ftp_dirs}")
        dirs_arr = []
        for (name, facts) in ftp_dirs:
            if name in ['.', '..']:
                continue
            elif facts['type'] == 'dir' and re.match("^\d{10}$", name):
                dirs_arr.append(name)

        for item in dirs_arr:
            if int(item) < stamp_before:
                dir_to_remove = f"{remote_dir}/{item}"
                self.ftp_dir_remove(session, dir_to_remove, local_logger)

    def ftp_dir_remove(self, session, path_q: str, local_logger):
        mlsd_facts = session.mlsd(path=path_q)
        for (name, facts) in mlsd_facts:
            if name in ['.', '..']:
                continue
            elif facts['type'] == 'file':
                try:
                    local_logger.info(f"trying to delete {path_q}/{name}")
                    session.delete(f"{path_q}/{name}")
                except ftplib.Error as e:
                    local_logger.info(f"ERROR {e}")
                except socket.timeout as to:
                    local_logger.info(f"ERROR {to}")
            elif facts['type'] == 'dir':
                self.ftp_dir_remove(session, f"{path_q}/{name}", local_logger)

        try:
            session.rmd(path_q)
        except ftplib.Error as e:
            raise ftplib.Error(e)


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
    tar_arr = ["tar", "-cf", out_file, "-I", "pigz"]
    if len(excludes) > 0:
        for item_exclude in excludes:
            tar_arr.extend([f"--exclude={remove_slash(item_exclude)}"])

    tar_arr.append(arch_dir)

    return tar_arr


def pg_archive(dst_dir: str):
    pg_dump_cmd = ['sudo', '-u', 'postgres', 'pg_dump', '--no-acl', '-Fp', '-Z', '5', 'userside']
    dst_file = f"{dst_dir}userside.sql.gz"
    print(dst_file)
    with open(dst_file, "wb") as outfile:
        subprocess.run(pg_dump_cmd, stdout=outfile)


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
            ftp_open_upload = ftp_process.ftp_conn(logger)
            ftp_process.ftp_upload(out_file,
                                   backup_ftp_dir,
                                   backup_stamp,
                                   ftp_open_upload,
                                   logger)
            ftp_open_upload.quit()

    pg_archive(backup_dir)

    ftp_open_rotate = ftp_process.ftp_conn(logger)
    try:
        ftp_process.ftp_backup_rotate(backup_ftp_dir,
                                      config_data['ftp_backup_rotate'],
                                      backup_stamp,
                                      logger,
                                      ftp_open_rotate)
    except ErrFtpRotate as err_ftp:
        logger.exception(err_ftp)
        sys.exit(1)
    except SocketTimeout as so_t:
        logger.exception(so_t)
        sys.exit(1)
    ftp_open_rotate.quit()

    try:
        f = open(nagios_file, "w")
        f.write(str(int(time.time())))
        f.close()
        os.remove(pid_file)
    except IOError as e:
        logger.exception(f"##### {e}")


if __name__ == "__main__":
    main()
