# -------------------------------------------------------------
# ipc.py - analyses inter-process communication efficiency
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Analyses inter-process communication efficiency.

Handles interaction of the controller with the interface modules and writes
    the converted data to file.

"""
__all__ = ["collect_and_store"]

import logging

logger = logging.getLogger("collect.controller.ipc")
logger.setLevel(logging.DEBUG)


def collect_and_store(time, filename):
    """
    Uses one of the interface modules to collect ipc data.

    :param time:
        The time in seconds for which to collect the data.
    :param filename:
        The name of the file in which to store the output.
    """
    # @Choose interface and implement
    logger.info("Enter ipc collect_and_store function. Recording ipc data for "
                "%s seconds. Output filename: %s", time, filename)
    raise NotImplementedError("ipc")
