import argparse
import json
import logging
import os
import sys


def add_slash(directory):
    if not directory.endswith("/"):
        dir_return = directory + "/"
    else:
        dir_return = directory
    return dir_return


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', type=str, required=True, help="Path to config file", dest='config')
    parser.add_argument('-v', '--verbose', required=False, action='store_true', dest='verbose')

    args_cmd = parser.parse_args()
    config_file = args_cmd.config
    verbose = args_cmd.verbose

    config_open = open(config_file, encoding='utf-8')
    config_data = json.load(config_open)
    log_file_name = os.path.basename(sys.argv[0]).split(".")[0]
    log_file = f"{add_slash(config_data['log_dir'])}{log_file_name}.log"
    print(log_file)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


if __name__ == "__main__":
    main()
