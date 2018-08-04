# -------------------------------------------------------------
# cpu.py - analyses scheduling performance
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

"""
Analyses scheduling performance.

Handles interaction of the controller with the interface modules and writes
    the converted data to file.

"""
__all__ = ["sched_collect_and_store"]

import logging

from collect.writer import write
from collect.interface import perf

logger = logging.getLogger("collect.controller.cpu")
logger.setLevel(logging.DEBUG)


def sched_collect_and_store(time, filename):
    """
    Uses interface modules to collect cpu scheduling data.

    :param time:
        The time in seconds for which to collect the data.
    :param filename:
        The name of the file in which to store the output.

    """

    logger.info("Enter sched_collect_and_record. Recording cpu scheduling data "
                "for %s seconds. Output filename: %s", time, filename)

    # Collect relevant data using perf
    collecter = perf.Scheduling(time)
    collecter.collect()

    # Create SchedEvent object generator
    sched_data = collecter.get()

    # Create file from the SchedEvent objects
    write.create_cpu_event_data_cpel(sched_data, filename)
