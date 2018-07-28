# -------------------------------------------------------------
# converter/main.py - Saves data objects into a file.
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

"""
Saves data objects into a file.

Gets the data that was collected by an interface module and converted into
formatted objects and writes them into a file that was provided by the user.

"""
__all__ = ["create_stack_data_unsorted", "create_cpu_event_data", "create_mem_event_data"]

import collections
import logging
import struct
from datetime import datetime

logger = logging.getLogger("converter.main")
logger.setLevel(logging.DEBUG)


def create_stack_data_unsorted(stack_events, filename):
    """
    Count, sort and saves the stack data from the generator into a file.

    :param stack_events:
        An iterable of :class:`StackEvent` objects.
    :param filename:
        The name of the file into which to store the output.

    """
    logger.info("Enter create_stack_data_unsorted")

    logger.info("Counting number of stack occurrences")
    # Count stack occurrences
    cnt = collections.Counter(stack_events)

    logger.info("Sort stacks")
    # @Sort by keys (recursively by ascending index)

    logger.info("Writing folded stacks to file")
    # Write data to file
    # Format: eg. perf;[unknown];_perf_event_enable;event_function_call 24
    with open(filename, "w") as out:
        for stack_event, count in cnt.items():
            out.write(";".join(stack_event.stack) + " {}\n".format(count))

    logger.info("Done.")


def create_cpu_event_data(sched_events, filename):
    """
    Saves the event data from the generator into a file.

    :param sched_events:
        An iterator of :class:`SchedEvent` objects.
    :param filename:
        The name of the file into which to store the output.

    """
    # @Write to file
    with open(filename, "w") as out:
        for event in sched_events:
            out.write(str(event) + "\n")


def create_cpu_event_data_cpel(sched_events, filename):
    """
    Saves the event data from the generator in a file in CPEL format.

    :param sched_events:
        An iterator of :class:`SchedEvent` objects.
    :param filename:
        The name of the file into which to store the output.


    """
    # unwrap the generator (if it is one)
    events = list(sched_events)

    # Header ----------------------------------------------------------

    # Format:
    # 0x0 	    Endian bit (0x80), File Version, 7 bits (0x1...0x7F)
    # 0x1 	    Unused, 8 bits
    # 0x2-0x3 	Number of sections (16 bits) (NSECTIONS)
    # 0x4 	    File date (32-bits) (POSIX "epoch" format)

    # Use big endian as per specification
    endian_bit = 1
    file_version = 255
    first_byte = endian_bit << 7 | file_version
    # Calculate number of sections afterwards
    number_of_sections = 511
    # Use POSIX "epoch" format for date
    file_date = int(datetime.now().timestamp())
    # Just date: file_date = int(datetime.combine(date.today(),
    # time(0)).timestamp())

    header = struct.pack(">cxhi", bytes([first_byte]), number_of_sections,
                     file_date)
    print(header)

    # String tables -----------------------------------------------------
    type = 1
    length = 0 # Only know this after parsing all the strings
    info = struct.pack(">ii")
    # Symbol table ---------------------------------------------------------
    type = 2
    length = 0  # Only know this after parsing all the strings
    info = struct.pack(">ii")
    # Event definitions ----------------------------------------------------
    type = 3
    length = 0  # Only know this after parsing all the strings
    info = struct.pack(">ii")
    # Track definitions ----------------------------------------------------
    type = 4
    length = 0  # Only know this after parsing all the strings
    info = struct.pack(">ii")
    # Event sections -------------------------------------------------------
    type = 5
    length = 0  # Only know this after parsing all the strings
    info = struct.pack(">ii")


def create_mem_event_data(mem_events, filename):
    """
    Save memory event data from generator to output file.

    :param mem_events:
        An iterator over :class:`StackEvent` objects.
    :param filename:
        The output file.

    """

    logger.info("Enter create_mem_event_data")

    logger.info("Counting number of mem stack occurrences")

    # Count stack occurrences
    cnt = collections.Counter(mem_events)

    logger.info("Sort mem")
    # @Sort by keys (recursively by ascending index)

    logger.info("Writing folded mem stacks to file")
    # Write data to file
    # Format: eg. perf;[unknown];_perf_event_enable;event_function_call 24
    with open(filename, "w") as out:
        for mem_event, count in cnt.items():
            out.write(";".join(mem_event.stack) + " {}\n".format(count))

    logger.info("Done.")


if __name__=="__main__":
    create_cpu_event_data_cpel(None, None)
