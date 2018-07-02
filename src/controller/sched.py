# -------------------------------------------------------------
# sched.py - analyses scheduling performance
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Analyses scheduling performance.

Handles interaction of the controller with the interface modules.

"""

import src.interface.perf as perf


def collect_all(time, filename):
    """
    Uses perf module to collect scheduling data

    :param time:
        The time in seconds for which to collect the data.
    :param filename:
        The location where the file is stored.

    """
    perf.collect_sched_all(time)
    perf.get_sched_data(filename)
