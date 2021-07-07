#!/usr/bin/env python3
import argparse
import logging
import os
import subprocess
import sys

LOG_FILE = "/var/log/mysql_backup.log"
DIR_TO_BACKUP = "/var/tmp/mysql_backup"


def add_slash(directory):
    if not directory.endswith("/"):
        dir_return = directory + "/"
    else:
        dir_return = directory
    return dir_return


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--database', type=str, required=True, help="Path to config file", dest='database')

    args_cmd = parser.parse_args()
    database = args_cmd.database

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if not os.path.isdir(DIR_TO_BACKUP):
        try:
            os.makedirs(DIR_TO_BACKUP)
            logger.info("INFO directory {0} created".format(DIR_TO_BACKUP))
        except OSError as e:
            logger.info("ERROR could not create directory {0}".format(e))
            sys.exit(1)
    else:
        logger.info("INFO directory exists {0}".format(DIR_TO_BACKUP))

    logger.info(database)

    backup_destination = "{0}{1}.sql".format(add_slash(DIR_TO_BACKUP), database)
    dump_cmd = ['mysqldump', '-B', database, '|', 'pigz', '>', backup_destination]
    run_mysqldump = subprocess.run(dump_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if run_mysqldump.returncode != 0:
        logger.info("ERROR in {0}".format(run_mysqldump.stderr))
        sys.exit(1)


if __name__ == "__main__":
    main()
