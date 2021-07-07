#!/usr/bin/env python3
import argparse

LOG_FILE = "/var/log/mysql_backup.log"
DEF_EXTRA_FILE = "/root/my.cnf"


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--database', type=str, required=True, help="Path to config file", dest='database')

    args_cmd = parser.parse_args()
    database = args_cmd.database

    with open(LOG_FILE, "w") as log_file:
        log_file.write("test11212")


if __name__ == "__main__":
    main()
