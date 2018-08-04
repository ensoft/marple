# -------------------------------------------------------------
# mem.py - analyses memory allocation and deallocation
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

"""
Analyses memory allocation and deallocation

Handles interaction of the controller with the interface modules and writes
    the converted data to file.

"""
__all__ = ["collect_and_store"]

import logging

from collect.writer import write
from collect.interface import perf

logger = logging.getLogger("collect.controller.mem")
logger.setLevel(logging.DEBUG)


def collect_and_store(time, filename):
    """
    Uses one of the interface modules to collect memory data.

    :param time:
        The time in seconds for which to collect the data.
    :param filename:
        The name of the file in which to store the output.

    """

    logger.info("Enter mem collect_and_store function. Recording memory data "
                "for %s seconds. Output filename: %s", time, filename)

    # Collect and write data using perf
    collecter = perf.Memory(time)
    collecter.collect()
    data = collecter.get()

    # Write data
    writer = write.Writer(data, filename)
    writer.write()