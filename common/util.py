# -------------------------------------------------------------
# util.py - various utilities
# July 2018 - Andrei Diaconu, Hrutvik Kanabar
# -------------------------------------------------------------

"""Various utilities"""

import platform
import re
import common.exceptions as exceptions


def check_kernel_version(required_kernel):
    """
    Decorator function that checks if the target kernel supports the interface

    :param: required_kernel:
        The required kernel for the interface
    :return: returns True is the interface is supported, false otherwise

    """
    def wrap(f):
        def wrapped_check(*args):
            target_kernel = platform.release()
            delimited_rk = re.split('\.|-', required_kernel)
            delimited_tk = re.split('\.|-', target_kernel)
            if delimited_tk[0:3] < delimited_rk[0:3]:
                raise exceptions.NotSupportedException("Kernel not supported",
                                                       required_kernel)
            return f(*args)
        return wrapped_check
    return wrap


def Override(superclass):
    def overrider(method):
        assert(method.__name__ in dir(superclass))
        return method
    return overrider
