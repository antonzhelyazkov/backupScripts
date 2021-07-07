#!/usr/bin/env python3
import argparse

LOG_FILE = "/var/log/mysql_backup.log"
DEF_EXTRA_FILE = "/root/my.cnf"


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', type=str, required=False, help="Path to config file", dest='config')
    parser.add_argument('-v', '--verbose', required=False, action='store_true', dest='verbose')

    args_cmd = parser.parse_args()
    config_file = args_cmd.config
    verbose = args_cmd.verbose

    print(verbose)

    with open(LOG_FILE, "w") as log_file:
        log_file.write("test1")


if __name__ == "__main__":
    main()
