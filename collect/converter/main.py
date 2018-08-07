# -------------------------------------------------------------
# converter/main.py - Saves data objects into a file.
# June-July 2018 - Franz Nowak, Hrutvik Kanabar
# -------------------------------------------------------------

"""
Saves data objects into a file.

Gets the data that was collected by an interface module and converted into
formatted objects and writes them into a file that was provided by the user.

"""
__all__ = ["create_stack_data_unsorted", "create_cpu_event_data",
           "create_mem_flamegraph_data", "create_disk_flamegraph_data",
           "create_datapoint_file"]

import collections
import logging
import struct
from datetime import datetime

from collect.converter import datatypes

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
    logger.info("Enter create_cpu_data.")

    no_data_flag = True

    logger.info("Writing cpu events to file.")
    # @Write to file
    with open(filename, "w") as out:
        for event in sched_events:
            no_data_flag = False
            out.write(str(event) + "\n")
        if no_data_flag:
            raise ValueError(
                "No stack data objects found in the iterable to be "
                "converted.")


def create_cpu_event_data_cpel(sched_events, filename):
    """
    Saves the event data from the generator in a file in CPEL format.

    :param sched_events:
        An iterator of :class:`SchedEvent` objects.
    :param filename:
        The name of the file into which to store the output.


    """
    logger.info("Enter create_cpu_event_data_cpel.")

    cpel_writer = CpelWriter(sched_events)
    cpel_writer.write(filename)


def create_mem_flamegraph_data(mem_events, filename):
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


def create_disk_flamegraph_data(disk_events, filename):
    """
    Save disk event data from generator to output file.

    :param disk_events:
        An iterator over :class:`StackEvent` objects.
    :param filename:
        The output file.

    """
    logger.info("Enter create_disk_event_data")

    logger.info("Counting number of disk stack occurrences")

    # Count stack occurrences
    cnt = collections.Counter(disk_events)

    logger.info("Sort disk")
    # @Sort by keys (recursively by ascending index)

    logger.info("Writing folded disk stacks to file")
    # Write data to file
    # Format: eg. perf;[unknown];_perf_event_enable;event_function_call 24
    with open(filename, "w") as out:
        for disk_event, count in cnt.items():
            out.write(";".join(disk_event.stack) + " {}\n".format(count))

    logger.info("Done.")


def create_datapoint_file(datapoints, output_file):
    """
    Save datapoint data as comma-separated values.

    :param datapoints:
        The datapoints generator.
    :param output_file:
        The file to save to disk.

    """
    logger.info("Enter create_datapoint_file")

    with open(output_file, "w") as out:
        for datapoint in datapoints:
            # Write as comma-separated values
            s = str(datapoint.x) + "," + str(datapoint.y) + "," + \
                datapoint.info + "\n"
            out.write(s)


