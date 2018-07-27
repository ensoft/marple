# -------------------------------------------------------------
# converter/main.py - Saves data objects into a file.
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Saves data objects into a file.

Gets the data that was collected by an interface module and converted into
formatted objects and writes them into a file that was provided by the user.

"""
__all__ = ["create_stack_data_unsorted", "create_cpu_event_data"]

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

    cpel_writer = CpelWriter(sched_events)
    cpel_writer.write(filename)


class CpelWriter:
    """A class that takes event data and converts it to a CPEL file."""

    # ENDIAN_BIT: int value for endianness of the file (0 for big, 1 for little)
    ENDIAN_BIT = 0
    # FILE_VERSION: int value of 1 for showing this is a CPEL file
    FILE_VERSION = 1

    def __init__(self, event_objects):
        """
        Initialise the input data and read in the data

        :param event_objects:
            An iterator of event objects to be processed.
        """
        self.event_objects = event_objects

        # Information for writing the file header (no of sections etc.)
        self.info = dict()

        # Create attributes for section data
        self.string_table = dict()
        self.symbol_table = dict()
        self.event_definitions = dict()
        self.track_definitions = dict()
        self.event_data = dict()

        # Create list attribute for section lengths
        self.section_length = []

        # Int counting the number of sections in the file
        self.no_of_sections = 0

        # fill the above data structures with data from event input.
        self._collect()

    def _insert_strings(self, event_object):
        """
        Puts the string resources of the event object into the string table.

        :param event_object:
            A reference to the currently processed event object.

        """
        pass

    def _insert_symbols(self, event_object):
        """
        Unused for now.
        :param event_object:
             A reference to the currently processed event object.

        """
        pass

    def _insert_event_def(self, event_object):
        """
        Puts the event into the event definition attribute.

        :param event_object:
            A reference to the currently processed event object.

        """
        pass

    def _insert_track_def(self, event_object):
        """
        Puts the track into the track definition attribute.

        :param event_object:
            A reference to the currently processed event object.

        """
        pass

    def _insert_event(self, event_object):
        """
        Puts event data into the event attribute.

        :param event_object:
            A reference to the currently processed event object.

        """
        pass

    def _collect(self):
        """
        Processes the data and puts it into data structures.

        """
        for event_object in self.event_data:
            self._insert_strings(event_object)
            # self._insert_symbols(event_object)
            self._insert_event_def(event_object)
            self._insert_track_def(event_object)
            self._insert_event(event_object)
        self.no_of_sections += 4

    def _write_header(self, file_descriptor):
        """
        Writes the file header into the Cpel file.

        :param file_descriptor:
            The file descriptor of the Cpel file.

        """
        # Format:
        # 0x0 	    Endian bit (0x80), File Version, 7 bits (0x1...0x7F)
        # 0x1 	    Unused, 8 bits
        # 0x2-0x3 	Number of sections (16 bits) (NSECTIONS)
        # 0x4 	    File date (32-bits) (POSIX "epoch" format)

        # Calculate the file info byte
        first_byte = self.ENDIAN_BIT << 7 | self.FILE_VERSION
        # Insert number of sections
        number_of_sections = self.no_of_sections
        # Use POSIX "epoch" format for date
        file_date = int(datetime.now().timestamp())
        # Just date: file_date = int(datetime.combine(date.today(),
        #   time(0)).timestamp())

        header = struct.pack(">cxhi", bytes([first_byte]), number_of_sections,
                             file_date)

        file_descriptor.write(header)

    def write(self, filename):
        """
        Writes the data to disk in a CPEL file.

        :param filename:
            The name of the output file to which to write the data.

        """
        # Write linearly from data structures
        with open(filename, "w") as file_:
            self._write_header(file_)


if __name__ == "__main__":
    create_cpu_event_data_cpel(None, None)
