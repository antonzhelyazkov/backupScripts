import argparse
import json
import logging
import os
import sys

from logdecorator import log_on_start, log_on_end, log_on_error, log_exception


def add_slash(directory):
    if not directory.endswith("/"):
        dir_return = directory + "/"
    else:
        dir_return = directory
    return dir_return


@log_on_start
@log_on_error
@log_on_end
def display_info(log_file, qwe):
    pass


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', type=str, required=True, help="Path to config file", dest='config')

    args_cmd = parser.parse_args()
    config_file = args_cmd.config
    config_open = open(config_file, encoding='utf-8')
    config_data = json.load(config_open)
    script_name = os.path.basename(sys.argv[0]).split(".")
    log_file = f"{add_slash(config_data['log_dir'])}{script_name[0]}.log"

    logging.basicConfig(level=logging.INFO)

    display_info(log_file, 1232)


if __name__ == "__main__":
    main()
