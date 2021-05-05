import argparse
import json
import logging
import os
import sys


class PrintLog:
    def __init__(self, log_file):
        self.log_file = log_file

    def log(self, verbose: bool, msg: str):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        if verbose:
            logger.addHandler(file_handler)
            logger.addHandler(stream_handler)
            logger.info(msg)
        else:
            logger.addHandler(file_handler)
            logger.info(msg)


def add_slash(directory):
    if not directory.endswith("/"):
        dir_return = directory + "/"
    else:
        dir_return = directory
    return dir_return


def test_log(print_log):
    print_log(f"test_log wqewerwer")


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

    print_log = PrintLog(log_file)
    print_log.log(verbose, f"test msg")

    test_log(lambda msg: print_log.log(verbose, msg))

if __name__ == "__main__":
    main()
