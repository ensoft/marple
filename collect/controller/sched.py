# -------------------------------------------------------------
# sched.py - analyses scheduling performance
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Analyses scheduling performance.

Handles interaction of the controller with the interface modules.

"""

import collect.interface.perf as perf


def collect_all(time):
    """
    Uses perf module to collect scheduling data

    :param time:
        The time in seconds for which to collect the data.

    """
    perf.collect_sched(time)
    perf.get_sched_data()
