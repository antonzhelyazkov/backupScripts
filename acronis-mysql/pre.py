#!/usr/bin/env python3

LOG_FILE = "/var/log/mysql_backup.log"
DEF_EXTRA_FILE = "/root/my.cnf"


def main():
    with open(LOG_FILE, "w") as log_file:
        log_file.write("test1")


if __name__ == "__main__":
    main()
