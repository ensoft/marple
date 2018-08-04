# -------------------------------------------------------------
# stack.py - does stack tracing
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

"""
Does stack tracing.

Handles interaction of the controller with the interface modules and writes
    the converted data to file.

"""
__all__ = ["collect_and_store"]

import logging

from common import config
from collect.writer import write
from collect.interface import perf

# COLLECTION_FREQUENCY - int constant specifying the default sample frequency
_COLLECTION_FREQUENCY = 99

logger = logging.getLogger("collect.controller.stack")
logger.setLevel(logging.DEBUG)


def collect_and_store(time, filename):
    """
    Uses interface modules to collect call stack tracing data.

    :param time:
        The time in seconds for which to collect the data.
    :param filename:
        The name of the file in which to store the output.

    """

    logger.info("Enter stack collect_and_store function. Recording stack data "
                "for %s seconds. Output filename: %s", time, filename)

    # Use default frequency for data collection
    frequency = config.get_default_frequency() if \
        config.get_default_frequency() is not None else _COLLECTION_FREQUENCY

    options = perf.Stack.Options(frequency, "-a")

    # Collect and write data using perf
    collecter = perf.Stack(time, options)
    collecter.collect()
    data = collecter.get()

    # Write data
    writer = write.Writer(data, filename)
    writer.write()
