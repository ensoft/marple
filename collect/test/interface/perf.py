import os
import shutil
import unittest

import collect.interface.perf as perf
import collect.converter.sched_event as sched_event
import collect.test.util as util


# -----------------------------------------------------------------------------
# Globals
#

_THIS_DIR = os.path.dirname(os.path.realpath(__file__))
_DATA_DIR = os.path.join(_THIS_DIR, "data")

_SCHED_EVENTS = ["abc"]


# -----------------------------------------------------------------------------
# Helpers
#

class _BaseTest(util.BaseTest):
    """Base test class for perf testing."""
    pass


# -----------------------------------------------------------------------------
# Tests
#

class DataGenTest(_BaseTest):
    """Test class for the _data_gen() generator."""

    def setUp(self):
        """Per-test set-up"""
        super().setUp()

    def tearDown(self):
        """Per-test tear-down"""
        super().tearDown()

    def test_basic(self):
        """
        Basic test for _data_gen().
        
        Write some formatted data to a temporary file, and check that _data_gen
        correctly converts it.
        
        """
        # Expected event data
        expected = [sched_event.SchedEvent("name1", "12345", "[001]", "1232454",
                                           "event1"),
                    sched_event.SchedEvent("name2", "67890", "[003]", "67899",
                                           "event2")]

        filename = self._TEST_DIR + "data_gen_test"

        # Create a file with formatted data
        with open(filename, "w") as file_:
            for entry in expected:
                file_.write(" ".join(entry) + "\n")

        # Run _data_gen() to get a generator of items.
        actual = list(perf._data_gen(filename))

        self.assertEqual(expected, actual)

    def test_sched_data_neg(self):
        """Test when data_gen is passed an invalid file."""
        with self.assertRaises(FileNotFoundError):
            list(perf._data_gen(self._TEST_DIR + "this/file/definitely/doesnt/"
                                                 "exist"))


class StackParserTest(_BaseTest):
    """Test class for the StackParser class."""

    def test_stack_data(self):
        pass

    def test_stack_data_neg(self):
        pass

    def test_StackParser_basic(self):
        pass

    def test_StackParser_fn1(self):
        pass

    def test_stack_collapse(self):
        pass

