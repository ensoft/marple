# -------------------------------------------------------------
# IO/write.py - Saves data objects into a file.
# June-July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
Saves data objects into a file.

Gets the data that was collected by an interface module and converted into
formatted objects and writes them into a file that was provided by the user.

"""
__all__ = (
    'CpelWriter',
)

import logging
import struct
from datetime import datetime

from marple.common import util

logger = logging.getLogger(__name__)
logger.debug('Entered module: %s', __name__)


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

    def __init__(self, event_objects, track):
        """
        Initialise the input data and read in the data

        :param event_objects:
            An iterator of :class:`EventDatum` objects to be processed.
        :param track:
            The track to be used. The objects of are of type :class:`EventDatum`
            which has a touple `specifid_data`; for the scheduling events the
            order is (name/pid, cpu)

        """
        self.event_objects = event_objects
        self.track = track

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

    def _decide_track_label(self, event_object):
        """
        Method that decides the track and the label for a particular event
        Scheduling events of the type `EventType` have their specific data as
        follows: (name/pid, cpu)

        :param event_object: the event we want to fine the track and label for
        :return: a pair (track, label)

        """
        if self.track == "pid":
            return (event_object.specific_datum[0],
                    event_object.specific_datum[1])
        elif self.track == "cpu":
            return (event_object.specific_datum[1],
                    event_object.specific_datum[0])
        else:
            raise ValueError("Unknown option for the track: {}. "
                             "Expected cpu or pid.".format(
                              self.track))

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
        track, label = self._decide_track_label(event_object)
        self._insert_string(label)
        self._insert_string(track)
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

        track, _ = self._decide_track_label(event_object)
        if track not in self.track_definitions_dict:
            self.track_definitions_dict[track] = \
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

        track, label = self._decide_track_label(event_object)
        self.event_data.append(
            (event_object.time,
             self.track_definitions_dict[track],
             self.event_definitions_dict[event_object.type],
             self.string_table[label])
        )

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

    @util.log(logger)
    def write(self, filename):
        """
        Writes the data to disk in a CPEL file.

        :param filename:
            The name of the output file to which to write the data.

        """
        # Write linearly from data structures
        with open(filename, "wb") as file_:
            # CPEL Header
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

# if __name__ == "__main__":
#     WriterCPEL.write([datatypes.SchedEvent(datum="test_name (pid: "
#                                                            "1234)",
#                                                      track="cpu 2",
#                                                      time=11112221,
#                                                      type="event_type"
#                                                      ),
#                                 datatypes.SchedEvent(datum="test_name2 (pid: "
#                                                            "1234)",
#                                                      track="cpu 1",
#                                                      time=11112222,
#                                                      type="event_type")],
#                                "../test/writer/example_scheddata.cpel",
#                      "[CPEL]")
