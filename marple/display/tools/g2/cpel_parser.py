#!/usr/bin/env python3

# -------------------------------------------------------------
# cpel_parser.py - Reads in a cpel binary file and displays its data by section.
# July 2018 - Franz Nowak
# -------------------------------------------------------------

"""
CPEL parser - Reads in a cpel binary file and displays its data by section.

This is to understand the format, not just read the data, for which you would
    use vpp/cpeldump.

"""

import re
import struct
import sys
from datetime import datetime

# SAMPLE_SIZE: An int defining the number of bytes of string shown to user.
SAMPLE_SIZE = 256


class CPELParser:
    """
    CPEL parser - Reads in a cpel binary file and displays its data by section.

    :arg filename:
        The CPEL file to parse.
    """

    # SECTION_TYPES: A list of types of section for user display
    SECTION_TYPES = ["(empty)", "String Table Section", "Symbol Table Section",
                     "Event Definition Section", "Track Definition Section",
                     "Event Section"]

    def __init__(self, filename: str):
        """
        Initialises the parser.

        :param filename:
            The name of the file containing binary data in CPEL format.

        """
        self.filename = filename
        self.string_tables = dict()

    def _get_string(self, string_table, offset):
        """
        Fetches a string from the string resource table.

        :param string_table:
            The table name of the string resource table.
        :param offset:
            The offset in bytes of the start of the string in the string table.

        :return:
            The string resource from the string table.

        """
        rest = str(self.string_tables[string_table])[offset:]
        return rest.split("\x00", 1)[0]

    @staticmethod
    def _parse_file_header(file_descriptor):
        """
        Parses and prints the file header.

        :param file_descriptor:
            The file descriptor of the file containing the data.

        """
        # Octet_offset, 	Data
        # 0x0 	    Endian bit (0x80), File Version, 7 bits (0x1...0x7F)
        # 0x1 	    Unused, 8 bits
        # 0x2-0x3 	Number of sections (16 bits)
        # 0x4 	    File date (32-bits) (POSIX "epoch" format)

        (file_info, number_of_sections, file_date) = \
            struct.unpack(">cxhi", file_descriptor.read(8))

        print("Endian-bit: {} ({}-endian)"
              .format(file_info[0] >> 7, "little" if (file_info[0] >> 7) == 1
                      else "big"))
        print("File version: {}".format(file_info[0] & 127))
        print("Number of sections: {}".format(number_of_sections))
        print("File date: {}".format(datetime.fromtimestamp(file_date)))

    def _parse_tld(self, file_descriptor):
        """

        :param file_descriptor:
            The file descriptor of the file containing the data.

        :return:
            A tuple of the section type number and the section length,
                or None, None if the end of file was reached.

        """
        # Get type and length info
        tld = file_descriptor.read(8)

        # Check for end of file
        if len(tld) != 8:
            print("EOF")
            return None, None

        # Unpack type and length info
        (section_type_nr, section_length) = struct.unpack(">ii", tld)
        section_type = self.SECTION_TYPES[section_type_nr]

        # Print info about section
        print("\nSection type: {}".format(section_type))
        print("Section length: {}".format(section_length))

        return section_type_nr, section_length

    @staticmethod
    def _parse_section_header(file_descriptor, section_type_nr: int,
                              section_length: int):
        """
        Parses the header of a given section.

        :param file_descriptor:
            The file descriptor of the file containing the data.
        :param section_type_nr:
            The index of the section type in the SECTION_TYPES list.
        :param section_length:
            The length in bytes of the section.

        :return:
            A tuple of the section length and the table name.

        """
        new_section_length = section_length
        table_name = None

        # Section type 1 does not need any more info
        if section_type_nr == 1:
            pass

        elif section_type_nr in range(2, 6):
            # struct event_definition_section_header {
            #     char string_table_name[64];
            #     unsigned long number_of_event_definitions;
            # };

            # Get string table name
            table_name = str(file_descriptor.read(64).decode())
            table_name = re.sub(r"\x00", "", table_name)
            # Section name is included in section length, so subtract
            new_section_length -= 64
            print("Table name: {}".format(table_name))

            # Get number of entries
            (number_of_entries,) = struct.unpack(">L", file_descriptor.read(4))
            # number of entries included in section length, so subtract
            new_section_length -= 4
            print("Number of entries: {}".format(number_of_entries))

            # Event section
            if section_type_nr == 5:
                # struct event_section_header {
                #     ...
                #     unsigned long clock_ticks_per_microsecond;
                # };

                # Get number of ticks per microsecond
                (ticks_per_us,) = struct.unpack(">L", file_descriptor.read(4))
                # included in section length, so subtract
                section_length -= 4
                print("Ticks per microsecond: {}".format(ticks_per_us))

        # Unknown/ empty section
        else:
            new_section_length = 0

        return new_section_length, table_name

    def _parse_string_table(self, binary_content: bytes, section_length: int):
        """
        Parses a string table section of the file.

        :param binary_content:
            The data of the section in binary format.
        :param section_length:
            The length in bytes of the section.

        """
        (char_content,) = struct.unpack(">{}s".format(section_length),
                                        binary_content)

        # Convert binary strings to utf8 (could break for non-characters)
        string_resources = str(char_content.decode())

        # Split at the first Null terminator to get table name and string list
        table_name = string_resources.split("\x00", 1)[0]
        print("Table name: {}".format(table_name))

        # Save string resources as a string in dict
        self.string_tables[table_name] = string_resources

        # Output some of it
        print("{}...".format(re.sub(r"\x00", ", ", string_resources[
                                                   :SAMPLE_SIZE])))

    def _parse_symbol_table(self, binary_content: bytes, section_length: int,
                            table_name: str):
        """
        Parses a symbol table section.

        :param binary_content:
            The data of the section in binary format.
        :param section_length:
            The length in bytes of the section.
        :param table_name:
            The name of the string table associated with this section.

        """
        # struct symbol_section_entry {
        #     unsigned long value;
        #     unsigned long name_offset_in_string_table;
        # };
        print("value name:")
        for index in range(0, int(section_length), 8):
            (value, name_offset) = struct.unpack(
                ">LL", binary_content[index:index + 8])
            print("{}\t{}".format(value,
                                  self._get_string(table_name, name_offset)))

    def _parse_event_definition_section(self, binary_content: bytes,
                                        section_length: int,
                                        table_name: str):
        """
        Parses an event definition section.

        :param binary_content:
            The data of the section in binary format.
        :param section_length:
            The length in bytes of the section.
        :param table_name:
            The name of the string table associated with this section.

        """

        # struct event_definition_entry {
        #     unsigned long event_code;
        #     unsigned long event_format_offset_in_string_table;
        #     unsigned long datum_format_offset_in_string_table;
        # };
        print("event_code [event_offset] [datum_offset]:")

        for index in range(0, int(section_length), 12):
            (event_code, event_offset, datum_offset) = struct.unpack(
                ">LLL", binary_content[index:index + 12])
            print("{}\t{}[{}] (\"{}\")\t{}[{}] (\"{}\")"
                  .format(event_code,
                          table_name,
                          event_offset,
                          self._get_string(
                              table_name,
                              event_offset),
                          table_name,
                          datum_offset,
                          self._get_string(
                              table_name,
                              datum_offset)))

    def _parse_track_definition_section(self, binary_content: bytes,
                                        section_length: int,
                                        table_name: str):
        """
        Parses a track definition section.

        :param binary_content:
            The data of the section in binary format.
        :param section_length:
            The length in bytes of the section.
        :param table_name:
            The name of the string table associated with this section.

        """
        # struct track_definition {
        #     unsigned long track_id;
        #     unsigned long track_format_offset_in_string_table;
        # };
        print("track_id [track_offset]:")
        for index in range(0, int(section_length), 8):
            (track_id, track_offset) = struct.unpack(">LL", binary_content[
                                                            index:index + 8])
            print("{}\t{}[{}] (\"{}\")".format(track_id, table_name,
                                               track_offset, self._get_string(
                                                  table_name, track_offset)))

    def _parse_event_section(self, binary_content: bytes, section_length: int,
                             table_name: str):
        """
        Parses an event section.

        :param binary_content:
            The data of the section in binary format.
        :param section_length:
            The length in bytes of the section.

        """
        # struct event_entry {
        # 	unsigned long time[2];
        # 	unsigned long track;
        # 	unsigned long event_code;
        # 	unsigned long event_datum;
        # };
        print("time \t\t\t\t\t track \t event_code \t event_datum:")
        for index in range(0, int(section_length) - 20, 20):
            (time0, time1, track, event_code, event_datum) = struct.unpack(
                ">LLLLL", binary_content[index:index + 20])

            time = (time0 << 32) | time1
            print("time:\t{} \t track:{:5d} \t event:{:5d} \t\t{}"
                  .format(time,
                          track,
                          event_code,
                          self._get_string(
                              table_name,
                              event_datum)))

    def parse_file(self):
        """ The main function of the parser, parses the CPEL file. """
        with open(sys.argv[1], "rb") as file_:

            # Parse the file header
            self._parse_file_header(file_)

            # Parse the sections
            while True:
                # get type and length info
                section_type_nr, section_length = self._parse_tld(file_)

                # Check if we have reached the end of the file
                if not section_type_nr or not section_length:
                    break

                # Get table name and ticks per microsecond
                section_length, table_name = \
                    self._parse_section_header(file_,
                                               section_type_nr, section_length)

                # Read in the remainder of the section
                binary_content = file_.read(section_length)

                # String Table Section
                if section_type_nr == 1:
                    self._parse_string_table(binary_content, section_length)

                # Symbol Table Section
                elif section_type_nr == 2:
                    self._parse_symbol_table(binary_content, section_length,
                                             table_name)
                # Event Definition Section
                elif section_type_nr == 3:
                    self._parse_event_definition_section(binary_content,
                                                         section_length,
                                                         table_name)
                # Track Definition Section
                elif section_type_nr == 4:
                    self._parse_track_definition_section(binary_content,
                                                         section_length,
                                                         table_name)
                # Event Section
                elif section_type_nr == 5:
                    self._parse_event_section(binary_content,
                                              section_length,
                                              table_name)
                # If the given number is not in the range 1-5
                else:
                    print("Invalid Section number {}".format(
                        section_type_nr))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit("No input argument. Please select a file to parse.")

    try:
        parser = CPELParser(sys.argv[1])
        parser.parse_file()

    except FileNotFoundError as fnfe:
        exit("File {} not found, please check filename.".format(fnfe.filename))

    except IOError as ioe:
        exit("Unexpected IOError occurred: {}".format(ioe))

    except struct.error as se:
        exit("Unable to parse. {}".format(se.args))

    except Exception as e:
        exit("Unexpected Error occurred: {}".format(e.args))
