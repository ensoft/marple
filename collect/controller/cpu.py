# -------------------------------------------------------------
# cpu.py - analyses scheduling performance
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Analyses scheduling performance.

Handles interaction of the controller with the interface modules.

"""

import collect.interface.perf as perf


def collect(time):
    """
    Uses perf module to collect scheduling data

    :param time:
        The time in seconds for which to collect the data.

    :return:
        A generator of scheduling event objects.

    """
    perf.collect_sched(time)
    return perf.get_sched_data()
