import struct
import unittest
from unittest import mock
from io import StringIO
import os
import shutil

import common.datatypes
from collect.IO import write
from common.datatypes import StackDatum, EventDatum, PointDatum
import util.g2.cpel_writer as cpel_writer


@mock.patch('builtins.open')
class WriterTest(unittest.TestCase):

    def test_empty_data(self, open_mock):
        # Create mocks
        context_mock = open_mock.return_value
        file_mock = StringIO()
        context_mock.__enter__.return_value = file_mock

        # Run test
        writer = common.datatypes.Writer()
        writer.write([], "test", {})
        self.assertEqual("{}\n", file_mock.getvalue())

    def test_stack_data(self, open_mock):
        # Create mocks
        context_mock = open_mock.return_value
        file_mock = StringIO()
        context_mock.__enter__.return_value = file_mock

        # Set up test values
        stack_data = [
            StackDatum(1, ("A", "B", "C")),
            StackDatum(2, ("D", "E")),
            StackDatum(3, ("F", "G"))
        ]
        expected = "{}\n1#A;B;C\n2#D;E\n3#F;G\n"

        # Run test
        writer = common.datatypes.Writer()
        writer.write(stack_data, "test", {})
        self.assertEqual(expected, file_mock.getvalue())

    def test_datapoint_data(self, open_mock):
        # Create mocks
        context_mock = open_mock.return_value
        file_mock = StringIO()
        context_mock.__enter__.return_value = file_mock

        # Set up test values
        dp_data = [
            PointDatum(1.0, 2.0, 'info1'),
            PointDatum(3.0, 4.51, 'info2'),
            PointDatum(0.0, 1.3, 'info3')
        ]
        expected = "{}\n1.0,2.0,info1\n3.0,4.51,info2\n0.0,1.3,info3\n"

        # Run test
        writer = common.datatypes.Writer()
        writer.write(dp_data, "test", {})
        self.assertEqual(expected, file_mock.getvalue())

    def test_sched_data(self, open_mock):
        # Create mocks
        context_mock = open_mock.return_value
        file_mock = StringIO()
        context_mock.__enter__.return_value = file_mock

        # Set up test values
        sched_data = [
            EventDatum(time=1, type="type1",
                       specific_datum=("track1", "datum1")),
            EventDatum(time=2, type="type2",
                       specific_datum=("track2", "datum2")),
            EventDatum(time=3, type="type3",
                       specific_datum=("track3", "datum3")),
        ]
        # First line is an empty header
        expected = "{}\n1#type1#('track1', 'datum1')\n2#type2#('track2'," \
                   " 'datum2')\n3#type3#('track3', 'datum3')\n"

        # Run test
        writer = common.datatypes.Writer()
        writer.write(sched_data, "test", {})
        self.assertEqual(expected, file_mock.getvalue())


class SchedTest(unittest.TestCase):
    """Class for testing creation and conversion of event object data"""
    _TEST_DIR = "/tmp/marple-test/"

    def setUp(self):
        """Per-test set-up"""
        os.makedirs(self._TEST_DIR, exist_ok=True)

    def tearDown(self):
        """Per-test tear-down"""
        shutil.rmtree(self._TEST_DIR)

    # Create Event iterators for testing
    testEvents = [EventDatum(specific_datum=("cpu 2", "test_name (pid: 1234)"),
                             time=11112221,
                             type="event_type"),
                  EventDatum(specific_datum=("cpu 1", "test_name2 (pid: 1234)"),
                             time=11112222,
                             type="event_type")]


class CPELTest(SchedTest):
    """Class for testing conversion from event objects to CPEL"""

    # Well known output file
    example_file = "collect/test/IO/example_scheddata.cpel"

    @mock.patch("util.g2.cpel_writer.CpelWriter._insert_object_symbols")
    @mock.patch("util.g2.cpel_writer.CpelWriter._write_symbols")
    def test_symbol_table_added_consistently(self, write_mock, insert_mock):
        """
        Checks that either symbol table is not used, or used consistently.

        Original implementation left tself._TEST_DIR +he symbol table section methods
        unimplemented. If they get added later, changes have to be made in 5
        places. This test checks this.

        """
        filename = self._TEST_DIR + "symbol_test.cpel"
        writer = cpel_writer.CpelWriter(self.testEvents)
        writer.write(filename)

        # Check whether symbol write gets called in write method. Split
        if write_mock.called:
            # Make sure that the collect function has called the insert fn
            self.assertTrue(insert_mock.called)
            self.assertNotEqual(writer.section_length[2], 0)
            self.assertEqual(writer.no_of_sections, 5)
        else:
            self.assertFalse(insert_mock.called)
            self.assertEqual(writer.section_length[2], 0)
            self.assertEqual(writer.no_of_sections, 4)

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
        writer = cpel_writer.CpelWriter(self.testEvents)
        writer.write(filename)
        with open(filename, "rb") as test_file, \
                open(self.example_file, "rb") as correct_file:
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
        writer = cpel_writer.CpelWriter([
            EventDatum(specific_datum=("t1", "d1"), time=1, type="e1"),
            EventDatum(specific_datum=("t2", "d2"), time=2, type="e2")])
        writer.write(filename)

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
        writer = cpel_writer.CpelWriter([
            EventDatum(specific_datum=("1", "d"), time=1, type="e"),
            EventDatum(specific_datum=("1", "d"), time=1, type="e")])
        writer.write(filename)

        # There should be 5 strings in the string table, 3 plus table name + %s
        self.assertEqual(self._get_nr_of_entries(filename, 1), 5)

        # Tracks and events look the same, so only one entry per section
        self.assertEqual(self._get_nr_of_entries(filename, 3), 1)
        self.assertEqual(self._get_nr_of_entries(filename, 4), 1)

        # Despite the same timing, there were two events so number should be two
        self.assertEqual(self._get_nr_of_entries(filename, 5), 2)
