import struct
import unittest

import collect.converter.main as converter
from collect.converter import datatypes
from collect.test import util
from collect.converter.datatypes import StackEvent, SchedEvent


class _BaseTest(util.BaseTest):
    """Base test class"""

# -----------------------------------------------------------------------------
# Tests
#


class StackTest(_BaseTest):
    """Class for testing data conversion of stack data"""

    def check_create_stack_data(self, example, expected):
        filename = self._TEST_DIR + "create_stackdata_test"

        # Run converter on example input (implicitly tests hashability)
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

    def setUp(self):
        # Inherit temporary test directory.
        super().setUp()

        # Create Event iterators for testing
        self.testEvents = [datatypes.SchedEvent(datum="test_name (pid: "
                                                      "1234)",
                                                      track="cpu 2",
                                                      time=11112221,
                                                      type="event_type"
                                                ),
                           datatypes.SchedEvent(datum="test_name2 (pid: "
                                                      "1234)",
                                                      track="cpu 1",
                                                      time=11112222,
                                                      type="event_type")
                           ]


class CPELTest(SchedTest):
    """Class for testing conversion from event objects to CPEL"""

    # Well known output file
    example_file = "example_scheddata.cpel"

    def _compare_headers(self, file1, file2):
        """Helper function to compare headers between two CPEL files."""
        (first_byte1, nr_of_sections1, _) = struct.unpack(">cxhi",
                                                          file1.read(8))
        (first_byte2, nr_of_sections2, _) = struct.unpack(">cxhi",
                                                          file2.read(8))
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

    def test_variations(self):
        """Variations of data, same or different datum fields, same or different
        tracks, swapping track and data around, etc."""
        pass

    def test_duplicate_events(self):
        """Have completely duplicate events, see if it breaks things"""
        pass

    def test_timescales(self):
        """Test the time scales, different values for ticks per us (?)"""
        pass
