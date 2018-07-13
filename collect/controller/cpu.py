# -------------------------------------------------------------
# cpu.py - analyses scheduling performance
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Analyses scheduling performance.

Handles interaction of the controller with the interface modules and writes
    the converted data to file.

"""

__all__ = ["sched_collect_and_store"]

import logging

from ..converter import main as converter
from ..interface import perf

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
                "for {} seconds. Output filename: {}".format(time, filename))

    # Collect relevant data using perf
    perf.collect_sched(time)

    # Create SchedEvent object generator
    sched_data_formatted = perf.get_sched_data()

    # Create file from the SchedEvent objects
    converter.create_cpu_event_data(generator=sched_data_formatted,
                                    filename=filename)
