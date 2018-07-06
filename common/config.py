# -------------------------------------------------------------
# config.py - configuration of constants and defaults
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Configuration of constants and defaults

Provides functions returning the standard value for constants
used mainly in data collection

"""

__all__ = ["is_blocking", "get_default_time", "get_default_frequency"]

# Constants (temporary: will be in a file later)
_BLOCKING = True

_TIME = 10

_FREQUENCY = 99
# The default frequency is 99 rather than 100 to avoid
# recording in lockstep with some periodic activity.


def is_blocking():
    """
    Return config value defining whether caller should block

    The calling module function, e.g. perf.collect can either
    return while data is still being collected
    or wait for the collection to finish.
    This function is called to tell it which of these it should do.

    :return:
        A boolean value that specifies whether to block
    """
    return _BLOCKING


def get_default_time():
    """
    Return the default time for which to collect data

    :return:
        The default time in seconds

    """
    return _TIME


def get_default_frequency():
    """
    Return the default frequency

    :return:
        The default frequency in Hertz

    """
    return _FREQUENCY
