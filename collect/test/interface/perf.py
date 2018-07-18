import os

from unittest.mock import patch

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
    """Base test class for testing the stack parser class."""
    def setUp(self):
        """Creates a generic empty StackParser object."""
        super().setUp()
        self.stack_parser = perf.StackParser("")

    def tearDown(self):
        """Deallocates the StackParser objec.t"""
        super().tearDown()
        self.stack_parser = None


# -----------------------------------------------------------------------------
# Tests
#

class DataGenTest(_BaseTest):
    """Test class for the _sched_data_get() generator."""

    def setUp(self):
        """Per-test set-up."""
        super().setUp()

    def tearDown(self):
        """Per-test tear-down."""
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
                file_.write(event_to_str(entry) + "\n")

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
        """Per-test set-up."""
        super().setUp()

    def tearDown(self):
        """Per-test tear-down."""
        super().tearDown()

    def test_is_empty(self):
        """Tests the function recognising an empty line."""
        self.assertTrue(self.stack_parser._line_is_empty(""))

    def test_is_empty_neg(self):
        """Tests that the line_is_empty function recognises non empty lines."""
        self.assertFalse(self.stack_parser._line_is_empty(" Not empty "))

    def test_is_baseline(self):
        """Tests the function recognising a baseline."""
        # Variations of baselines
        baselines = ["java 25607 4794564.109216: cycles:",
                     "java 12688 [002] 6544038.708352: cpu-clock:",
                     "V8 WorkerThread 25607 4794564.109216: cycles:",
                     "java 24636/25607 [000] 4794564.109216: cycles:",
                     "java 12688/12764 6544038.708352: cpu-clock:",
                     "V8 WorkerThread 24636/25607 [000] 94564.109216: cycles:"]
        for line in baselines:
            self.assertTrue(self.stack_parser._line_is_baseline(line))

    def test_is_stackline(self):
        """Tests the function recognising a stackline."""
        # Variations of stacklines
        stacklines = \
            ["	ffffffffa01bbd11 __perf_event_enable ([kernel.kallsyms])",
             "  ffffffffa01b45bb event_function ([kernel.kallsyms])     ",
             "  142cb9 [unknown] (/usr/lib/linux-tools-4.15.0-24/perf)"
             "  21b97 __libc_start_main (/lib/x86_64-linux-gnu/libc-2.27.so)"
             "2e46258d4c544155 [unknown] ([unknown])"]

        for line in stacklines:
            self.assertTrue(self.stack_parser._line_is_stackline(line))

    def test_parse_baseline_pname_only(self):
        """Tests the extraction of process names in _parse_baseline."""
        # Check that a simple process name is extracted correctly
        self.stack_parser._parse_baseline(line="java 27 464.116: cycles:")
        self.assertTrue(self.stack_parser._pname == "java")

        # Check that a space separated process name gets space replaced by _
        self.stack_parser._parse_baseline(line="V8 WorkerThread 27 464.116: "
                                               "cycles:")
        self.assertTrue(self.stack_parser._pname == "V8_WorkerThread")

        # Check that the event_filter defaulted:
        self.assertTrue(self.stack_parser.event_filter == "cycles")

    @patch("collect.interface.perf.INCLUDE_PID", True)
    def test_parse_baseline_pid(self):
        """Tests creation of pname with pid."""
        self.stack_parser._parse_baseline(line="java 27 464.116: cycles:")
        self.assertTrue(self.stack_parser._pname == "java-27")

    @patch("collect.interface.perf.INCLUDE_TID", True)
    def test_parse_baseline_tid(self):
        """Tests creation of pname with pid and tid."""
        self.stack_parser._parse_baseline(line="java 27/1 464.116: cycles:")
        self.assertTrue(self.stack_parser._pname == "java-27/1")

    def test_parse_stackline(self):
        """Tests the insertion of stacklines in the stack array"""
        self.stack_parser._pname = "some_process"
        self.stack_parser._parse_stackline(line="ffffffffabe0c31d "
                                                "intel_pmu_enable_ (["
                                                "kernel.kallsyms])")

        self.assertTrue(self.stack_parser._stack == ["intel_pmu_enable_"])

    def test_make_stack(self):
        """Tests that a stack is correctly created from lines list and pname."""
        # Example data
        pname = "some_process"
        stacklines = ["call1", "call2"]

        # Expected output
        expected = tuple([pname] + stacklines)

        # Pass example data to stack parser
        self.stack_parser._pname = pname
        self.stack_parser._stack = stacklines

        # Run the stack maker function
        stackfolded = self.stack_parser._make_stack()

        self.assertTrue(stackfolded == expected)

    def test_StackParser_complete(self):

        # Example of a single stack from perf extracted stack data
        sample_stack = \
            ["swapper     0 [003] 687886.672908:  108724462 cycles:ppp:\n" 
             "ffffffffa099768b intel_idle ([kernel.kallsyms])\n"
             "ffffffffa07e5ce4 cpuidle_enter_state ([kernel.kallsyms])\n"
             "ffffffffa07e5f97 cpuidle_enter ([kernel.kallsyms])\n"
             "ffffffffa00d299c do_idle ([kernel.kallsyms])\n"
             "ffffffffa00d2723 call_cpuidle ([kernel.kallsyms])\n"
             "ffffffffa00d2be3 cpu_startup_entry ([kernel.kallsyms])\n"
             "ffffffffa00581cb start_secondary ([kernel.kallsyms])\n"
             "ffffffffa00000d5 secondary_startup_64 ([kernel.kallsyms])\n"
             "\n"]

        # Expected output data
        expected = [datatypes.StackEvent(stack=(
            "swapper", "secondary_startup_64", "start_secondary",
            "cpu_startup_entry", "call_cpuidle", "do_idle", "cpuidle_enter",
            "cpuidle_enter_state", "intel_idle"))]

        filename = self._TEST_DIR + "stack_collapse_test"

        # Create a file with formatted data
        with open(filename, "w") as file_:
            file_.writelines(sample_stack)

        self.stack_parser.filename = filename

        # Run the whole stack_collapse function
        events = self.stack_parser.stack_collapse()
        self.assertTrue(list(events) == expected)
