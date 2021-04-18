import argparse
import logging


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', type=str, required=True, help="Path to config file", dest='config')
    parser.add_argument('-v', '--verbose', required=False, action='store_true', dest='verbose')

    args_cmd = parser.parse_args()
    config_file = args_cmd.config
    verbose = args_cmd.verbose

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')

    file_handler = logging.FileHandler('sample.log')
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


if __name__ == "__main__":
    main()
