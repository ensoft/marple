import struct
import unittest

import collect.writer.write as converter
from collect.test import util
from common.datatypes import StackEvent, SchedEvent


class _BaseTest(util.BaseTest):
    """Base test class"""
    pass

# -----------------------------------------------------------------------------
# Tests
#


class StackTest(_BaseTest):
    """Class for testing data conversion of stack data"""

    def check_create_stack_data(self, example, expected):
        filename = self._TEST_DIR + "create_stackdata_test"

        # Run writer on example input (implicitly tests hashability)
        converter.create_stack_data_unsorted(example, filename)

        # Get the generated output
        output = ""
        with open(filename, "r") as file_:
            for line in file_:
                output += line

        # Later should also test sorting in separate function

        # Check that we got the desired output
        self.assertEqual(output, expected)

    def test_create_stack_data_basic(self):
        """Check that counter works and the output has the desired form"""

        # Example input
        example = (StackEvent(("pname", "call1", "call2")), StackEvent((
            "pname", "call1", "call2")), StackEvent(("pname", "call3",
                                                     "call4")))

        # Expected output:
        expected = "pname;call1;call2 2\n" \
            "pname;call3;call4 1\n"

        self.check_create_stack_data(example, expected)

    @unittest.skipIf(not hasattr(converter, "create_stack_data"),
                     "Only do once sorting has been implemented.")
    def test_create_stack_data_sorted(self):
        """Check that the sorting works"""

        # Example input
        example = (StackEvent(("pname", "call3", "call4")), StackEvent((
            "pname", "call1", "call2")), StackEvent((
                "pname", "call1", "call2")))

        # Expected output:
        expected = "pname;call1;call2 2\n" \
                   "pname;call3;call4 1\n"

        self.check_create_stack_data(example, expected)


class SchedTest(_BaseTest):
    """Class for testing creation and conversion of event object data"""

    # Create Event iterators for testing
    testEvents = [SchedEvent(datum="test_name (pid: 1234)",
                             track="cpu 2",
                             time=11112221,
                             type="event_type"),
                  SchedEvent(datum="test_name2 (pid: 1234)",
                             track="cpu 1",
                             time=11112222,
                             type="event_type")]


class CPELTest(SchedTest):
    """Class for testing conversion from event objects to CPEL"""

    # Well known output file
    example_file = "example_scheddata.cpel"

    def test_symbol_table_added_consistently(self):
        """
        Checks that either symbol table is not used, or used consistently.

        Original implementation left the symbol table section methods
        unimplemented. If they get added later, changes have to be made in 5
        places. This test checks this.

        """
        pass

    def _compare_headers(self, file1, file2):
        """Helper function to compare headers between two CPEL files."""
        first_byte1, nr_of_sections1, _ = struct.unpack(">cxhi", file1.read(8))
        first_byte2, nr_of_sections2, _ = struct.unpack(">cxhi", file2.read(8))
        self.assertEqual(first_byte1, first_byte2)
        self.assertEqual(nr_of_sections1, nr_of_sections2)

    def _compare_files(self, file1, file2):
        """Helper function to compare file content of two files."""
        while True:
            buffer1 = file1.read(1024)
            buffer2 = file2.read(1024)
            self.assertEqual(buffer1, buffer2)
            if not buffer1 or not buffer2:
                break

    def test_basic_file(self):
        """Creates a test file in test directory and compares it with example"""
        filename = self._TEST_DIR + "create_scheddata_test.cpel"
        converter.create_cpu_event_data_cpel(self.testEvents, filename)
        with open(filename, "rb") as test_file, open(self.example_file,
                                                     "rb") as correct_file:
            self._compare_headers(test_file, correct_file)
            self._compare_files(test_file, correct_file)

    @staticmethod
    def _get_nr_of_entries(filename, required_section_nr):
        """
        Finds the number of entries of a specific section.

        :param filename:
            The name of the CPEL file to be searched.
        :param required_section_nr:
            The number of the section to be examined.
        :return:
            The number of entries of that section.

        """

        with open(filename, "rb") as file_:

            # Get number of sections
            _, nr_of_sections = struct.unpack(">hh", file_.read(4))

            # Skip the rest of the header, to the string table
            file_.read(8)

            # Get the length of the string table
            (string_table_length,) = struct.unpack(">i", file_.read(4))

            # Get the string table
            string_table = file_.read(string_table_length).rstrip(
                b"\x00").split(bytes(b"\x00"))

            if required_section_nr == 1:
                return len(string_table)

            # Iterate through non string table sections
            for _ in range(1, nr_of_sections):

                this_section_nr, length = struct.unpack(">ii", file_.read(8))

                # Check whether this is the droid we're looking for
                if this_section_nr == required_section_nr:
                    # Skip string table name
                    file_.read(64)
                    # Next unsigned long is the required number of entries
                    (section_length,) = struct.unpack(">L", file_.read(4))
                    return section_length
                # Otherwise skip to the next section
                file_.read(length)

            return 0

    def test_nr_of_entries(self):
        """
        Test the right number of entries get created in each section.

        For two completely different events, check the nr of entries in each
        section is two.

        """

        filename = self._TEST_DIR + "create_scheddata_test_variations.cpel"

        # Two different events with different data, track and event:
        converter.create_cpu_event_data_cpel([SchedEvent(datum="d1",
                                                         track="t1",
                                                         time=1,
                                                         type="e1"),
                                              SchedEvent(datum="d2",
                                                         track="t2",
                                                         time=2,
                                                         type="e2")],
                                             filename)

        # Number of strings should be 8, 6 plus name of section plus format str
        self.assertEqual(self._get_nr_of_entries(filename, 1), 8)

        # All other sections should have two entries, one per event
        self.assertEqual(self._get_nr_of_entries(filename, 3), 2)
        self.assertEqual(self._get_nr_of_entries(filename, 4), 2)
        self.assertEqual(self._get_nr_of_entries(filename, 5), 2)

    def test_duplicate_events(self):
        """Have completely duplicate events, see if it breaks things."""

        filename = self._TEST_DIR + "create_scheddata_test_variations.cpel"

        # Two different events with same data, track, and event:
        converter.create_cpu_event_data_cpel([SchedEvent(datum="d",
                                                         track="1",
                                                         time=1,
                                                         type="e"),
                                              SchedEvent(datum="d",
                                                         track="1",
                                                         time=1,
                                                         type="e")],
                                             filename)

        # There should be 5 strings in the string table, 3 plus table name + %s
        self.assertEqual(self._get_nr_of_entries(filename, 1), 5)

        # Tracks and events look the same, so only one entry per section
        self.assertEqual(self._get_nr_of_entries(filename, 3), 1)
        self.assertEqual(self._get_nr_of_entries(filename, 4), 1)

        # Despite the same timing, there were two events so number should be two
        self.assertEqual(self._get_nr_of_entries(filename, 5), 2)

