# -------------------------------------------------------------
# test_data_io.py - test module for datatypes used in marple
# August 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

""" Tests the datatypes used in marple. """
import os
import shutil
import struct
import unittest
from unittest import mock

from marple.common import (
    data_io,
    exceptions,
    paths,
    consts
)
from marple.common.data_io import EventDatum
from marple.display.tools.g2 import cpel_writer


class _DatatypeBaseTest(unittest.TestCase):
    def check_from_str(self, in_str, expected):
        actual = expected.from_string(in_str)
        self.assertEqual(expected, actual, msg='Expected {}, got {}'
                         .format(expected, actual))


class PointDatumTest(_DatatypeBaseTest):
    """Test datapoints are correctly converted to/from strings."""
    standard_field = consts.field_separator.join(["0.0", "0.0", "info"])

    def test_empty_string(self):
        """Ensure empty strings raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.PointDatum.from_string("")

    def test_malformed_floats(self):
        """Ensure invalid string floats raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.PointDatum.from_string(consts.field_separator.join(
                ["test", "0.0", "info"]
            ))
        with self.assertRaises(exceptions.DatatypeException):
            data_io.PointDatum.from_string(consts.field_separator.join(
                ["0.0", "tests", "info"]
            ))

    def test_too_few_fields(self):
        """Ensure strings with too few fields raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.PointDatum.from_string(consts.field_separator.join(
                ["0.0", "0.0"]
            ))

    def test_empty_info_field(self):
        """Ensure empty info field is OK"""
        result = data_io.PointDatum.from_string(consts.field_separator.join(
                ["0", "0"]
            ) + consts.field_separator)
        self.assertEqual(result.info, "",
                         msg="Expected info field '', was actually {}"
                         .format(result.info))

    def test_with_newline_n(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.PointDatum(0.0, 0.0, 'info')
        self.check_from_str(self.standard_field + "\n", expected)

    def test_with_newline_r(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.PointDatum(0.0, 0.0, 'info')
        self.check_from_str(consts.field_separator.join(
            ["0.0", "0.0", "info"]) + "\r", expected)

    def test_with_newline_rn(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.PointDatum(0.0, 0.0, 'info')
        self.check_from_str(self.standard_field + "\r\n", expected)

    def test_without_newline(self):
        """Ensure from_string works without newlines"""
        expected = data_io.PointDatum(0.0, 0.0, 'info')
        self.check_from_str(self.standard_field, expected)

    def test_to_string(self):
        """Test datapoints are correctly converted to strings."""
        dp = data_io.PointDatum(0.0, 0.0, 'info')
        expected = self.standard_field
        actual = str(dp)
        self.assertEqual(expected, actual, msg='Expected {}, got {}'
                         .format(expected, actual))


class StackDatumTest(_DatatypeBaseTest):
    """Test stack data are correctly converted to/from strings."""

    standard_field = consts.field_separator.join(["0", "A", "B"])

    def test_empty_string(self):
        """Ensure empty strings raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.StackDatum.from_string(consts.field_separator.join([""]))

    def test_malformed_floats(self):
        """Ensure invalid string floats raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.StackDatum.from_string(consts.field_separator.join(
                ["test", "A", "B"]))

    def test_too_few_fields(self):
        """Ensure strings with too few fields raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.StackDatum.from_string(consts.field_separator.join(
                ["test"]))

    def test_empty_stack_field(self):
        """Ensure empty stack field is OK"""
        result = data_io.StackDatum.from_string(consts.field_separator.join(
            ["0"]) + consts.field_separator)
        self.assertEqual(result.stack, ('',),
                         msg="Expected stack field empty, was actually {}"
                         .format(result.stack))

    def test_with_newline_n(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.StackDatum(0, ('A', 'B'))
        self.check_from_str(self.standard_field + '\n', expected)

    def test_with_newline_r(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.StackDatum(0, ('A', 'B'))
        self.check_from_str(self.standard_field + '\r', expected)

    def test_with_newline_rn(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.StackDatum(0, ('A', 'B'))
        self.check_from_str(self.standard_field + '\r\n', expected)

    def test_without_newline(self):
        """Ensure from_string works without newlines"""
        expected = data_io.StackDatum(0, ('A', 'B'))
        self.check_from_str(self.standard_field, expected)

    def test_to_string(self):
        """Test datapoints are correctly converted to strings."""
        sd = data_io.StackDatum(0, ('A', 'B'))
        expected = self.standard_field
        actual = str(sd)
        self.assertEqual(expected, actual, msg='Expected {}, got {}'
                         .format(expected, actual))


class EventDatumTest(_DatatypeBaseTest):
    """Test sched event data are correctly converted to/from strings."""

    def test_empty_string(self):
        """Ensure empty strings raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.EventDatum.from_string("")

    def test_malformed_ints(self):
        """Ensure invalid string ints raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.EventDatum.from_string("test$$$A$$$(\'B\', \'C\')")

    def test_too_few_fields(self):
        """Ensure strings with too few fields raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.EventDatum.from_string("test")

    def test_empty_type_field(self):
        """Ensure empty type field is OK"""
        result = data_io.EventDatum.from_string(
            "1" + consts.field_separator + consts.field_separator +
            "{'pid': 'p', 'comm': 'c', 'cpu': 'c'}" + consts.field_separator +
            "None"
        )
        self.assertEqual(result.type, "",
                         msg="Expected type field '', was actually {}"
                         .format(result.type))

    def test_specific_datum_field(self):
        """Ensure empty track field is OK"""
        result = data_io.EventDatum.from_string(
            "1" + consts.field_separator + "type" + consts.field_separator +
            "{}" + consts.field_separator +
            "None"
        )
        self.assertEqual(result.specific_datum, {},
                         msg="Expected type field '', was actually {}"
                         .format(result.specific_datum))

    def test_with_newline_n(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.EventDatum(
            time=1, type="type",
            specific_datum={'pid': 'p1', 'comm': 'n1', 'cpu': 'c1'},
            connected=[('source_', 'dest_')])
        x = "1" + consts.field_separator + "type" + consts.field_separator + \
            "{'pid': 'p1', 'comm': 'n1', 'cpu': 'c1'}" + \
            consts.field_separator + "[('source_', 'dest_')]"
        self.check_from_str(x + '\n', expected)

    def test_with_newline_r(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.EventDatum(
            time=1, type="type",
            specific_datum={'pid': 'p1', 'comm': 'n1', 'cpu': 'c1'},
            connected=[('source_', 'dest_')])
        x = "1" + consts.field_separator + "type" + consts.field_separator + \
            "{'pid': 'p1', 'comm': 'n1', 'cpu': 'c1'}" + \
            consts.field_separator + "[('source_', 'dest_')]"
        self.check_from_str(x + '\r', expected)

    def test_with_newline_rn(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.EventDatum(
            time=1, type="type",
            specific_datum={'pid': 'p1', 'comm': 'n1', 'cpu': 'c1'},
            connected=[('source_', 'dest_')])
        x = "1" + consts.field_separator + "type" + consts.field_separator + \
            "{'pid': 'p1', 'comm': 'n1', 'cpu': 'c1'}" + \
            consts.field_separator + "[('source_', 'dest_')]"
        self.check_from_str(x + '\r\n', expected)

    def test_without_newline(self):
        """Ensure from_string works without newlines"""
        """Ensure from_string copes with newlines"""
        expected = data_io.EventDatum(
            time=1, type="type",
            specific_datum={'pid': 'p1', 'comm': 'n1', 'cpu': 'c1'},
            connected=[('source_', 'dest_')])
        x = "1" + consts.field_separator + "type" + consts.field_separator + \
            "{'pid': 'p1', 'comm': 'n1', 'cpu': 'c1'}" + \
            consts.field_separator + "[('source_', 'dest_')]"
        self.check_from_str(x, expected)

    def test_to_string(self):
        """Test datapoints are correctly converted to strings."""
        se = data_io.EventDatum(
            time=1, type="type",
            specific_datum={'pid': 'p1', 'comm': 'n1', 'cpu': 'c1'},
            connected=[('source_', 'dest_')])
        expected = "1" + consts.field_separator + "type" + consts.field_separator + \
            "{'pid': 'p1', 'comm': 'n1', 'cpu': 'c1'}" + \
            consts.field_separator + "[('source_', 'dest_')]"
        actual = str(se)
        self.assertEqual(expected, actual, msg='Expected {}, got {}'
                         .format(expected, actual))


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
    testEvents = [
        EventDatum(
            time=11112221, type="event_type",
            specific_datum={'pid': '1234', 'comm': 'test_name', 'cpu': 'cpu 2'},
            connected=None),
        EventDatum(
            time=11112222, type="event_type",
            specific_datum={'pid': '1234', 'comm': 'test_name2', 'cpu': 'cpu 1'},
            connected=None)]


class CPELTest(SchedTest):
    """Class for testing conversion from event objects to CPEL"""

    # Well known output file
    example_file = paths.MARPLE_DIR + "/common/test/example_scheddata.cpel"

    @mock.patch("marple.display.tools.g2.cpel_writer."
                "CpelWriter._insert_object_symbols")
    @mock.patch("marple.display.tools.g2.cpel_writer.CpelWriter._write_symbols")
    def test_symbol_table_added_consistently(self, write_mock, insert_mock):
        """
        Checks that either symbol table is not used, or used consistently.

        Original implementation left tself._TEST_DIR +he symbol table section
        methods unimplemented.
        If they get added later, changes have to be made in 5 places.
        This test checks this.

        """
        filename = self._TEST_DIR + "symbol_test.cpel"
        writer = cpel_writer.CpelWriter(self.testEvents, "pid")
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
        writer = cpel_writer.CpelWriter(self.testEvents, "pid")
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
            EventDatum(
                time=11112221, type="e1",
                specific_datum={'pid': 'p1', 'comm': 'n1', 'cpu': 'c1'},
                connected=None),
            EventDatum(
                time=11112222, type="e2",
                specific_datum={'pid': 'p2', 'comm': 'n2', 'cpu': 'c2'},
                connected=None)],
            track="pid")
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
        event = EventDatum(time=1, type='e', connected=None,
                           specific_datum={'pid': 'p', 'comm': 'c', 'cpu': 'c'})
        writer = cpel_writer.CpelWriter(
            [event, event], track='pid'
        )
        writer.write(filename)

        # There should be 5 strings in the string table, 3 plus table name + %s
        self.assertEqual(self._get_nr_of_entries(filename, 1), 5)

        # Tracks and events look the same, so only one entry per section
        self.assertEqual(self._get_nr_of_entries(filename, 3), 1)
        self.assertEqual(self._get_nr_of_entries(filename, 4), 1)

        # Despite the same timing, there were two events so number should be two
        self.assertEqual(self._get_nr_of_entries(filename, 5), 2)
