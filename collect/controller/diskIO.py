# -------------------------------------------------------------
# diskIO.py - analyses disk I/O efficiency
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Analyses disk I/O efficiency

Handles interaction of the controller with the interface modules and writes
    the converted data to file.

"""
__all__ = ["collect_and_store"]

import logging

logger = logging.getLogger("collect.controller.diskIO")
logger.setLevel(logging.DEBUG)


def collect_and_store(time, filename):
    """
    Uses one of the interface modules to collect disk I/O data.

    :param time:
        The time in seconds for which to collect the data.
    :param filename:
        The name of the file in which to store the output.
    """
    # @Choose interface and implement
    logger.info("Enter diskIO collect_and_store function. Recording disk I/O "
                "data for {} seconds. Output filename: {}".format(time,
                                                                  filename))
    raise NotImplementedError("diskIO")
