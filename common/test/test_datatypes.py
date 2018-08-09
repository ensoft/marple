# -------------------------------------------------------------
# test_datatypes.py - test module for datatypes used in marple
# August 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

""" Tests the datatypes used in marple. """

import unittest

from common import datatypes
from common import exceptions

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
            datatypes.Datapoint.from_string("")

    def test_malformed_floats(self):
        """Ensure invalid string floats raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            datatypes.Datapoint.from_string("test,0.0,info")
        with self.assertRaises(exceptions.DatatypeException):
            datatypes.Datapoint.from_string("0.0,test,info")

    def test_too_few_fields(self):
        """Ensure strings with too few fields raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            datatypes.Datapoint.from_string("0.0,0.0")

    def test_empty_info_field(self):
        """Ensure empty info field"""
        result = datatypes.Datapoint.from_string("0.0,0.0,")
        self.assertEqual(result.info, "",
                         msg="Expected info field '', was actually {}"
                         .format(result.info))

    def test_with_newline_n(self):
        """Ensure from_string copes with newlines"""
        expected = datatypes.Datapoint(0.0, 0.0, 'info')
        self.check_from_str('0.0,0.0,info\n', expected)

    def test_with_newline_r(self):
        """Ensure from_string copes with newlines"""
        expected = datatypes.Datapoint(0.0, 0.0, 'info')
        self.check_from_str('0.0,0.0,info\r', expected)

    def test_with_newline_rn(self):
        """Ensure from_string copes with newlines"""
        expected = datatypes.Datapoint(0.0, 0.0, 'info')
        self.check_from_str('0.0,0.0,info\r\n', expected)

    def test_without_newline(self):
        """Ensure from_string works without newlines"""
        expected = datatypes.Datapoint(0.0, 0.0, 'info')
        self.check_from_str('0.0,0.0,info', expected)

    def test_to_string(self):
        """Test datapoints are correctly converted to strings."""
        dp = datatypes.Datapoint(0.0, 0.0, 'info')
        expected = '0.0,0.0,info'
        actual = str(dp)
        self.assertEqual(expected, actual, msg='Expected {}, got {}'
                         .format(expected, actual))


class StackDataTest(_DatatypeBaseTest):
    """Test stack data are correctly converted to/from strings."""

    def test_empty_string(self):
        """Ensure empty strings raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            datatypes.Datapoint.from_string("")

    def test_malformed_floats(self):
        """Ensure invalid string floats raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            datatypes.Datapoint.from_string("test,A;B")

    def test_too_few_fields(self):
        """Ensure strings with too few fields raise a DatatypeException"""
        with self.assertRaises(exceptions.DatatypeException):
            datatypes.Datapoint.from_string("test")

    def test_empty_stack_field(self):
        """Ensure empty stack field"""
        result = datatypes.StackData.from_string("0,")
        self.assertEqual(result.stack, ('',),
                         msg="Expected stack field empty, was actually {}"
                         .format(result.stack))

    def test_with_newline_n(self):
        """Ensure from_string copes with newlines"""
        expected = datatypes.StackData(0, ('A', 'B'))
        self.check_from_str('0,A;B\n', expected)

    def test_with_newline_r(self):
        """Ensure from_string copes with newlines"""
        expected = datatypes.StackData(0, ('A', 'B'))
        self.check_from_str('0,A;B\r', expected)

    def test_with_newline_rn(self):
        """Ensure from_string copes with newlines"""
        expected = datatypes.StackData(0, ('A', 'B'))
        self.check_from_str('0,A;B\r\n', expected)

    def test_without_newline(self):
        """Ensure from_string works without newlines"""
        expected = datatypes.StackData(0, ('A', 'B'))
        self.check_from_str('0,A;B', expected)

    def test_to_string(self):
        """Test datapoints are correctly converted to strings."""
        sd = datatypes.StackData(0, ('A', 'B'))
        expected = '0,A;B'
        actual = str(sd)
        self.assertEqual(expected, actual, msg='Expected {}, got {}'
                         .format(expected, actual))