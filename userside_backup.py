import argparse


def my_logger(orig_func):
    import logging
    logging.basicConfig(filename=f'{orig_func.__name__}', level=logging.INFO)

    def wrapper(*args, **kwargs):
        logging.info(f'Ran with args: {args}, and kwargs: {kwargs}')
        return orig_func(*args, **kwargs)

    return wrapper


@my_logger
def display_info(name, age):
    pass


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--config', type=str, required=True, help="Path to config file", dest='config')

    args_cmd = parser.parse_args()
    config_file = args_cmd.config

    display_info(config_file, 1232)


if __name__ == "__main__":
    main()
