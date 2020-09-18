import os
import errno
import time

from gousto_test.utils.logging import get_logger

logger = get_logger()


def time_function(logger):
    """A decorator function to time how long a function takes to run"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            logger.debug(
                "Function {} completed in {} seconds".format(
                    func.__name__, round(time.time() - start_time, 4)
                )
            )
            return result

        return wrapper

    return decorator


def mkdir_p(file_path):
    """Create a file path if one does not exist"""
    try:
        os.makedirs(file_path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(file_path):
            pass
        else:
            print("OS error: {}".format(exc))
            raise


def safe_open(dir_path, type):
    """Opens files safely (if the directory does not exist, it is created).
    Taken from https://stackoverflow.com/a/600612/119527
    """
    # Open "path" for writing, creating any parent directories as needed.
    mkdir_p(os.path.dirname(dir_path))
    return open(dir_path, type)
