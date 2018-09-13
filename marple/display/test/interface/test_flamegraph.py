# -------------------------------------------------------------
# test_flamegraph.py - test module for the flamegraph interface
# August 2018 - Hrutvik Kanabar, Andrei Diaconu
# -------------------------------------------------------------

""" Tests the flamegraph interface. """

import collections
import unittest
from io import StringIO
from unittest import mock

from marple.common import data_io
from marple.display.interface import flamegraph


class _FlamegraphBaseTest(unittest.TestCase):
    """ Base class for flamegraph tests """
    coloring = 'test_color'
    weight_units = "kb"

    datum_generator = (
        data_io.StackDatum(1, ('2', '3', '4', '5'))
    )
    data = data_io.StackData(datum_generator, None, None, None, data_io.StackData.DataOptions("kb"))


    outfile = mock.MagicMock()
    outfilename = "test_output"
    outfile.__str__.return_value = outfilename
    file_mock = StringIO("")

    # Set up blank flamegraph
    fg = object.__new__(flamegraph.Flamegraph)

    fg.display_options = flamegraph.Flamegraph.DisplayOptions(coloring)
    fg.data_options = data_io.StackData.DataOptions("kb")
    fg.data = data


class InitTest(_FlamegraphBaseTest):
    """ Test the __init__ function for interface calls"""
    @mock.patch('marple.display.interface.flamegraph.config')
    def test(self, config_mock):
        config_mock.get_option_from_section.return_value = self.coloring
        fg = flamegraph.Flamegraph(self.data)

        self.assertEqual(self.data, fg.data)
        self.assertEqual(self.coloring, fg.display_options.coloring)
        self.assertEqual(self.weight_units, fg.data_options.weight_units)


class MakeTest(_FlamegraphBaseTest):
    """ Test the flamegraph creation """

    # Set up test data and expected values
    test_stack_datums = [
        data_io.StackDatum(1, ('A1', 'A2', 'A3')),
        data_io.StackDatum(2, ('B1', 'B2', 'B3', 'B4')),
        data_io.StackDatum(3, ('A1', 'A2', 'A3'))
    ]

    test_stack_data = data_io.StackData(test_stack_datums, None, None, None,
                                        data_io.StackData.DataOptions("kb"))

    expected = collections.Counter({('A1', 'A2', 'A3'): 4,
                                    ('B1', 'B2', 'B3', 'B4'): 2})

    expected_temp_file = "A1;A2;A3 4\n" \
                         "B1;B2;B3;B4 2\n"

    @mock.patch('marple.display.interface.flamegraph.file')
    @mock.patch('builtins.open')
    @mock.patch('marple.display.interface.flamegraph.subprocess')
    def test_no_options(self, subproc_mock, open_mock, temp_file_mock):
        """ Test without display options """
        temp_file_mock.TempFileName.return_value.__str__.return_value = \
            "test_temp_file"

        fg = flamegraph.Flamegraph(self.data)

        context_mock1, context_mock2 = mock.MagicMock(), mock.MagicMock()
        file_mock1, file_mock2 = StringIO(""), StringIO("")
        open_mock.side_effect = [context_mock1, context_mock2]
        context_mock1.__enter__.return_value = file_mock1
        context_mock2.__enter__.return_value = file_mock2

        actual = fg._make(self.test_stack_data)

        temp_file_mock.TempFileName.return_value.__str__.\
            assert_has_calls((mock.call(), mock.call()))
        open_mock.assert_has_calls([
            mock.call("test_temp_file", "w"),
            mock.call("test_temp_file", "w")
        ])
        self.assertEqual(file_mock1.getvalue(), self.expected_temp_file)

        subproc_mock.Popen.assert_called_once_with(
            [flamegraph.FLAMEGRAPH_DIR, "--color=hot", "--countname=kb",
             "test_temp_file"],
            stdout=file_mock2
        )
        self.assertEqual(self.expected, actual)

    @mock.patch('marple.display.interface.flamegraph.file')
    @mock.patch('builtins.open')
    @mock.patch('marple.display.interface.flamegraph.subprocess')
    def test_with_coloring(self, subproc_mock, open_mock, temp_file_mock):
        """ Test with a options """
        temp_file_mock.TempFileName.return_value.__str__.return_value = \
            "test_temp_file"

        fg = flamegraph.Flamegraph(self.data)

        context_mock1, context_mock2 = mock.MagicMock(), mock.MagicMock()
        file_mock1, file_mock2 = StringIO(""), StringIO("")
        open_mock.side_effect = [context_mock1, context_mock2]
        context_mock1.__enter__.return_value = file_mock1
        context_mock2.__enter__.return_value = file_mock2

        actual = fg._make(self.test_stack_data)

        temp_file_mock.TempFileName.return_value.__str__.\
            assert_has_calls((mock.call(), mock.call()))
        open_mock.assert_has_calls([
            mock.call("test_temp_file", "w"),
            mock.call("test_temp_file", "w")
        ])
        self.assertEqual(file_mock1.getvalue(), self.expected_temp_file)
        subproc_mock.Popen.assert_called_once_with(
            [flamegraph.FLAMEGRAPH_DIR, '--color=hot', '--countname=kb',
             'test_temp_file'], stdout=file_mock2
        )
        self.assertEqual(self.expected, actual)


class ShowTest(_FlamegraphBaseTest):
    """ Test the showing of the flamegraph """

    @mock.patch('marple.display.interface.flamegraph.file')
    @mock.patch('marple.display.interface.flamegraph.Flamegraph._make')
    @mock.patch('marple.display.interface.flamegraph.subprocess')
    @mock.patch('marple.display.interface.flamegraph.os')
    def test(self, os_mock, subproc_mock, make_mock, temp_file_mock):
        environ_mock = {'SUDO_USER': 'test_user'}
        os_mock.environ.__getitem__.side_effect = environ_mock.__getitem__

        self.fg.svg_temp_file = "test_svg_file"

        self.fg.show()

        make_mock.assert_called_once_with(self.data)

        subproc_mock.call.assert_called_once_with(
            ['su', '-', '-c', 'firefox ' + "test_svg_file", "test_user"]
        )
