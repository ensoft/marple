# -------------------------------------------------------------
# disk_io.py - analyses disk I/O efficiency
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

"""
Analyses disk I/O efficiency

Handles interaction of the controller with the interface modules and writes
    the converted data to file.

"""
__all__ = ["collect_and_store"]

import logging

from collect.writer import write
from collect.interface import (
    perf,
    iosnoop
)

logger = logging.getLogger("collect.controller.diskIO")
logger.setLevel(logging.DEBUG)


def collect_and_store(time, filename, latency=True):
    """
    Uses one of the interface modules to collect disk I/O data.

    :param time:
        The time in seconds for which to collect the data.
    :param filename:
        The name of the file in which to store the output.

    """
    # @Choose interface and implement
    logger.info("Enter diskIO collect_and_store function. Recording disk I/O "
                "data for %s seconds. Output filename: %s", time, filename)

    # Select collecter
    if latency:
        collecter = iosnoop.DiskLatency
    else:
        collecter = perf.DiskBlockRequests

    # Create data collecter object
    collecter_obj = collecter(time)

    # Collect data
    data = collecter_obj.collect()

    # Write data
    writer = write.Writer(data, filename)
    writer.write()