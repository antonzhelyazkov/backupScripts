#!/usr/bin/env python3
import argparse
import logging
import os
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


if __name__ == "__main__":
    main()
