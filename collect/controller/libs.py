# -------------------------------------------------------------
# libs.py - analyses library and other file load times
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Analyses library and other file load times.

Handles interaction of the controller with the interface modules and writes
    the converted data to file.

"""
__all__ = ["collect_and_store"]

import logging

logger = logging.getLogger("collect.controller.lib")
logger.setLevel(logging.DEBUG)


def collect_and_store(time, filename):
    """
    Uses one of the interface modules to collect library load time data.

    :param time:
        The time in seconds for which to collect the data.
    :param filename:
        The name of the file in which to store the output.
    """
    # @Choose interface and implement
    logger.info("Enter libs collect_and_store function. Recording library data "
                "for %s seconds. Output filename: %s", time, filename)
    raise NotImplementedError("libs")
