
def my_logger(orig_func):
    import logging
    logging.basicConfig(filename=f'{orig_func.__name__}', level=logging.INFO)

    def wrapper(*args, **kwargs):
        logging.info(f'Ran with args: {args}, and kwargs: {kwargs}')
        return orig_func(*args, **kwargs)

    return wrapper


@my_logger
def display_info(name, age):
    # if True:
    #     print('display_info ran with arguments ({}, {})'.format(name, age))
    pass


def main():

    display_info("qweqwe", 1232)


if __name__ == "__main__":
    main()