class CpelWriter:
    """A class that takes event data and converts it to a CPEL file."""

    # _ENDIAN_BIT: int value for endianness of the file(0 for big, 1 for little)
    _ENDIAN_BIT = 0

    # _FILE_VERSION: int value of 1 for showing this is a CPEL file.
    _FILE_VERSION = 1

    # _FILE_STRING_TABLE_NAME: str, name of the (only) file string table (64b).
    _FILE_STRING_TABLE_NAME = "FileStrtab" + 54 * "\x00"

    # _SECTION_HEADER_LENGTHS: apart from string section, add 64 for the table
    #     name, 4 for length info and for the event section, 4 for ticks per us.
    _SECTION_HEADER_LENGTHS = {1: 0, 2: 68, 3: 68, 4: 68, 5: 72}

    def __init__(self, event_objects):
        """
        Initialise the input data and read in the data

        :param event_objects:
            An iterator of :class:`SchedEvent` objects to be processed.

        """
        self.event_objects = event_objects

        # Information for writing the file header (no of sections etc.)
        self.info = {}

        # Attribute for section lengths, key is section, value is length
        self.section_length = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

        # Create attributes for string section data
        self.string_table = {}
        self._string_resource = ""
        short_table_name = self._FILE_STRING_TABLE_NAME.rstrip("\x00")
        self.string_table[short_table_name] = 0
        self._string_resource += short_table_name
        self.section_length[1] = len(short_table_name)
        self.string_table["%s"] = self.section_length[1] + 1
        self._string_resource += ("\x00" + "%s")
        self.section_length[1] += (len("%s") + 1)

        # Dict for symbol table section
        self.symbol_table = {}

        # Dicts for event definition section
        self.event_definitions_dict = {}
        self.event_data_dict = {}
        # Index for the two above
        self.event_def_index = 0

        # Dict for the track definitions
        self.track_definitions_dict = {}
        self.track_def_index = 0

        # List of events for event section
        self.event_data = []

        # Int counting the number of sections in the file
        self.no_of_sections = 0

        # fill the above data structures with data from event input.
        self._collect()

    def _insert_string(self, string_key: str):
        """
        Puts a string into the string table, taking care of updating the index.
        :param string_key:
            A string to be put into the string table.

        """
        if string_key not in self.string_table:
            self.string_table[string_key] = self.section_length[1] + 1
            self.section_length[1] += (len(string_key) + 1)
            self._string_resource += ("\x00" + string_key)

    def _insert_object_strings(self, event_object):
        """
        Puts the string resources of the event object into the string table.

        :param event_object:
            A reference to the currently processed event object.

        """
        # insert datum, track, event_type (not time)
        self._insert_string(event_object.datum)
        self._insert_string(event_object.track)
        self._insert_string(event_object.type)

    def _insert_object_symbols(self, event_object):
        """
        Unused for now.
        :param event_object:
             A reference to the currently processed event object.

        """
        raise NotImplementedError("Method insert symbols not implemented.")

    def _insert_object_event_def(self, event_object):
        """
        Puts the event into the event definition attribute.

        :param event_object:
            A reference to the currently processed event object.

        """
        # event_code event_offset datum_offset (4 bytes each)
        if event_object.type not in self.event_definitions_dict:
            self.event_definitions_dict[event_object.type] = \
                self.event_def_index
            self.event_def_index += 1

            # add 3 x 4 = 12 (bytes) to the obj def section length
            self.section_length[3] += 12

    def _insert_object_track_def(self, event_object):
        """
        Puts the track into the track definition attribute.

        :param event_object:
            A reference to the currently processed event object.

        """
        # track_id track_format_offset (4 bytes each)

        if event_object.track not in self.track_definitions_dict:
            self.track_definitions_dict[event_object.track] = \
                self.track_def_index
            self.track_def_index += 1

            # add 2 x 4 = 8 (bytes) to the track def section length
            self.section_length[4] += 8

    def _insert_object_event_data(self, event_object):
        """
        Puts event data into the event attribute.

        :param event_object:
            A reference to the currently processed event object.
                time: string("d+.d+")

        """
        # time,time (from object) track_id (from track_def_dict) event_code (
        #   from event_def_dict) event_datum (from string table) (4 bytes each)

        self.event_data.append((event_object.time,
                                self.track_definitions_dict[event_object.track],
                                self.event_definitions_dict[event_object.type],
                                self.string_table[event_object.datum]))

        # add 5 x 4 = 20 (bytes) to the event data section length
        self.section_length[5] += 20

    def _collect(self):
        """
        Processes the data and puts it into data structures.

        """
        # sequence of all the functions needed
        insert_functions = [self._insert_object_strings,
                            # self._insert_object_symbols
                            self._insert_object_event_def,
                            self._insert_object_track_def,
                            self._insert_object_event_data]

        for event_object in self.event_objects:
            for fn in insert_functions:
                fn(event_object)

        self.no_of_sections += len(insert_functions)

    def _write_file_header(self, file_descriptor):
        """Writes the file header into the Cpel file."""
        # Format:
        # 0x0 	    Endian bit (0x80), File Version, 7 bits (0x1...0x7F)
        # 0x1 	    Unused, 8 bits
        # 0x2-0x3 	Number of sections (16 bits) (NSECTIONS)
        # 0x4 	    File date (32-bits) (POSIX "epoch" format)

        # Calculate the file info byte
        first_byte = self._ENDIAN_BIT << 7 | self._FILE_VERSION
        # Use POSIX "epoch" format for date
        file_date = int(datetime.now().timestamp())
        # Just date: file_date = int(datetime.combine(date.today(),
        #   time(0)).timestamp())

        header = struct.pack(">cxhi", bytes([first_byte]),
                             self.no_of_sections,
                             file_date)

        file_descriptor.write(header)

    @staticmethod
    def _write_tld(section_type_nr: int, section_length: int,
                   file_descriptor):
        """
        Writes the type and the length of the following section into file.

        :param section_type_nr:
            The identifier of the section type.
        :param section_length:
            The length of the section.
        :param file_descriptor:
            The file descriptor of the file to be written to.

        """
        tld = struct.pack(">ii", section_type_nr, section_length)
        file_descriptor.write(tld)

    def _write_strings(self, file_descriptor):
        """
        Writes the string table into the file

        :param file_descriptor:
            The file descriptor of the file to be written to.

        """
        file_descriptor.write(bytearray(self._string_resource, "ascii"))

    def _write_symbols(self):
        """
        Not needed now.
        Writes the symbol table into the file.

        """
        # struct symbol_section_entry {
        #     unsigned long value;
        #     unsigned long name_offset_in_string_table;
        # };
        raise NotImplementedError("Method write symbol table not implemented.")

    def _write_event_def(self, file_descriptor):
        """
        Writes the event definition section into the file

        :param file_descriptor:
            The file descriptor of the file to be written to.

        """
        # struct event_definition_entry {
        #     unsigned long event_code;
        #     unsigned long event_format_offset_in_string_table;
        #     unsigned long datum_format_offset_in_string_table;
        # };

        # sort by value (index) and write into file
        for event_format_offset, event_code in sorted(
                self.event_definitions_dict.items(),
                key=(lambda x: x[1])):

            event_format = self.string_table[event_format_offset]
            event_data_format = self.string_table["%s"]
            file_descriptor.write(struct.pack(">LLL", event_code,
                                              event_format, event_data_format))

    def _write_track_def(self, file_descriptor):
        """
        Writes the track definition section into the file

        :param file_descriptor:
            The file descriptor of the file to be written to.

        """
        # struct track_definition {
        #     unsigned long track_id;
        #     unsigned long track_format_offset_in_string_table;
        # };

        # Sort by value (id) and write into file
        for track_format_offset, track_id in sorted(
                self.track_definitions_dict.items(),
                key=(lambda x: x[0])):

            track_format = self.string_table[track_format_offset]
            file_descriptor.write(struct.pack(">LL", track_id, track_format))

    def _write_events(self, file_descriptor):
        """
        Writes the event data to disk

        :param file_descriptor:
            The file descriptor of the file to be written to.

        """
        # struct event_entry {
        # 	unsigned long time[2];
        # 	unsigned long track;
        # 	unsigned long event_code;
        # 	unsigned long event_datum;
        # };

        for time, track_id, event_code, event_datum in self.event_data:
            
            # Split time up into two 32 bit unsigned longs
            times = self._convert_time(time)
            data = struct.pack(">LLLLL", times[0], times[1], track_id,
                               event_code, event_datum)
            file_descriptor.write(data)

    def _write_section_header(self, no_of_entries, file_descriptor,
                              event_section=False):
        """
        Writes the table name before the start of a section

        :param no_of_entries:
            The number of entries the section has.
        :param file_descriptor:
            The file descriptor of the file to be written to.
        :param event_section:
            Optional flag to indicate that the sectionn is an event section.

        """
        file_descriptor.write(bytearray(self._FILE_STRING_TABLE_NAME, "ascii"))
        file_descriptor.write(struct.pack(">L", no_of_entries))

        if event_section:
            # Write a number for ticks per microsecond:
            file_descriptor.write(struct.pack(">L", 1000000))

    @staticmethod
    def _convert_time(time):
        """
        Splits a 64 bit number into two 32 bit numbers.

        :param time:
            A positive 64 bit number.

        :return:
            A list of two unsigned 32 bit numbers.

        """
        times = [time >> 32, time & 2 ** 32 - 1]
        return times

    def _pad_strings(self):
        """Makes sure the string section is padded to the nearest four bytes"""
        padnum = 4 - (len(self._string_resource) % 4)
        for _ in range(padnum):
            self._string_resource += "\x00"
            self.section_length[1] += 1

    def write(self, filename):
        """
        Writes the data to disk in a CPEL file.

        :param filename:
            The name of the output file to which to write the data.

        """
        # Write linearly from data structures
        with open(filename, "wb") as file_:

            # Header
            self._write_file_header(file_)

            # String Table
            self._pad_strings()
            self._write_tld(1, self.section_length[1], file_)
            self._write_strings(file_)

            # Event Definition Section
            self._write_tld(3, self.section_length[3] +
                            self._SECTION_HEADER_LENGTHS[3], file_)
            self._write_section_header(len(self.event_definitions_dict), file_)
            self._write_event_def(file_)

            # Track Definition Section
            self._write_tld(4, self.section_length[4] +
                            self._SECTION_HEADER_LENGTHS[4], file_)
            self._write_section_header(len(self.track_definitions_dict), file_)
            self._write_track_def(file_)

            # Event Section
            self._write_tld(5, self.section_length[5] +
                            self._SECTION_HEADER_LENGTHS[5], file_)
            self._write_section_header(len(self.event_data), file_,
                                       event_section=True)
            self._write_events(file_)


if __name__ == "__main__":
    create_cpu_event_data_cpel([datatypes.SchedEvent(datum="test_name (pid: "
                                                           "1234)",
                                                     track="cpu 2",
                                                     time=11112221,
                                                     type="event_type"
                                                     ),
                                datatypes.SchedEvent(datum="test_name2 (pid: "
                                                           "1234)",
                                                     track="cpu 1",
                                                     time=11112222,
                                                     type="event_type")],
                               "../test/converter/example_scheddata.cpel")
