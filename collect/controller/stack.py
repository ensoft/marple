# -------------------------------------------------------------
# cpu.py - analyses scheduling performance
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Analyses scheduling performance.

Handles interaction of the controller with the interface modules.

"""

from ...common import config
from ..interface import perf

# COLLECTION_FREQUENCY - int constant specifying the default sample frequency
_COLLECTION_FREQUENCY = 99


def collect(time):
    """
    Uses perf module to collect call stack tracing data

    :param time:
        The time in seconds for which to collect the data.
    :param frequency:
        The frequency in Hertz with which to collect the data.

    :return:
        A generator of stack event objects.

    """

    # Use default frequency for data collection
    frequency = config.get_default_frequency() if \
        config.get_default_frequency() is not None else _COLLECTION_FREQUENCY

    perf.collect(time, frequency)
    _filename = perf.get_stack_data()
    return perf.parse(_filename)
