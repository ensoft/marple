# -------------------------------------------------------------
# test_ebpf.py - tests for interactions with the bcc/eBPF module
# August 2018 - Andrei Diaconu
# -------------------------------------------------------------

""" Test bcc/ebpf interactions and stack parsing. """

import unittest
from unittest import mock
from collect.test import util_collect

from collect.interface import ebpf
from common import datatypes


class _BaseTest(util_collect.BaseTest):
    """Base test class"""


class Mallocstacks(_BaseTest):
    """
    Class that tests the mallocstacks interface

    """

    @staticmethod
    def to_kilo(num):
        """
        Helper function, transforms from bytes to kilobytes
        :param num: number of bytes
        :return: closest into to the actual number of kilobytes

        """
        return int(num / 1000)

    @staticmethod
    def mock(mock_ret):
        """
        Helper method for the testing of collect

        :param mock_ret: stdout mock value
        :returns gen: generator of StackData objects, based on what mock_ret is
        """
        with mock.patch("subprocess.Popen") as popenmock:
            popenmock().communicate.return_value = (mock_ret,
                                                    b"")
            ms_obj = ebpf.MallocStacks(100)
            gen = ms_obj.collect()

            return [stack_data for stack_data in gen]

    def test_basic_collect(self):
        """
        Basic test case where everything should work as expected

        """
        mock_return_popen_stdout = b"123123#proc1#func1#func2\n321321#proc2#" \
                                   b"func1#func2#func3\n"

        expected = [datatypes.StackData(self.to_kilo(123123),
                                        ("proc1", "func1", "func2")),
                    datatypes.StackData(self.to_kilo(321321),
                                        ("proc2", "func1", "func2", "func3"))]

        output = self.mock(mock_return_popen_stdout)
        self.assertEqual(output, expected)

    def test_strange_symbols(self):
        """
        Basic test case where everything should work as expected

        """
        mock_return_popen_stdout = b"123123#1   [];'#[]-=1   2=\n"

        expected = [datatypes.StackData(self.to_kilo(123123),
                                        ("1   [];'", "[]-=1   2="))]

        output = self.mock(mock_return_popen_stdout)
        self.assertEqual(output, expected)

    def test_nan(self):
        """
        Tests if the weight is not a number the exception is raised correctly

        """
        mock_return_popen_stdout = b"NOTANUMBER#abcd#abcd\n"
        with self.assertRaises(ValueError):
            output = self.mock(mock_return_popen_stdout)
