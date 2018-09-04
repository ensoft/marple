# -------------------------------------------------------------
# test_data_io.py - test module for datatypes used in marple
# August 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

""" Tests the datatypes used in marple. """
import json
import os
import shutil
import struct
import unittest
from enum import Enum
from io import StringIO
from unittest import mock

from marple.common import (
    data_io,
    exceptions,
    paths
)
from marple.common.data_io import StackDatum, PointDatum, EventDatum
from marple.display.tools.g2 import cpel_writer


class _DatatypeBaseTest(unittest.TestCase):
    def check_from_str(self, in_str, expected):
        actual = expected.from_string(in_str)
        self.assertEqual(expected, actual, msg='Expected {}, got {}'
                         .format(expected, actual))


class DatapointTest(_DatatypeBaseTest):
    """Test datapoints are correctly converted to/from strings."""

    def test_empty_string(self):
        """Ensure empty strings raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.PointDatum.from_string("")

    def test_malformed_floats(self):
        """Ensure invalid string floats raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.PointDatum.from_string("test,0.0,info")
        with self.assertRaises(exceptions.DatatypeException):
            data_io.PointDatum.from_string("0.0,test,info")

    def test_too_few_fields(self):
        """Ensure strings with too few fields raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.PointDatum.from_string("0.0,0.0")

    def test_empty_info_field(self):
        """Ensure empty info field is OK"""
        result = data_io.PointDatum.from_string("0.0,0.0,")
        self.assertEqual(result.info, "",
                         msg="Expected info field '', was actually {}"
                         .format(result.info))

    def test_with_newline_n(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.PointDatum(0.0, 0.0, 'info')
        self.check_from_str('0.0,0.0,info\n', expected)

    def test_with_newline_r(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.PointDatum(0.0, 0.0, 'info')
        self.check_from_str('0.0,0.0,info\r', expected)

    def test_with_newline_rn(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.PointDatum(0.0, 0.0, 'info')
        self.check_from_str('0.0,0.0,info\r\n', expected)

    def test_without_newline(self):
        """Ensure from_string works without newlines"""
        expected = data_io.PointDatum(0.0, 0.0, 'info')
        self.check_from_str('0.0,0.0,info', expected)

    def test_to_string(self):
        """Test datapoints are correctly converted to strings."""
        dp = data_io.PointDatum(0.0, 0.0, 'info')
        expected = '0.0,0.0,info'
        actual = str(dp)
        self.assertEqual(expected, actual, msg='Expected {}, got {}'
                         .format(expected, actual))


class StackDataTest(_DatatypeBaseTest):
    """Test stack data are correctly converted to/from strings."""

    def test_empty_string(self):
        """Ensure empty strings raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.StackDatum.from_string("")

    def test_malformed_floats(self):
        """Ensure invalid string floats raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.StackDatum.from_string("test$$$A;B")

    def test_too_few_fields(self):
        """Ensure strings with too few fields raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            data_io.StackDatum.from_string("test")

    def test_empty_stack_field(self):
        """Ensure empty stack field is OK"""
        result = data_io.StackDatum.from_string("0$$$")
        self.assertEqual(result.stack, ('',),
                         msg="Expected stack field empty, was actually {}"
                         .format(result.stack))

    def test_with_newline_n(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.StackDatum(0, ('A', 'B'))
        self.check_from_str('0$$$A;B\n', expected)

    def test_with_newline_r(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.StackDatum(0, ('A', 'B'))
        self.check_from_str('0$$$A;B\r', expected)

    def test_with_newline_rn(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.StackDatum(0, ('A', 'B'))
        self.check_from_str('0$$$A;B\r\n', expected)

    def test_without_newline(self):
        """Ensure from_string works without newlines"""
        expected = data_io.StackDatum(0, ('A', 'B'))
        self.check_from_str('0$$$A;B', expected)

    def test_to_string(self):
        """Test datapoints are correctly converted to strings."""
        sd = data_io.StackDatum(0, ('A', 'B'))
        expected = '0$$$A;B'
        actual = str(sd)
        self.assertEqual(expected, actual, msg='Expected {}, got {}'
                         .format(expected, actual))


class SchedEventTest(_DatatypeBaseTest):
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
        result = data_io.EventDatum.from_string("1$$$$$$(\'track\', \'datum\')")
        self.assertEqual(result.type, "",
                         msg="Expected type field '', was actually {}"
                         .format(result.type))

    def test_empty_track_field(self):
        """Ensure empty track field is OK"""
        result = data_io.EventDatum.from_string("1$$$type$$$(\'\', \'datum\')")
        self.assertEqual(result.specific_datum[0], "",
                         msg="Expected type field '', was actually {}"
                         .format(result.specific_datum[0]))

    def test_empty_datum_field(self):
        """Ensure empty datum field is OK"""
        result = data_io.EventDatum.from_string("1$$$type$$$(\'track\',\'\')")
        self.assertEqual(result.specific_datum[1], "",
                         msg="Expected type field '', was actually {}"
                         .format(result.specific_datum[1]))

    def test_with_newline_n(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.EventDatum(0, 'type', ('track', 'datum'))
        self.check_from_str('0$$$type$$$(\'track\', \'datum\')\n', expected)

    def test_with_newline_r(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.EventDatum(0, 'type', ('track', 'datum'))
        self.check_from_str('0$$$type$$$(\'track\', \'datum\')\r', expected)

    def test_with_newline_rn(self):
        """Ensure from_string copes with newlines"""
        expected = data_io.EventDatum(0, 'type', ('track', 'datum'))
        self.check_from_str('0$$$type$$$(\'track\', \'datum\')\r\n', expected)

    def test_without_newline(self):
        """Ensure from_string works without newlines"""
        expected = data_io.EventDatum(0, 'type', ('track', 'datum'))
        self.check_from_str('0$$$type$$$(\'track\', \'datum\')', expected)

    def test_to_string(self):
        """Test datapoints are correctly converted to strings."""
        se = data_io.EventDatum(0, 'type', ('track', 'datum'))
        expected = '0$$$type$$$(\'track\', \'datum\')'
        actual = str(se)
        self.assertEqual(expected, actual, msg='Expected {}, got {}'
                         .format(expected, actual))


class ReaderTest(unittest.TestCase):
    """
    Class that tests the reader context manager used to open marple files
    """

    def test_normal_file(self):
        """
        Tests if under normal conditions the file object is consumed
        correctly and the results are consistent

        """
        file_header = "{\"start\": \"2018-08-20 18:46:38.403129\", " \
                      "\"end\": \"2018-08-20 18:46:39.403129\", " \
                      "\"datatype\": \"Event Data\", " \
                      "\"interface\": \"Scheduling Events\"}\n"

        file_data = "1#2#3#4#5\n" \
                    "6#7#8#9#10\n" \
                    "11#12#13#14#15#16#17"
        file_object = StringIO(file_header + file_data)

        header = data_io.read_header(file_object)
        data = data_io.read_until_line(file_object, '\n')
        self.assertDictEqual(header, {"start": "2018-08-20 18:46:38.403129",
                                      "end": "2018-08-20 18:46:39.403129",
                                      "datatype": "Event Data",
                                      "interface": "Scheduling Events"})
        self.assertEqual([line for line in data],
                         ["1#2#3#4#5\n", "6#7#8#9#10\n",
                          "11#12#13#14#15#16#17"])

    def test_stops_correctly(self):
        """
        Tests if the data is being read until the separator and not beyond it

        """
        file_header = "{\"start\": \"2018-08-20 18:46:38.403129\", " \
                      "\"end\": \"2018-08-20 18:46:39.403129\", " \
                      "\"datatype\": \"Event Data\", " \
                      "\"interface\": \"Scheduling Events\"}\n"

        file_data = "1#2#3#4#5\n" \
                    "6#7#8#9#10\n\n" \
                    "11#12#13#14#15#16#17"
        file_object = StringIO(file_header + file_data)

        header = data_io.read_header(file_object)
        data = data_io.read_until_line(file_object, '\n')
        self.assertDictEqual(header, {"start": "2018-08-20 18:46:38.403129",
                                      "end": "2018-08-20 18:46:39.403129",
                                      "datatype": "Event Data",
                                      "interface": "Scheduling Events"})
        self.assertEqual([line for line in data],
                         ["1#2#3#4#5\n", "6#7#8#9#10\n"])

    def test_bad_JSON(self):
        """
        Tests an invalid header (ie not in a JSON format)

        """
        file_header = "{\"start\" \"2018-08-20 18:46:38.403129\", " \
                      "\"end\": \"2018-08-20 18:46:39.403129\", " \
                      "\"datatype\": \"Event Data\", " \
                      "\"interface\": \"Scheduling Events\"}\n"

        file_data = "1#2#3#4#5\n" \
                    "6#7#8#9#10\n" \
                    "11#12#13#14#15#16#17"
        file_object = StringIO(file_header + file_data)

        with self.assertRaises(json.JSONDecodeError):
            data_io.read_header(file_object)


@mock.patch('builtins.open')
class WriterTest(unittest.TestCase):
    class TestEnum(Enum):
        TEST_ENUM = 'test_enum'

    @staticmethod
    def header_helper(data):
        data.start_time = 'start'
        data.end_time = 'end'
        data.interface = WriterTest.TestEnum.TEST_ENUM
        data.datatype = 'datatype'
        try:
            data.data_options = {'option': 'opt_value'}
        except AttributeError:
            pass

    expected_header = json.dumps(
        {"start": 'start',
         "end": 'end',
         "interface": 'test_enum',
         "datatype": 'datatype',
         "data_options": {'option': 'opt_value'}}
    )

    def test_empty_data(self, open_mock):
        # Create mocks
        context_mock = open_mock.return_value
        file_mock = StringIO()
        context_mock.__enter__.return_value = file_mock

        data = object.__new__(data_io.StackData)
        data.datum_generator = []
        self.header_helper(data)

        # Run test
        data_io.write(data, "test")
        self.assertEqual("{}\n\n".format(self.expected_header),
                         file_mock.getvalue())

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

        data = object.__new__(data_io.StackData)
        data.datum_generator = stack_data
        self.header_helper(data)
        expected = "{}\n1$$$A;B;C\n2$$$D;E\n3$$$F;G\n\n"\
            .format(self.expected_header)

        # Run test
        data_io.write(data, "test")
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

        data = object.__new__(data_io.PointData)
        data.datum_generator = dp_data
        self.header_helper(data)
        expected = "{}\n1.0,2.0,info1\n3.0,4.51,info2\n0.0,1.3,info3\n\n"\
            .format(self.expected_header)

        # Run test
        data_io.write(data, "test")
        self.assertEqual(expected, file_mock.getvalue())

    def test_event_data(self, open_mock):
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

        data = object.__new__(data_io.EventData)
        data.datum_generator = sched_data
        self.header_helper(data)
        expected = "{}\n1$$$type1$$$('track1', 'datum1')\n2$$$type2$$$" \
                   "('track2', 'datum2')\n3$$$type3$$$('track3', 'datum3')\n\n"\
            .format(self.expected_header)

        # Run test
        data_io.write(data, "test")
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
        writer = cpel_writer.CpelWriter(
            [EventDatum(specific_datum=("t1", "d1"), time=1, type="e1"),
             EventDatum(specific_datum=("t2", "d2"), time=2, type="e2")],
            track="pid"
        )
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
        writer = cpel_writer.CpelWriter(
            [EventDatum(specific_datum=("1", "d"), time=1, type="e"),
             EventDatum(specific_datum=("1", "d"), time=1, type="e")],
            track='pid'
        )
        writer.write(filename)

        # There should be 5 strings in the string table, 3 plus table name + %s
        self.assertEqual(self._get_nr_of_entries(filename, 1), 5)

        # Tracks and events look the same, so only one entry per section
        self.assertEqual(self._get_nr_of_entries(filename, 3), 1)
        self.assertEqual(self._get_nr_of_entries(filename, 4), 1)

        # Despite the same timing, there were two events so number should be two
        self.assertEqual(self._get_nr_of_entries(filename, 5), 2)
