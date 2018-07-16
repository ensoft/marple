# -------------------------------------------------------------
# converter/main.py - Saves data objects into a file.
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Saves data objects into a file.

Gets the data that was collected by an interface module and converted into
formatted objects and writes them into a file that was provided by the user.

"""
__all__ = ["create_stack_data", "create_cpu_event_data"]

import logging
import collections

logger = logging.getLogger("converter.main")
logger.setLevel(logging.DEBUG)


def create_stack_data(stack_events, filename):
    """
    Count, sort and saves the stack data from the generator into a file.

    :param stack_events:
        An iterable of :class:`StackEvent` objects
    :param filename:
        The name of the file into which to store the output.

    """
    logger.info("Enter create_stack_data")

    logger.info("Counting number of stack occurrences")
    # Count stack occurrences
    cnt = collections.Counter(stack_events)

    logger.info("Sort stacks")
    # @Sort by keys (recursively by ascending index)
    pass

    logger.info("Writing folded stacks to file")
    # Write data to file
    # Format: eg. perf;[unknown];_perf_event_enable;event_function_call 24
    with open(filename, "w") as out:
        for key, val in cnt.items():
            out.write(";".join(key) + " {}\n".format(val))

    logger.info("Done.")


def create_cpu_event_data(generator, filename):
    """
    Saves the event data from the generator into a file.

    :param generator:
        The generator of SchedEvent objects
    :param filename:
        The name of the file into which to store the output.

    """
    # @Write to file
    with open(filename, "w") as out:
        for event in generator:
            out.write(str(event) + "\n")
