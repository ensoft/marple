# -------------------------------------------------------------
# stack.py - does stack tracing
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Does stack tracing.

Handles interaction of the controller with the interface modules and writes 
    the converted data to file.

"""
__all__ = ["collect_and_store"]

import logging

from common import config
from ..converter import main as converter
from ..interface import perf

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

    # Use default frequency for data collection
    frequency = config.get_default_frequency() if \
        config.get_default_frequency() is not None else _COLLECTION_FREQUENCY

    # Collect raw data using perf
    perf.collect(time, frequency)

    # Collapse the stack, create stack object generator
    stack_data_formatted = perf.get_stack_data()

    # Create file from the folded stack objects
    converter.create_stack_data(generator=stack_data_formatted, 
                                filename=filename)
