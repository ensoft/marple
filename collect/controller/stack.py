# -------------------------------------------------------------
# cpu.py - analyses scheduling performance
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Analyses scheduling performance.

Handles interaction of the controller with the interface modules.

"""

import collect.interface.perf as perf


def collect(time, frequency):
    """
    Uses perf module to collect call stack tracing data

    :param time:
        The time in seconds for which to collect the data.
    :param frequency:
        The frequency in Hertz with which to collect the data.

    :return:
        A generator of stack event objects.

    """
    perf.collect(time, frequency)
    _filename = perf.get_stack_data()

    return perf.parse(_filename)
