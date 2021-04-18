import argparse
import json
import logging
import os
import sys
import time


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

    try:
        f = open(nagios_file, "w")
        f.write(str(int(time.time())))
        f.close()
        os.remove(pid_file)
    except IOError as e:
        logger.exception(f"##### {e}")


if __name__ == "__main__":
    main()
