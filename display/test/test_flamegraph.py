# -------------------------------------------------------------
# test_flamegraph.py - test module for the flamegraph interface
# August 2018 - Hrutvik Kanabar
# -------------------------------------------------------------

""" Tests the flamegraph interface. """

import unittest
from unittest import mock
from io import StringIO
import collections
import json

from display import flamegraph
from common import datatypes


class _FlamegraphBaseTest(unittest.TestCase):
    """ Base class for flamegraph tests """
    coloring = 'test_color'
    infilename = 'test_input'
    outfile = mock.MagicMock()
    outfilename = "test_output"
    outfile.__str__.return_value = outfilename
    file_mock = StringIO("")

    # Set up blank flamegraph
    fg = object.__new__(flamegraph.Flamegraph)
    fg.coloring = coloring
    fg.in_filename = infilename
    fg.out_filename = outfilename


class MockedReader:
    """
    Class used to mock the context manager Reader
    """
    def __init__(self, file):
        pass

    def __enter__(self):
        js = "{\"start\": \"2018-08-20 18:46:38.403129\", \"end\": " \
             "\"2018-08-20 18:46:39.403129\", \"datatype\": \"Event" \
             " Data\", \"interface\": \"Memory/Time\"}"
        return json.loads(js), ""

    def __exit__(self, *args):
        pass


class InitTest(_FlamegraphBaseTest):
    """ Test the __init__ function for interface calls"""
    def test(self):
        fg = flamegraph.Flamegraph(self.infilename, self.outfile,
                                   self.coloring)
        self.assertEqual(self.infilename, fg.in_filename)
        self.outfile.set_options.assert_called_once_with("flamegraph", "svg")
        # self.outfile.__str__.assert_called_once_with() # gives a Pylint error
        self.assertEqual(self.outfilename, fg.out_filename)
        self.assertEqual(self.coloring, fg.coloring)


class ReadTest(_FlamegraphBaseTest):
    """ Test the _read function """
    @mock.patch("collect.IO.read.Reader")
    def test_empty_file(self, reader_mock):
        """ Ensure the module copes with an empty graph """
        # Set up mock
        reader_mock.return_value.__enter__.return_value = ("", StringIO(""))

        result = list(self.fg._read())
        reader_mock.assert_called_once_with(self.fg.in_filename)
        self.assertEqual([], result)

    @mock.patch("collect.IO.read.Reader")
    def test_normal_file(self, reader_mock):
        """ Test opening of a normal file """
        reader_mock.return_value.__enter__.return_value = ("",
                                                           StringIO("1#"
                                                                    "A1;A2;A3\n"
                                                                    "2#B1;B2;"
                                                                    "B3;B4\n"))

        result = list(self.fg._read())
        reader_mock.assert_called_once_with(self.fg.in_filename)
        expected = [datatypes.StackDatum(1, ('A1', 'A2', 'A3')),
                    datatypes.StackDatum(2, ('B1', 'B2', 'B3', 'B4'))]
        self.assertEqual(expected, result)


class MakeTest(_FlamegraphBaseTest):
    """ Test the flamegraph creation """

    # Set up test data and expected values
    test_stack_data = [
        datatypes.StackDatum(1, ('A1', 'A2', 'A3')),
        datatypes.StackDatum(2, ('B1', 'B2', 'B3', 'B4')),
        datatypes.StackDatum(3, ('A1', 'A2', 'A3'))
    ]

    expected = collections.Counter({('A1', 'A2', 'A3'): 4,
                                    ('B1', 'B2', 'B3', 'B4'): 2})

    expected_temp_file = "A1;A2;A3 4\n" \
                         "B1;B2;B3;B4 2\n"

    @mock.patch('display.flamegraph.file')
    @mock.patch('builtins.open')
    @mock.patch('display.flamegraph.subprocess')
    def test_no_coloring(self, subproc_mock, open_mock, temp_file_mock):
        """ Test without a colouring option """
        temp_file_mock.TempFileName.return_value.__str__.return_value = \
            "test_temp_file"
        context_mock1, context_mock2 = mock.MagicMock(), mock.MagicMock()
        file_mock1, file_mock2 = StringIO(""), StringIO("")
        open_mock.side_effect = [context_mock1, context_mock2]
        context_mock1.__enter__.return_value = file_mock1
        context_mock2.__enter__.return_value = file_mock2

        self.fg.coloring = None
        actual = self.fg._make(self.test_stack_data)

        temp_file_mock.TempFileName.return_value.__str__.\
            assert_called_once_with()
        open_mock.assert_has_calls([
            mock.call("test_temp_file", "w"),
            mock.call(self.outfilename, "w")
        ])
        self.assertEqual(file_mock1.getvalue(), self.expected_temp_file)
        subproc_mock.Popen.assert_called_once_with(
            [flamegraph.FLAMEGRAPH_DIR, "test_temp_file"], stdout=file_mock2
        )
        self.assertEqual(self.expected, actual)

    @mock.patch('display.flamegraph.file')
    @mock.patch('builtins.open')
    @mock.patch('display.flamegraph.subprocess')
    def test_with_coloring(self, subproc_mock, open_mock, temp_file_mock):
        """ Test with a colouring option """
        temp_file_mock.TempFileName.return_value.__str__.return_value = \
            "test_temp_file"
        context_mock1, context_mock2 = mock.MagicMock(), mock.MagicMock()
        file_mock1, file_mock2 = StringIO(""), StringIO("")
        open_mock.side_effect = [context_mock1, context_mock2]
        context_mock1.__enter__.return_value = file_mock1
        context_mock2.__enter__.return_value = file_mock2

        self.fg.coloring = 'test_colouring'
        actual = self.fg._make(self.test_stack_data)

        temp_file_mock.TempFileName.return_value.__str__.\
            assert_called_once_with()
        open_mock.assert_has_calls([
            mock.call("test_temp_file", "w"),
            mock.call(self.outfilename, "w")
        ])
        self.assertEqual(file_mock1.getvalue(), self.expected_temp_file)
        subproc_mock.Popen.assert_called_once_with(
            [flamegraph.FLAMEGRAPH_DIR, '--color=test_colouring',
             "test_temp_file"], stdout=file_mock2
        )
        self.assertEqual(self.expected, actual)


class ShowTest(_FlamegraphBaseTest):
    """ Test the showing of the flamegraph """

    @mock.patch('display.flamegraph.Flamegraph._read')
    @mock.patch('display.flamegraph.Flamegraph._make')
    @mock.patch('display.flamegraph.subprocess')
    @mock.patch('display.flamegraph.os')
    def test(self, os_mock, subproc_mock, make_mock, read_mock):
        environ_mock = {'SUDO_USER': 'test_user'}
        os_mock.environ.__getitem__.side_effect = environ_mock.__getitem__

        self.fg.show()
        stack_gen_mock = read_mock.return_value
        read_mock.assert_called_once_with()
        make_mock.assert_called_once_with(stack_gen_mock)

        subproc_mock.call.assert_called_once_with(
            ['su', '-', '-c', 'firefox ' + self.fg.out_filename, "test_user"]
        )
