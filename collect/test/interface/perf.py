import os

import collect.interface.perf as perf
import collect.converter.datatypes as datatypes
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


class _StackParserTest(_BaseTest):
    """Base test class for testing the stack parser class"""
    stack_parser = perf.StackParser("")


# -----------------------------------------------------------------------------
# Tests
#

class DataGenTest(_BaseTest):
    """Test class for the _sched_data_get() generator."""

    def setUp(self):
        """Per-test set-up"""
        super().setUp()

    def tearDown(self):
        """Per-test tear-down"""
        super().tearDown()

    def test_basic(self):
        """
        Basic test for _sched_data_get().
        
        Write some formatted data to a temporary file, and check that
        _sched_data_get correctly converts it.
        
        """
        def event_to_str(sched_event):
            return "{} {} [00{}] {}: {}".format(*sched_event)

        # Expected event data
        # e.g. perf   961 [000] 707827.248468:       sched:sched_wakeup:
        expected = [datatypes.SchedEvent("name1", 12345, 1, "1232.454",
                                         "event1"),
                    datatypes.SchedEvent("name2", 67890, 3, "678.99",
                                         "event2")]

        filename = self._TEST_DIR + "data_gen_test"

        # Create a file with formatted data
        with open(filename, "w") as file_:
            # file_.writelines(event_to_str(entry) for entry in expected)
            for entry in expected:
                file_.write(event_to_str(entry)+"\n")
                print(event_to_str(entry)+"\n")

        # Run _sched_data_get() to get a generator of items.
        actual = list(perf._sched_data_gen(filename))

        self.assertEqual(expected, actual)

    def test_sched_data_neg(self):
        """Test when data_gen is passed an invalid file."""
        with self.assertRaises(FileNotFoundError):
            list(perf._sched_data_gen(self._TEST_DIR +
                                      "this/file/definitely/doesnt/exist"))


class StackParserTest(_StackParserTest):
    """Test class for the StackParser class."""

    def setUp(self):
        """Per-test set-up"""
        super().setUp()

    def tearDown(self):
        """Per-test tear-down"""
        super().tearDown()

    def test_is_empty(self):
        """Tests the function recognising an empty line."""
        self.assertTrue(self.stack_parser._line_is_empty(""))

    def test_is_baseline(self):
        """Tests the function recognising a baseline"""
        # Variations of baselines
        baselines = [""]
        for line in baselines:
            self.assertTrue(self.stack_parser._line_is_baseline(line))

    def test_is_stackline(self):
        """Tests the function recognising a stackline"""
        # Variations of stacklines
        stacklines = [""]
        for line in stacklines:
            self.assertTrue(self.stack_parser._line_is_stackline(line))

    def test_stack_collapse_basic(self):
        """Check the stack_collapse function calls the appropriate parsers"""
        # can stub out the is_... functions as they are tested separately
        pass

    def test_parse_baseline(self):
        pass

    def test_parse_stackline(self):
        pass

    def test_make_stack(self):
        pass

    def test_StackParser_complete(self):
        pass
