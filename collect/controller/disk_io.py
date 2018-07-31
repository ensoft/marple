# -------------------------------------------------------------
# disk_io.py - analyses disk I/O efficiency
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Analyses disk I/O efficiency

Handles interaction of the controller with the interface modules and writes
    the converted data to file.

"""
__all__ = ["collect_and_store"]

import logging

from ..converter import main as converter
from ..interface import perf
from ..interface import iosnoop

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

    if latency:
        iosnoop.collect_disk(time, filename)
    else:
        # Collect and format disk data using perf
        perf.collect_disk(time)
        disk_data_formatted = perf.get_disk_data()

        # Create file
        converter.create_disk_event_data(disk_data_formatted, filename)
